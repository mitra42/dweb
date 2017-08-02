const CommonList = require("./CommonList");  // Superclass
const Dweb = require("./Dweb");

// Utility packages (ours) Aand one-loners


// ######### Parallel development to MutableBlock.py ########

// Note naming convention - p_xyz means it returns a Promise

class KeyChain extends CommonList {
    // This class is pulled form MutableBlock.py


    constructor(hash, data, master, keypair, keygen, mnemonic, verbose) { //Note not all these parameters are supported (yet) by CommonList.constructor
        super(hash, data, master, keypair, keygen, mnemonic, verbose);
        if (!this._keys) this._keys = []; // Could be overridden by data in super
        this.table = "kc";
    }
    static p_new(mnemonic, keygen, name, verbose) {
        let kc = new KeyChain(null, { "name": name }, true, null, keygen, mnemonic, verbose);
        return kc.p_store(verbose) // Dont need to wait on store to load and fetchlist but will do so to avoid clashes
            .then(() => KeyChain.addkeychains(kc))
            .then(() => kc.p_fetch_then_list(verbose))  //fetchlist gets the elements
            .then(() => kc) //Fetches blocks in p_loadandfetchlist.success
            // Note kc returned from promise NOT from p_new so have to catch in a ".then"
        //if verbose: print "Created keychain for:", kc.keypair.private.mnemonic
        //if verbose and not mnemonic: print "Record these words if you want to access again"
    }

    keytype() { return Dweb.KeyPair.KEYTYPESIGNANDENCRYPT; }  // Inform keygen

    p_fetchlist(verbose) {
        // Call chain is kc.p_new > kc.loadandfetchlist > KC.p_fetchlist > THttp.p_rawlist > Thttp.list > KC.p_fetchlist.success > caller's success
        let self = this;
        return super.p_fetchlist(verbose)
            // Called after CL.p_fetchlist has unpacked data into Signatures in _list
            //.then(() => self._keys = Dweb.Signature.filterduplicates(self._list).map((sig) => new Dweb.UnknownBlock(sig.hash, verbose)))
            .then(() => Promise.all(Dweb.Signature.filterduplicates(self._list)
                .map((sig) => new Dweb.UnknownBlock(sig.hash, verbose))
                .map((ub) => ub.p_fetch(verbose)))) // Return is result of p_fetch which is new obj
            .then((keys) => self._keys = keys)
            .then(() => { if (verbose) console.log("KC.p_fetchlist Got keys", ...Dweb.utils.consolearr(self._keys))})
    }

    keys() {    // Is property in Python
        // Keys are fetched during p_fetchlist
        return this._keys;
    }


