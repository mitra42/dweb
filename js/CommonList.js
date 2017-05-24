const SmartDict = require("./SmartDict");
const KeyPair = require("./KeyPair");
const Signature = require("./Signature");
const StructuredBlock = require("./StructuredBlock");
const Dweb = require("./Dweb");
// ######### Parallel development to MutableBlock.py ########

class CommonList extends SmartDict {
    constructor(hash, data, master, keypair, keygen, mnemonic, verbose, options) {
        // data = json string, or dict
        //TODO implmenent mnemonic, keypair, keygen
        //console.log("CL(", data, master, options,")");
        super(hash, data, verbose, options);
        this._list = [];   // Array of signatures
        if (keygen || mnemonic) {
            this.keypair = KeyPair.keygen(this.keytype(), mnemonic, null, verbose);
        } else {
            this._setkeypair(keypair, verbose);
        }
        this._master = master;  // Note this must be AFTER _setkeypair since that sets based on keypair found and _async_storepublic for example wants to force !master
        if (!this._master) { this._publichash = hash; }
    }
    keytype() { return Dweb.KEYPAIRKEYTYPESIGN; }

    __setattr__(name, value) {
        // Call chain is ...  or constructor > _setdata > _setproperties > __setattr__
        // catch equivalent of getters and setters here
        let verbose = false;
        if (name === "keypair") {
            this._setkeypair(value, verbose);
        } else {
            super.__setattr__(name, value);
        }
    }

    _setkeypair(value, verbose) {
        // Call chain is ...  or constructor > _setdata > _setproperties > __setattr__ > _setkeypair
        if (value && ! (value instanceof KeyPair)) {
            value = new KeyPair(null, {"key":value}, verbose);  // Synchronous value will be decoded, not fetched
        }
        this.keypair = value;
        this._master = value && value.has_private();
    }

    preflight(dd) {
        if (dd.keypair) {
            if (dd._master && !dd._acl && !this._allowunsafestore) {
                Dweb.utils.SecurityWarning("Probably shouldnt be storing private key", dd);
            }
            dd.keypair = dd._master ? dd.keypair.privateexport() : dd.keypair.publicexport();
        }
        let publichash = dd._publichash; // Save before preflight
        dd = super.preflight(dd);  // Edits dd in place
        if (dd._master) { // Only store on Master, on !Master will be None and override storing hash as _publichash
            dd._publichash = publichash;   // May be None, have to do this AFTER the super call as super filters out "_*"  #TODO-REFACTOR_PUBLICHASH
        }
        return dd;
    }

    fetch() {
        console.assert(false, "XXX Undefined function CommonList.fetch replace carefully with load");
    }

    async_load(verbose, success, error) {   // Python can also fetch based on just having key
        if (this._needsfetch) { // Only load if need to
            if (verbose) { console.log("CommonList.load:",this._hash)}
            this._needsfetch = false;
            // Need to fetch body and only then fetchlist since for a list the body might include the publickey whose hash is needed for the list
            let self = this;
            Dweb.transport.async_rawfetch(this, this._hash, verbose,
                function(data) {
                    if (data) {self._setdata(JSON.parse(data))}
                    if (success) { success(undefined);}
                },
                error);
        } else {
            if (success) {success(undefined);} // Pass to success as if loaded, and see what action reqd
        }
    }

    async_fetchlist(verbose, success, error) {
        // Load a list, note it does not load the individual items, just the Signatures. To do that, provide a "success" to loop over htem afterwards.
        // Call chain is mb.load > CL.fetchlist > THttp.rawlist > Thttp.load > CL|MB.fetchlist.success > callers.success
        let self = this;
        Dweb.transport.async_rawlist(this, this._hash, verbose,
            function(lines) {
                //console.log("async_fetchlist:",lines[0]); // Should be a full line, not just "[" which suggests unparsed.
                //lines = JSON.parse(lines))   Should already by a list
                console.log("CommonList:async_fetchlist.success", self._hash, "len=", lines.length);
                self._list = [];
                for (let i in lines) {
                    //TODO verify signature
                    //if CryptoLib.verify(s):
                    //noinspection JSUnfilteredForInLoop
                    let s = new Signature(null, lines[i], verbose);        // Signature ::= {date, hash, privatekey etc }
                    self._list.push(s);
                }
                if (success) {success(undefined);}
            },
            error);
    }
    async_loadandfetchlist(verbose, success, error) {
        // Utility function to simplify nested functions
        let self=this;
        this.async_load(verbose,
            function(msg) { self.async_fetchlist(verbose, success, error) },
            error);
    }
    blocks(verbose) {
        let results = {};   // Dictionary of { SHA... : StructuredBlock(hash=SHA... _signatures:[Signature*] ] ) }
        for (let i in this._list) {
            let s = this._list[i];
            if (! results[s.hash]) {
                results[s.hash] = new StructuredBlock(s.hash, null, verbose);  //TODO Handle cases where its not a SB
            }
            results[s.hash]._signatures.push(s);
        }
        let sbs = [];      // [ StructuredBlock* ]
        for (let k in results) {
            sbs.push(results[k]);      // Array of StructuredBlock
        }
        //TODO sort list
        sbs.sort(StructuredBlock.compare); // Could inline: sbs.sort(function(a, b) { ... }
        return sbs;
    }
    _async_storepublic() { //verbose,success, error
        console.assert(false, "Intentionally XXX Undefined function CommonList._async_storepublic - should implement in subclasses");
    }
    async_store(verbose, success, error) {  // Based on python
        //if (verbose) { console.log("CL.store", this); }
        if (this._master && ! this._publichash) {
            this._async_storepublic(verbose, success, error); //Stores asynchronously, but hash set immediately
        }
        if ( ! (this._master && this.dontstoremaster)) {
            super.async_store(verbose, success, error);    // Transportable.store(verbose)
        } else {
            if (success) { success(null); }
        }
        return this;
    }

    publicurl() { console.assert(false, "XXX Undefined function CommonList.publicurl"); }   // For access via web
    privateurl() { console.assert(false, "XXX Undefined function CommonList.privateurl"); }   // For access via web

    async_signandstore(obj, verbose, success, error) {
        /*
         Sign and store a StructuredBlock on a list - via the SB's signatures - see add for doing independent of SB

         :param StructuredBlock obj:
         :param verbose:
         :param options:
         :return:
         */
        let self = this;
        this.async_load(verbose,
            function(msg) {
                console.assert(self._master, "ForbiddenException: Signing a new entry when not a master list");
                // The obj.store stores signatures as well (e.g. see StructuredBlock.store)
                obj.sign(self, verbose).async_store(verbose, success, error);
            },
            error);
        return this; // For chaining
    }
    async_add(obj, verbose, success, error) {
        /*
         Add a object, typically MBM or ACL (i.e. not a StructuredBlock) to a List,
         COPIED TO JS 2017-05-24

         :param obj: Object to store on this list or a hash string.
         :param success: funciton(msg) to run on success
         :param error: funciton(msg) to run on success
         :returns Signature: Returns the Signature immediately for adding to local copy
         */
        let hash = (typeof obj === "string") ? obj : obj._hash;
        console.assert(hash, "Empty string or undefined or null would be an error");
        let sig = Signature.sign(this, hash, verbose);
        Dweb.transport.async_add(hash, sig.date, sig.signature, sig.signedby, verbose, success, error);
        return sig;  // Return sig immediately, typically for adding to local copy of list
        // Caller will probably want to add obj to list , not done here since MB handles differently from KC etc
    }
}
exports = module.exports = CommonList;
