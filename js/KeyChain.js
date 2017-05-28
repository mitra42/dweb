const CommonList = require("./CommonList");
const MutableBlock = require("./MutableBlock");
const KeyPair = require("./KeyPair");
const UnknownBlock = require("./UnknownBlock");

const Dweb = require("./Dweb");
// ######### Parallel development to MutableBlock.py ########

class KeyChain extends CommonList {
    // This class is pulled form MutableBlock.py
    // Notable changes:


    constructor(hash, data, master, keypair, keygen, mnemonic, verbose) { //Note not all these parameters are supported (yet) by CommonList.constructor
        super(hash, data, master, keypair, keygen, mnemonic, verbose);
        if (!this._keys) this._keys = []; // Could be overridden by data in super
        this.table = "kc";
    }
    static async_new(mnemonic, keygen, name, verbose, success, error) {
        let kc = new KeyChain(null, { "name": name }, true, null, keygen, mnemonic, verbose);
        kc.async_store(verbose, null, error);
        // Dont need to wait on store to load and fetchlist
        KeyChain.addkeychains(kc);
        kc.async_loadandfetchlist(verbose, success, error);  //Fetches blocks in async_fetchlist.success
        //if verbose: print "Created keychain for:", kc.keypair.private.mnemonic
        //if verbose and not mnemonic: print "Record these words if you want to access again"
        return kc
    }
    keytype() { return Dweb.KEYPAIRKEYTYPESIGNANDENCRYPT; }  // Inform keygen

    async_fetchlist(verbose, success, error) {  // Check callers of fetchlist and how pass parameters
        // Call chain is kc.async_new > kc.loadandfetchlist > KC.async_fetchlist > THttp.async_rawlist > Thttp.list > KC.fetchlist.success > caller's success
        let self = this;
        super.async_fetchlist(verbose,
            function (unused) {
                // Called after CL.async_fetchlist has unpacked data into Signatures in _list
                let results={};
                self._keysloading = self._keysloading || 0;
                for (let i in self._list) {
                    self._keysloading += 1;
                    let sig = self._list[i];
                    if (! results[sig.hash]) {
                        let key = new UnknownBlock(sig.hash, verbose);
                        results[sig.hash] = key;
                        key.async_load(verbose, ["addtokeysonload", self, success], null);   // Order isn't significant - could be MB or ACL
                    }
                }
                // Success done above when all loaded. if (success) { success(undefined); }  // Note success is applied to the KC, before the blocks have been loaded
            },
            error);
    }


    keys() {    // Is property in Python
        // Keys are fetched during async_fetchlist
        return this._keys;
    }


    async_add(obj, verbose, success, error) {
        /*
         Add a obj (usually a MutableBlock or a ViewerKey) to the keychain. by signing with this key.
         Item should usually itself be encrypted (by setting its _acl field)
         COPIED FROM PYTHON 2017-05-24

         :param obj: JSON structure to add to KeyChain 0 should be a Signature
         */
        let sig = super.async_add(obj, verbose, success, error);  // Adds to dWeb list
        this._list.push(sig);
    }

    encrypt(res, b64) {
        /*
         Encrypt an object (usually represented by the json string). Pair of .decrypt()

         :param res: The material to encrypt, usually JSON but could probably also be opaque bytes
         :param b64:
         :return:
         */
        // Should be a signing key
        return this.keypair.encrypt(res, b64, this);  // data, b64, signer
    }
    decrypt(data, verbose) {
        /*
         :param data: String from json, b64 encoded
         :param verbose:
         :return: decrypted text
         */
        let key = this.keypair._key;
        if (key.encrypt) { // NACL key
            return this.keypair.decrypt(data, true, this); //data, b64, signer
        } else {
            Dweb.utils.ToBeImplementedException("Keypair.decrypt for ", key);
        }
    }



    accesskey() { console.assert(false, "XXX Undefined property KeyChain.accesskey"); }

    static addkeychains(keychains) {
        //Add keys I can view under to ACL
        //param keychains:   Array of keychains
        if (keychains instanceof Array) {
            Dweb.keychains = Dweb.keychains.concat(keychains);
        } else {
            Dweb.keychains.push(keychains);
        }
    }

    static find(publichash, verbose) {
        /* Locate a needed key by its hash */
        for (let i in Dweb.keychains) {
            let kc = Dweb.keychains[i];
            if (kc._publichash === publichash) {
                if (verbose) console.log("KeyChain.find successful for",publichash);
                return kc;
            }
        }
        return null;
    }

    _async_storepublic(verbose, success, error) { // Based on python CL._storepublic, but done in each class in JS
        console.log("KeyChain._async_storepublic");
        let kc = new KeyChain(null, {"name": this.name}, false, this.keypair, false, null, verbose);
        this._publichash = kc.async_store(verbose, success, error)._hash;  //returns immediately with precalculated hash
    }

    async_store(verbose, success, error) {
        // CommonList.store(verbose, success, error)
        this.dontstoremaster = true;
        return super.async_store(verbose, success, error)  // Stores public version and sets _publichash - never returns
    }
    fetch() { console.log("Intentionally XXX Undefined function MutableBlock.fetch use load/success"); }   // Split into load/onload

    static _findbyclass(clstarget) {
        // Super obscure double loop, but works and fast
        let res = [];
        for (let i in Dweb.keychains) {
            let keys = Dweb.keychains[i].keys();
            for (let j in keys) {
                let k = keys[j];
                if (k instanceof clstarget) res.push(k);
            }
        }
        return res;
    }

    static myviewerkeys() {
        /*
         :return: Array of Viewer Keys on the KeyChains
         */
        return KeyChain._findbyclass(KeyPair);
    }

    static mymutableBlocks() {
        /*
         :return: Array of Viewer Keys on the KeyChains
         */
        return KeyChain._findbyclass(MutableBlock);
    }
}


exports = module.exports = KeyChain;
