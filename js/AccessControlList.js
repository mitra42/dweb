const CommonList = require("./CommonList");
const Dweb = require("./Dweb");
const sodium = require("libsodium-wrappers");
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
        if ((!this._master) && this.keypair._key.sign.publicKey) { //TODO not sure if this is correct, as _key might be array
            dd["naclpublic"] = dd.naclpublic || dd.keypair.publicexport();   // Store naclpublic for verification
        }
        // Super has to come after above as overrights keypair, also cant put in CommonList as MB's dont have a naclpublic and are only used for signing, not encryption
        return super.preflight(dd);
    }

    p_add(viewerpublichash, verbose) {
        /*
        Add a new ACL entry
        Needs publickey of viewer

        :param self:
        :return: promise resolving to this for chaining
        */
        let self = this;
        if (verbose) console.log("AccessControlList.add viewerpublichash=",viewerpublichash);
        if (!this._master) {
            throw new Dweb.errors.ForbiddenError("Cant add viewers to ACL copy");
        }
        let viewerpublickeypair = new Dweb.KeyPair(viewerpublichash, null, verbose);
        return viewerpublickeypair.p_fetch(verbose)
            .then(() => {
                let aclinfo = {
                    //Need to go B64->binary->encrypt->B64
                    "token": viewerpublickeypair.encrypt(Dweb.CryptoLib.b64dec(self.accesskey), true, self),
                    "viewer": viewerpublichash
                };
                let sb = new Dweb.StructuredBlock(null, aclinfo, verbose); //hash,data,verbose
                return (sb);
            })
            .then((sb) => self.p_signandstore(sb, verbose))
            .then(() => self);
    }

    tokens() { console.assert(false, "XXX Undefined function AccessControlList.tokens"); };
    encrypt(data, b64) { return Dweb.CryptoLib.sym_encrypt(data, this.accesskey, b64); };
    decrypt(data, viewerkeypair, verbose) {
        console.assert(false, "XXX Undefined function AccessControlList.decrypt");
    };

    /* BELOW COMES FROM ITEMS PUT HERE PRIOR TO IMPLEMENTATION ABOVE WHICH COMES FROM ACL.py */

    _p_storepublic(verbose) {
        // Note - doesnt return a promise, the store is happening in the background
        if (verbose) console.log("AccessControlList._p_storepublic");
        //AC(hash, data, master, keypair, keygen, mnemonic, verbose, options) {
        let acl = new AccessControlList(null, {"name": this.name}, false, this.keypair, false, null, verbose, {});
        acl.p_store(verbose); // Async, but will set _hash immediately
        this._publichash = acl._hash;  //returns immediately with precalculated hash
    }

    static p_test(verbose) { // Create and return a acl suitable for other tests, in process test ACL
        if (verbose) console.log("AccessControlList.p_test");
        return new Promise((resolve, reject) => {
            try {
                if (verbose) console.log("Creating AccessControlList");
                // Create a acl for testing, - full breakout is in test_keychain
                let accesskey = Dweb.CryptoLib.randomkey();
                let aclseed = "01234567890123456789012345678902"    // Note 01 at end used in mnemonic faking
                let keypair = Dweb.KeyPair.keygen(Dweb.KeyPair.KEYTYPESIGNANDENCRYPT, null, aclseed, verbose);
                //ACL(hash, data, master, keypair, keygen, mnemonic, verbose, options)
                let acl = new Dweb.AccessControlList(null, {
                    name: "test_acl.acl",
                    accesskey: Dweb.CryptoLib.b64enc(accesskey)
                }, true, keypair, false, null, verbose, {});
                acl._allowunsafestore = true;    // Not setting _acl on this
                acl.p_store(verbose)
                .then(() => {
                    acl._allowunsafestore = false;
                    if (verbose) console.log("Creating AccessControlList hash=", acl._hash);
                    resolve(acl);
                })
                .catch((err) => {
                    console.log("Error in AccessControlList.p_test", err);   // Log since maybe "unhandled" if just throw
                    reject(err);
                });
            } catch(err) {
                console.log("Caught exception in AccessControlList.p_test", err);
                throw err;
            }
        })
    }

}
exports = module.exports = AccessControlList;


