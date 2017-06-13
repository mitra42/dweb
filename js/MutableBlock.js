// ######### Parallel development to MutableBlock.py ########

const CommonList = require("./CommonList");
const StructuredBlock = require("./StructuredBlock");
const Dweb = require("./Dweb");

class MutableBlock extends CommonList {
    // { _hash, _key, _current: StructuredBlock, _list: [ StructuredBlock*]

    constructor(hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose, options) {
        //CL.constructor: hash, data, master, keypair, keygen, mnemonic, verbose
        //if (verbose) console.log("new MutableBlock(", hash, data, master, keypair, keygen, mnemonic, verbose, options, ")");
        super(hash, data, master, keypair, keygen, mnemonic, verbose, options);
        this.contentacl = contentacl;
        this._current = new StructuredBlock(contenthash, null, verbose);
        this.table = "mb"
    }

    p_elem(){ console.assert(false, "Need to define p_ function")}

    async_elem(el, verbose, successmethodeach, error) { console.trace(); console.assert(false, "OBSOLETE"); //TODO-IPFS obsolete with p_fetch
        if (this._needsfetch) {
            let self = this;
            this.async_load(verbose, function (msg) {
                self.async_elem(el, verbose, successmethodeach, error);
            }, null);
        } else {
            // this._current should be setup, it might not be loaded, but async_elem can load it
            this._current.async_elem(el, verbose, successmethodeach, error);    // Typically _current will be a SB
        }
    }

    p_fetchlist(verbose) {  // Check callers of fetchlist and how pass parameters
        // Call chain is mb.load > MB.fetchlist > THttp.rawlist > Thttp.list > MB.fetchlist.success > caller's success
        let self = this;
        return super.p_fetchlist(verbose)   // Return is a promise
        .then(() => { // Called after CL.p_fetchlist has unpacked data into Signatures in _list
                if (self._list.length) {
                    let sig = self._list[self._list.length - 1];  // Get most recent
                    self._current = new StructuredBlock(sig.hash, null, verbose);   // Store in _current
                }
        // Note any follow on .then is applied to the MB, not to the content, and the content might not have been loaded.
        })
    }

    async_fetchlist(verbose, success, error) {  // Check callers of fetchlist and how pass parameters //TODO-IPFS obsolete this
        // Call chain is mb.load > MB.fetchlist > THttp.rawlist > Thttp.list > MB.fetchlist.success > caller's success
        let self = this;
        super.async_fetchlist(verbose,
            function (unused) {
                // Called after CL.async_fetchlist has unpacked data into Signatures in _list
                if (self._list.length) {
                    let sig = self._list[self._list.length - 1];  // Get most recent
                    self._current = new StructuredBlock(sig.hash, null, verbose);   // Store in _current
                }
                if (success) { success(undefined); }  // Note success is applied to the MB, not to the content, and the content might not have been loaded.
            },
            error);
    }

    p_updatelist(){ console.assert(false, "Need to define p_ function")}

    async_updatelist(ul, verbose, successmethodeach, error) { console.trace(); console.assert(false, "OBSOLETE"); //TODO-IPFS obsolete with p_fetch
        // You can't pass "success" to updatelist as it spawns multiple threads
        //successmethodeach is method to apply to each element, see the path() function for definition
        while (ul.hasChildNodes()) {
            ul.removeChild(ul.lastChild);
        }
        let blocks = this.blocks(verbose);
        for (let ii in blocks) {     // Signed Blocks
            //noinspection JSUnfilteredForInLoop
            let i = blocks[ii];
            let li = document.createElement("li");
            ul.appendChild(li);
            i.async_load(verbose,
                function (msg) {
                    i.async_elem(li, verbose, successmethodeach, error);
                },
                error);
        }
    }

    p_update(){ console.assert(false, "Need to define p_ function")}

    async_update(type, data, verbose, success, error) {   console.trace(); console.assert(false, "OBSOLETE"); //TODO-IPFS obsolete with p_fetch // Send new data for this item to dWeb
        Dweb.transport.async_update(this, this._hash, type, data, verbose, success, error);
    }

    _p_storepublic(verbose) {
        // Note that this returns immediately after setting hash, so caller may not need to wait for success
        //(hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose, options)
        let mb = new MutableBlock(null, null, false, this.keypair, false, null, null, null, verbose, {"name": this.name});
        let prom = mb.p_store(verbose);    // Returns immediately but sets _hash first
        this._publichash = mb._hash;
        return prom;    // Have to return prom after set publichash
    }

    _async_storepublic(verbose, success, error) { console.trace(); console.assert(false, "OBSOLETE"); //TODO-IPFS obsolete with p_fetch
        // Note that this returns immediately after setting hash, so caller may not need to wait for success
        //(hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose, options)
        let mb = new MutableBlock(null, null, false, this.keypair, false, null, null, null, verbose, {"name": this.name});
        mb.async_store(verbose, success, error);    // Returns immediately but sets _hash first
        this._publichash = mb._hash;
    }

    contentacl() {console.assert(false, "XXX Undefined function MutableBlock.contentacl setter and getter"); }   // Encryption of content

    p_fetch(verbose) {
        /*
         COPIED FROM JS MutableBlock.fetch 2017-05-24
         :return: self for chaining
         */
        if (verbose) console.log("MutableBlock.p_fetch hash=", this._hash);
        let self = this;
        return super.p_fetch(verbose)
        .then(() => { self.p_fetchlist(); return self})
    }

