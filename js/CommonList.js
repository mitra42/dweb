const SmartDict = require("./SmartDict");
const KeyPair = require("./KeyPair");
const Signature = require("./Signature");
const StructuredBlock = require("./StructuredBlock");
const Dweb = require("./Dweb");
// ######### Parallel development to MutableBlock.py ########

class CommonList extends SmartDict {
    constructor(hash, data, master, keypair, keygen, mnemonic, verbose, options) {
        // data = json string, or dict
        //TODO note KeyPair.keygen doesnt implement mnemonic yet
        //console.log("CL(", data, master, options,")");
        super(hash, data, verbose, options);
        this._list = [];   // Array of signatures
        if (keygen || mnemonic) {
            this.keypair = KeyPair.keygen(this.keytype(), mnemonic, null, verbose);
        } else {
            this._setkeypair(keypair, verbose);
        }
        this._master = master;  // Note this must be AFTER _setkeypair since that sets based on keypair found and _p_storepublic for example wants to force !master
        if (!this._master) { this._publichash = hash; }
    }

    keytype() { return Dweb.KeyPair.KEYTYPESIGN; }

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
            dd._publichash = publichash;   // May be None, have to do this AFTER the super call as super filters out "_*"
        }
        return dd;
    }

    p_fetchlist(verbose) {
        // Load a list, note it does not load the individual items, just the Signatures. To do that, append a ".then" to loop over them afterwards.
        // Call chain is mb.load > CL.p_fetchlist > THttp.rawlist > Thttp.load > CL|MB.p_fetchlist.success > callers.success
        let self = this;
        if (!this._master && !this._publichash)  this._publichash = this._hash;  // We aren't master, so publichash is same as hash
        if (!this._publichash) this._p_storepublic(verbose); // Async, but sets _publichash immediately
        return Dweb.transport.p_rawlist(this._publichash, verbose)
            .then((lines) => {
                //console.log("p_fetchlist:",lines[0]); // Should be a full line, not just "[" which suggests unparsed.
                //lines = JSON.parse(lines))   Should already by a list
                if (verbose) console.log("CommonList:p_fetchlist.success", self._hash, "len=", lines.length);
                self._list = lines.map((l) => new Signature(null, l, verbose));
            })
    }

    p_fetch_then_list(verbose) {
        // Utility function to simplify nested functions
        // Need to fetch body and only then fetchlist since for a list the body might include the publickey whose hash is needed for the list
        let self=this;
        return this.p_fetch(verbose)
            .then(()=>self.p_fetchlist(verbose))
    }

    p_fetch_then_list_then_elements(verbose) {
        // Utility function to simplify nested functions
        // Need to fetch body and only then fetchlist since for a list the body might include the publickey whose hash is needed for the list
        let self=this;
        return this.p_fetch_then_list(verbose)
            .then(() => Promise.all(Dweb.Signature.filterduplicates(self._list) // Dont load multiple copies of items on list (might need to be an option?)
                .map((sig) => new Dweb.UnknownBlock(sig.hash, verbose))
                .map((ub) => ub.p_fetch(verbose)))) // Return is array result of p_fetch which is array of new objs (suitable for storing in keys etc)
        }

    blocks(verbose) {
        console.assert(false, "XXX@CL.blocks - checking if this ever gets used as should be handled by p_fetchlist.then");
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

    _p_storepublic(verbose) { //verbose
        console.assert(false, "Intentionally undefined function CommonList._p_storepublic - should implement in subclasses");
    }

    p_store(verbose) {
        //if (verbose) { console.log("CL.store", this); }
        if (this._master && ! this._publichash) {
            this._p_storepublic(verbose); //Stores asynchronously, but _publichash set immediately
        }
        if ( ! (this._master && this.dontstoremaster)) {
            return super.p_store(verbose);    // Transportable.store(verbose)
        } else {
            return new Promise((resolve, reject)=> resolve(null));  // I think this should be a noop - fetched already
        }
    }

    publicurl() { console.assert(false, "XXX Undefined function CommonList.publicurl"); }   // For access via web
    privateurl() { console.assert(false, "XXX Undefined function CommonList.privateurl"); }   // For access via web

    p_signandstore(obj, verbose ) {
        /*
         Sign and store a StructuredBlock on a list - via the SB's signatures - see add for doing independent of SB

         :param StructuredBlock obj:
         :param verbose:
         :return: this - for chaining
         */
        let self = this;
        return this.p_fetch(verbose)
            .then(() => {
                console.assert(self._master && self.keypair, "ForbiddenException: Signing a new entry when not a master list");
                // The obj.store stores signatures as well (e.g. see StructuredBlock.store)
                let sig = obj.sign(self, verbose);
                obj.p_store(verbose);
                self._list.push(sig);
                return obj;
            })
    }

    _makesig(hash, verbose) {
        console.assert(hash, "Empty string or undefined or null would be an error");
        console.assert(this._master, "Must be master to sign something");
        let sig = Signature.sign(this, hash, verbose);
        console.assert(sig.signature, "Must be a signature");
        return sig
    }
    p_add(hash, sig, verbose) {
        console.assert(sig,"Meaningless without a sig");
        return Dweb.transport.p_rawadd(hash, sig.date, sig.signature, sig.signedby, verbose);
    }

}
exports = module.exports = CommonList;