    p_addobj(obj, verbose) {
        /*
         Add a obj (usually a MutableBlock or a ViewerKey) to the keychain. by signing with this key.
         Item should usually itself be encrypted (by setting its _acl field)
         COPIED FROM PYTHON 2017-05-24

         :param obj: JSON structure to add to KeyChain 0 should be a Signature
         */
        let hash = (typeof obj === "string") ? obj : obj._hash;
        let sig = this._makesig(hash, verbose);
        this._list.push(sig);
        return super.p_add(hash, sig, verbose)    // Resolves to sig
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
         :return: decrypted text as string
         */
        let key = this.keypair._key;
        if (key.encrypt) { // NACL key
            return this.keypair.decrypt(data, this, "text"); //data, b64, signer
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

    _p_storepublic(verbose) {
        // Note - doesnt return a promise, the store is happening in the background
        if (verbose) console.log("KeyChain._p_storepublic");
        let kc = new KeyChain(null, {"name": this.name}, false, this.keypair, false, null, verbose);
        kc.p_store(verbose); // Async, but will set _hash immediately
        this._publichash = kc._hash;  //returns immediately with precalculated hash
    }

    p_store(verbose) {
        // CommonList.store(verbose, success, error)
        this.dontstoremaster = true;
        return super.p_store(verbose)  // Stores public version and sets _publichash - never returns
    }

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
        return KeyChain._findbyclass(Dweb.KeyPair);
    }

    static mymutableBlocks() {
        /*
         :return: Array of Viewer Keys on the KeyChains
         */
        return KeyChain._findbyclass(Dweb.MutableBlock);
    }

    static p_test(acl, verbose) {
        if (verbose) console.log("KeyChain.test");
        return new Promise((resolve, reject) => {
            try {
                // Set mnemonic to value that generates seed "01234567890123456789012345678901"
                const mnemonic = "coral maze mimic half fat breeze thought champion couple muscle snack heavy gloom orchard tooth alert cram often ask hockey inform broken school cotton"; // 32 byte
                // Test sequence extracted from test.py
                const qbf="The quick brown fox ran over the lazy duck";
                const vkpname="test_keychain viewerkeypair";
                let kc, kcs2, mb, mblockm, mbmaster, mbm2, mbm3, mm, sb, sb2, viewerkeypair;
                const keypairexport =  "NACL SEED:w71YvVCR7Kk_lrgU2J1aGL4JMMAHnoUtyeHbqkIi2Bk="; // So same result each time
                if (verbose) {
                    console.log("Keychain.test 0 - create");
                }
                KeyChain.p_new(mnemonic, false, "test_keychain kc", verbose)
                    .then((kc1) => {
                        kc = kc1;
                        if (verbose) console.log("KEYCHAIN 1 - add MB to KC");
                    })
                    .then(() => Dweb.MutableBlock.p_new(kc, null, "test_keychain mblockm", true, qbf, true, verbose)) //acl, contentacl, name, _allowunsafestore, content, signandstore, verbose, options
                    .then((mbm) => {mbmaster=mbm;  kc.p_addobj(mbmaster, verbose)})   //Sign and store on KC's list (returns immediately with Sig)
                    .then(() => {
                        if (verbose) console.log("KEYCHAIN 2 - add viewerkeypair to it");
                        viewerkeypair = new Dweb.KeyPair(null, {"name": vkpname, "key": keypairexport}, verbose);
                        viewerkeypair._acl = kc;
                        viewerkeypair.p_store(verbose); // Defaults to store private=True (which we want)   // Sets hash, dont need to wait for it to store
                    })
                    .then(() =>  kc.p_addobj(viewerkeypair, verbose))
                    .then(() => {
                        if (verbose) console.log("KEYCHAIN 3: Fetching mbm hash=", mbmaster._hash);
                        //MB(hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose, options)
                        mbm2 = new Dweb.MutableBlock(mbmaster._hash, null, true, null, false, null, null, null, verbose, null);
                    })
                    .then(() =>  mbm2.p_fetch(verbose))
                    .then(() => console.assert(mbm2.name === mbmaster.name, "Names should survive round trip",mbm2.name,"!==",mbmaster.name))
                    .then(() => {
                        if (verbose) console.log("KEYCHAIN 4: reconstructing KeyChain and fetch");
                        Dweb.keychains = []; // Clear Key Chains
                    })
                    //p_new(mnemonic, keygen, name, verbose)
                    .then(() => kcs2 = KeyChain.p_new(mnemonic, null, "test_keychain kc", verbose))
                    // Note success is run AFTER all keys have been loaded
                    .then(() => {
                        mm = KeyChain.mymutableBlocks();
                        console.assert(mm.length, "Should find mblockm");
                        mbm3 = mm[mm.length - 1];
                        console.assert(mbm3 instanceof Dweb.MutableBlock, "Should be a mutable block", mbm3);
                        console.assert(mbm3.name === mbmaster.name, "Names should survive round trip");
                     })
                    .then(() => {
                        if (verbose) console.log("KEYCHAIN 5: Check can user ViewerKeyPair");
                        // Uses acl passed in from AccessControlList.acl
                        acl._allowunsafestore = true;
                    })
                    .then(() => verbose = true)
                    .then(() => acl.p_add(viewerkeypair._hash, verbose))   //Add us as viewer
                    .then(() => {
                        console.assert("acl._list.length === 1", "Should have added exactly 1 viewerkeypair",acl);
                        sb = new Dweb.StructuredBlock(null, {"name": "test_sb", "data": qbf, "_acl": acl}, verbose); //hash,data,verbose
                    })
                    .then(() => sb.p_store(verbose))
                    .then(() => {
                        let mvk = KeyChain.myviewerkeys();
                        console.assert(mvk[0].name === vkpname, "Should find viewerkeypair stored above");
                        if (verbose) console.log("KEYCHAIN 6: Check can fetch and decrypt - should use viewerkeypair stored above");
                        sb2 = new Dweb.StructuredBlock(sb._hash, null, verbose);
                    })
                    .then (() => sb2.p_fetch(verbose))   //Fetch & decrypt
                    .then(() => {
                        console.assert(sb2.data === qbf, "Data should survive round trip");
                        if (verbose) console.log("KEYCHAIN 7: Check can store content via an MB");
                        //MB.new(acl, contentacl, name, _allowunsafestore, content, signandstore, verbose)
                    })
                    .then(() => Dweb.MutableBlock.p_new(null, acl, "mblockm", true, qbf, true, verbose))
                    .then((newmblockm) => {
                        mblockm = newmblockm;
                        //hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose, options
                        mb = new Dweb.MutableBlock(mblockm._publichash, null, false, null, null, null, null, null, verbose);
                    })
                    .then(() => mb.p_fetch_then_list_then_current(verbose))
                    .then(() => {
                        console.assert(mb.content() === qbf, "Data should round trip through ACL");
                    })

                    .then(() => {
                        if (verbose) console.log("KeyChain.test promises complete");
                        //console.log("KeyChain.test requires more tests defined");
                        resolve({kc: kc, mbmaster: mbmaster});
                    })
                    .catch((err) => {
                        console.log("Error in KeyChain.p_test", err);   // Log since maybe "unhandled" if just throw
                        reject(err);
                    })
            } catch (err) {
                console.log("Caught exception in KeyChain.p_test", err);
                throw err;
            }
        })
    }
}



exports = module.exports = KeyChain;
