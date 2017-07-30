const CommonList = require("./CommonList");
const Dweb = require("./Dweb");
// ######### Parallel development to AccessControlList.py ########


class AccessControlList extends CommonList {
    /*
    An AccessControlList is a list for each control domain, with the entries being who has access.

    To create a list, it just requires a key pair, like any other List

    See Authentication.rst
    From EncryptionList: accesskey   Key with which things on this list are encrypted
    From CommonList: keypair, _publichash, _list, _master, name
    */

    // Obviously ! This class hasnt' been implemented, currently just placeholder for notes etc

    constructor(hash, data, master, keypair, keygen, mnemonic, verbose, options) {
        super(hash, data, master, keypair, keygen, mnemonic, verbose, options);
        this.table = "acl";
    }

    preflight(dd) {
        console.log("XXX@25",self.keypair._key); //Looking for instance of sodium.signing.SigningKey or similar
        if ((!this._master) && (self.keypair._key instanceof sodium.signing.SigningKey)) {
            dd["naclpublic"] = dd.naclpublic || dd.keypair.naclpublicexport();   // Store naclpublic for verification
        }
        // Super has to come after above as overrights keypair, also cant put in CommonList as MB's dont have a naclpublic and are only used for signing, not encryption
        return super.preflight(dd);
    }
    add() { console.assert(false, "XXX Undefined function AccessControlList.add"); };
    tokens() { console.assert(false, "XXX Undefined function AccessControlList.tokens"); };
    encrypt() { console.assert(false, "XXX Undefined function AccessControlList.encrypt"); };
    decrypt(data, viewerkeypair, verbose) {
        console.assert(false, "XXX Undefined function AccessControlList.decrypt");
    };

/* BELOW COMES FROM ITEMS PUT HERE PRIOR TO IMPLEMENTATION ABOVE WHICH COMES FROM ACL.py */

    _p_storepublic(verbose, success, error) { // See KeyChain for example
        console.assert(false, "XXX Undefined function AccessControlList._p_storepublic");
        //mb = new MutableBlock(keypair=this.keypair, name=this.name)
    }

    /*
    p_test(verbose) { // Create and return a acl suitable for other tests, in process test ACL
        if (verbose) console.log("AccessControlList.p_test");
        return new Promise((resolve, reject) => {
            try {
                if (verbose) console.log("Creating AccessControlList");
                // Create a acl for testing, - full breakout is in test_keychain
                let accesskey = Dweb.CryptoLib.randomkey();
                let keypair = self.keyfromfile("test_acl1" + self.keytail, private = True, keytype = KeyPair.KEYTYPESIGN)
                let acl = new AccessControlList(null, {
                    name: "test_acl.acl",
                    accesskey: CryptoLib.b64enc(accesskey)
                }, true, keypair, false, null, verbose, {});
                acl._allowunsafestore = true    // Not setting _acl on this
                acl.p_store(verbose)
                .then(() => {
                    acl._allowunsafestore = False
                    if (verbose) console.log("Creating AccessControlList hash=", acl._hash);
                    resolve(acl);
                })
                .catch((err) => {
                    console.log("Error in AccessControlList.p_test", err);   // Log since maybe "unhandled" if just throw
                    reject(err);
                })
            } catch(err) {
                console.log("Caught exception in AccessControlList.p_test", err);
                throw err;
            }
        }
    }
    */
}
exports = module.exports = AccessControlList;


