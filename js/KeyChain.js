const CommonList = require("./CommonList");
const Dweb = require("./Dweb");
// ######### Parallel development to MutableBlock.py ########

class KeyChain extends CommonList {
    // This class is pulled form MutableBlock.py
    // Notable changes:


    constructor(hash, data, master, keypair, keygen, mnemonic, verbose) { //Note not all these parameters are supported (yet) by CommonList.constructor
        super(hash, data, master, keypair, keygen, mnemonic, verbose);
        this.table = "kc";
    }
    static async_new(mnemonic, keygen, name, verbose, success, error) {
        let kc = new KeyChain(null, { "name": name }, false, null, keygen, mnemonic, verbose);
        kc.async_store(verbose, null, error);
        // Dont need to wait on store to load and fetchlist
        KeyChain.addkeychains(kc);
        kc.async_loadandfetchlist(verbose, success, error);  //Was fetching blocks, but now done by "keys"
        //if verbose: print "Created keychain for:", kc.keypair.private.mnemonic
        //if verbose and not mnemonic: print "Record these words if you want to access again"
        return kc
    }
    keytype() { return Dweb.KEYPAIRKEYTYPESIGNANDENCRYPT; }  // Inform keygen

    keys() { console.log("XXX Undefined property KeyChain.keys"); }
    add() { console.log("XXX Undefined function KeyChain.add"); }

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
    decrypt() { console.log("XXX Undefined function KeyChain.decrypt"); }
    accesskey() { console.log("XXX Undefined property KeyChain.accesskey"); }

    static addkeychains(keychains) {
        //Add keys I can view under to ACL
        //param keychains:   Array of keychains
        if (typeof keychains === "object") {    // Should be array not dict
            Dweb.keychains = Dweb.keychains + keychains;
        } else {
            Dweb.keychains.push(keychains);
        }
    }

    find() { console.log("XXX Undefined function KeyChain.find"); }

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

    _findbyclass() { console.log("XXX Undefined function KeyChain._findbyclass"); }
    myviewerkeys() { console.log("XXX Undefined function KeyChain.myviewerkeys"); }
    mymutableBlocks() { console.log("XXX Undefined function KeyChain.mymutableBlocks"); }

}

exports = module.exports = KeyChain;
