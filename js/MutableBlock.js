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

    p_elem(el, verbose, successmethodeach) {
        if (this._needsfetch) {
            return this.p_fetch(verbose)
                .then((self) => self.p_elem(el, verbose, successmethodeach))
        } else {
            // this._current should be setup, it might not be loaded, but p_elem can load it
            return this._current.p_elem(el, verbose, successmethodeach);    // Typically _current will be a SB
        }
    }

    p_fetchlist(verbose) {
        // Superclasses CL.p_fetchlist as need to set _current on a MB
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

    /* OBSOLETE - but copy concept into anything publishing a list
    p_updatelist(ul, verbose, successmethodeach) {
        // You can't pass "success" to updatelist as it spawns multiple threads
        //successmethodeach is method to apply to each element, see the path() function for definition
        while (ul.hasChildNodes()) {
            ul.removeChild(ul.lastChild);
        }
        self.p_fetch_then_list_then_elem


        let blocks = this.blocks(verbose);  // Need to replace this, its like p_find_then_list_then_elements followed by loop on them

        for (let ii in blocks) {     // Signed Blocks - needs to be loop as should happen sequentionlly
            //noinspection JSUnfilteredForInLoop
            let i = blocks[ii];
            let li = document.createElement("li");
            ul.appendChild(li);
            i.p_fetch(verbose)
                .then((self) => i.p_elem(li, verbose, successmethodeach));
        }
    }
    */

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
    }

    contentacl() {console.assert(false, "XXX Undefined function MutableBlock.contentacl setter and getter"); }   // Encryption of content

    p_fetch_then_list_then_current(verbose) {
        /*
         Fetch a MB, then fetch list, then content.

         :return: Returns a promise that itself returns self for chaining
         */
        if (verbose) console.log("MutableBlock.p_fetch hash=", this._hash);
        let self = this;
        return super.p_fetch_then_list(verbose)
            .then(() => self._current && self._current.p_fetch(verbose))
            .then(() => self )
    }

    content() {
        console.assert(!this._needsfetch, "Content is asynchronous, must load first");
        return this._current.content();
    }

    file() {
        console.assert(false, "XXX Undefined function MutableBlock.file");
    }   // Retrieving data

    p_signandstore(verbose){    //TODO-AUTHENTICATION - add options to remove old signatures by same
        /*
         Sign and Store a version, or entry in MutableBlock master
         Exceptions: SignedBlockEmptyException if neither hash nor structuredblock defined, ForbiddenException if !master

         :return: self to allow chaining of functions
         */
        if ((!this._current._acl) && this.contentacl) {
            this._current._acl = this.contentacl;    //Make sure SB encrypted when stored
            this._current.dirty();   // Make sure stored again if stored unencrypted. - _hash will be used by signandstore
        }
        return super.p_signandstore(this._current, verbose)
            .then((sig) => { this._current._signatures.push(sig); return sig} )// Promise resolving to sig, ERR SignedBlockEmptyException, ForbiddenException

    }

    p_path(patharr, verbose, successmethod) {
        if (verbose) console.log("mb.p_path", patharr, successmethod);
        //sb.p_path(patharr, verbose, successmethod) {
        let curr = this._current;
        return curr.p_fetch(verbose)
            .then((obj) => obj.p_path(patharr, verbose, successmethod));
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


    static test(sb, verbose) {
        let mb;
        if (verbose) console.log("MutableBlock.test starting");
        return new Promise((resolve, reject) => {
            try {
                //(hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose, options
                let mb1 = new Dweb.MutableBlock(null, null, true, null, true, null, sb._hash, null, verbose, null);
                mb1._allowunsafestore = true; // No ACL, so shouldnt normally store, but dont want this test to depend on ACL
                let siglength = mb1._list.length; // Will check for size below
                mb1.p_signandstore(verbose) // Async, should set hash immediately but wait to retrieve after stored.
                    //.then(() => console.log("mb1.test after signandstore=",mb1))
                    .then(() => console.assert(mb1._list.length === siglength+1))
                    //MutableBlock(hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose, options) {
                    .then(() => mb = new MutableBlock(mb1._publichash, null, false, null, false, null, null, null, verbose, null))
                    .then(() => mb.p_fetch_then_list_then_current(verbose))
                    //.then(() => console.log("mb.test retrieved=",mb))
                    .then(() => console.assert(mb._list.length === siglength+1, "Expect list",siglength+1,"got",mb._list.length))
                    .then(() => console.assert(mb._current.data === sb.data, "Should have retrieved"))
                    //.then(() => mb.p_path(["langs", "readme.md"], verbose, ["p_elem", "myList.1", verbose,])) //TODO-PATH need a path based test
                    .then(() => { if (verbose) console.log("MutableBlock.test promises done"); })
                    .then(() => resolve({mb: mb}))
                    .catch((err) => {
                        console.log("Error in MutableBlock.test", err);   // Log since maybe "unhandled" if just throw
                        reject(err);
                    })
            } catch (err) {
                console.log("Caught exception in MutableBlock.test", err);
                throw(err)
            }
        })
    }
}
exports = module.exports = MutableBlock;
