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

    tokens(viewerkeypair, decrypt, verbose) {
        /*
        Find the entries for a specific viewer
        There might be more than one if either the accesskey changed or the person was added multiple times.
        Entries are StructuredBlocks with token being the decryptable token we want

        :param viewerkeypair:  KeyPair of viewer
        :param verbose:
        :param options:
        :return:
        */

        if (verbose) console.log("AccessControlList.tokens decrypt=",decrypt);
        console.assert(!this._needsfetch, "Dont attampt without doing a p_fetch first");
        let viewerhash = viewerkeypair._hash;
        if (! this._list.length) { return []};  //TODO-TEST can remove this line when below working
        let toks = this._list
            .filter((sig) => sig.data.viewer === viewerhash)    // Find any sigs that match this viewerhash - doesnt guarrantee decrypting
            .map((sig) => sig.data.token);
        if (decrypt) {
            toks = toks.map((tok) => viewerkeypair.decrypt(tok, this, "uint8array"));
        }
        return toks;
    }

    p_fetch_then_list_then_elements(verbose) {  // Like superclass, but fetch the blocks the sigs point to.
        return super.p_fetch_then_list_then_elements(verbose)
            .then(() => Promise.all(
                this._list.map((sig) => {return sig.p_block(verbose)})))
    }

    encrypt(data, b64) { return Dweb.CryptoLib.sym_encrypt(data, this.accesskey, b64); };

    decrypt(data, viewerkeypair, verbose) {
        /*
             Chain is SD.p_fetch > CryptoLib.p_decryptdata > ACL.decrypt > SD.setdata

            :param data: string from json - b64 encrypted
            :param viewerkeypair:
            :param verbose:
            :return:
        */
        console.assert(!this._needsfetch, "Dont attampt without doing a p_fetch_fetch_then_list_then_elements first");
        let vks = viewerkeypair || Dweb.KeyChain.myviewerkeys();
        if (!Array.isArray(vks)) { vks = [ vks ]; }
        for (let i in vks) {
            let vk = vks[i];
            let toks = this.tokens(vk, true, verbose); //viewerkeypair, decrypt, verbose //TODO-TEST will need to be any or something like that
            for (let j in toks) {
                let symkey = toks[j];
                try {
                    let r = Dweb.CryptoLib.sym_decrypt(data, symkey, "text"); //data. symkey #Exception DecryptionFail
                    return r;
                } catch(err) {
                    //Should really only catch DecryptionFail
                    //do nothing,
                }
            }
        }
        throw new Dweb.errors.AuthenticationError("ACL.decrypt: No valid keys found");
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