    async_load(verbose, success, error) { console.trace(); console.assert(false, "OBSOLETE"); //TODO-IPFS obsolete with p_fetch
        /*
         COPIED FROM JS MutableBlock.fetch 2017-05-24
         :return: self for chaining
         */
        if (verbose) console.log("MutableBlock.fetch pubkey=", self._hash);
        let self = this;
        super.async_load(verbose, function (msg) {
            self.async_fetchlist(success, error); }, error);
        return self;
    }

    content() {
        console.assert(!this._needsfetch, "Content is asynchronous, must load first");
        return this._current.content();
    }

    file() {
        console.assert(false, "XXX Undefined function MutableBlock.store");
    }   // Retrieving data

    p_signandstore(verbose){
        /*
         Sign and Store a version, or entry in MutableBlock master
         Exceptions: SignedBlockEmptyException if neither hash nor structuredblock defined, ForbiddenException if !master

         :return: self to allow chaining of functions
         */
        if ((!this._current._acl) && this.contentacl) {
            this._current._acl = this.contentacl;    //Make sure SB encrypted when stored
            this._current.dirty();   // Make sure stored again if stored unencrypted. - _hash will be used by signandstore
        }
        return super.p_signandstore(this._current, verbose) // ERR SignedBlockEmptyException, ForbiddenException
    }

    async_signandstore(verbose, success, error) { console.trace(); console.assert(false, "OBSOLETE"); //TODO-IPFS obsolete with p_fetch
        /*
         Sign and Store a version, or entry in MutableBlock master
         Exceptions: SignedBlockEmptyException if neither hash nor structuredblock defined, ForbiddenException if !master

         :return: self to allow chaining of functions
         */
        if ((!this._current._acl) && this.contentacl) {
            this._current._acl = this.contentacl;    //Make sure SB encrypted when stored
            this._current.dirty();   // Make sure stored again if stored unencrypted. - _hash will be used by signandstore
        }
        return super.async_signandstore(this._current, verbose, success, error) // ERR SignedBlockEmptyException, ForbiddenException
    }

    p_path(patharr, verbose, successmethod) { // obsoletes async_path
        if (verbose) console.log("mb.async_path", patharr, successmethod);
        //sb.async_path(patharr, verbose, successmethod, error) {
        let curr = this._current;
        return curr.p_fetch(verbose)
            .then((obj) => obj.p_path(patharr, verbose, successmethod));
    }

    async_path(patharr, verbose, successmethod, error) { console.trace(); console.assert(false, "OBSOLETE"); //TODO-IPFS obsolete with p_fetch
        if (verbose) {
            console.log("mb.async_path", patharr, successmethod);
        }
        //sb.async_path(patharr, verbose, successmethod, error) {
        let curr = this._current;
        curr.async_load(verbose,
            function (msg) {
                curr.async_path(patharr, verbose, successmethod, error);
            },
            error);
    }

    static p_new(acl, contentacl, name, _allowunsafestore, content, signandstore, verbose) {
        /*
         Utility function to allow creation of MB in one step
         :param acl:             Set to an AccessControlList or KeyChain if storing encrypted (normal)
         :param contentacl:      Set to enryption for content
         :param name:            Name of block (optional)
         :param _allowunsafestore: Set to True if not setting acl, otherwise wont allow storage
         :param content:         Initial data for content
         :param verbose:
         :param signandstore:    Set to True if want to sign and store content, can do later
         :param options:
         :return:
         */
        // See test.py.test_mutableblock for canonical testing of python version of this
        if (verbose) console.log("MutableBlock.p_new: Creating MutableBlock", name);
        // (hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose)
        let mblockm = new MutableBlock(null, null, true, null, true, null, null, contentacl, verbose, {"name": name}); // (name=name  // Create a new block with a new key
        mblockm._acl = acl;              //Secure it
        mblockm._current.data = content;  //Preload with data in _current.data
        mblockm._allowunsafestore = _allowunsafestore;
        if (_allowunsafestore) {
            mblockm.keypair._allowunsafestore = true;
        }
        if (signandstore && content) {
            return mblockm.p_store(verbose)
                .then((msg) => mblockm.p_signandstore(verbose)) //Sign it - this publishes it
                    .then(() => mblockm)
        } else {
            return mblockm.p_store(verbose)
                .then(() => mblockm)
        }
    }

    static test(sb, transport, verbose) {
        let mb;
        if (verbose) console.log("MutableBlock.test starting");
        return new Promise((resolve, reject) => {
            try {
                //(hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose, options
                let mb1 = new Dweb.MutableBlock(null, null, true, null, false, null, sb._hash, null, verbose, null);
                mb1.p_store(verbose) // Async, should set hash immediately but wait to retrieve after stored.
                    .then(() => mb = new MutableBlock(mb1._hash, null, false, null, false, null, null, null, verbose, null))
                    .then(() => mb.p_loadandfetchlist(verbose))
                    .then(() => console.log("TODO-IPFS This isn't finished yet, mb will not have the data as mb1 didnt publish it yet which needs crypto")) //sb, mb1, mb
                    //TODO-IPFS uncomment next line when have crypto etc
                    // .then(() => console.assert(mb._current.data === sb.data, "Should have retrieved"))
                    //.then(() => mb.p_path(["langs", "readme.md"], verbose, ["p_elem", "myList.1", verbose,]))
                    .then(() => console.log("MutableBlock.test promises done"))
                    .then(() => resolve({mb: mb}))
                    .catch((err) => {
                        console.log("Error in MutableBlock.test", err);   // Log since maybe "unhandled" if just throw
                        reject(err);
                    })
            } catch (err) {
                console.log("Caught exception in MutableBlock.test", err)
                raise(err)
            }
        })
    }
}
exports = module.exports = MutableBlock;
