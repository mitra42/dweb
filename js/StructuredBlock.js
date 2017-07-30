const SmartDict = require("./SmartDict");
const Signature = require("./Signature");
const Dweb = require("./Dweb");


// ######### Parallel development to StructuredBlock.py ########

class StructuredBlock extends SmartDict {

    //p_fetch uses SmartDict ..
    constructor(hash, data, verbose) {
        super(hash, data, verbose); // _hash is _hash of SB, not of data
        this._signatures = [];
        this._date = null;  // Updated in _earliestdate when loaded
        this.table = "sb";  // Note this is cls.table on python but need to separate from dictionary
    }
    p_store(verbose) {
        /*
         Store content if not already stored (note it must have been stored prior to signing)
         Store any signatures in the Transport layer
         Resolution of promise will happen on p_store, the addition of signatures will happen async - could change to Promise.all
         */
        if (!this._hash) {
            return super.p_store(verbose);    //Sets self._hash and stores in background if has changed
        }
        for (let i in this._signatures) {
            let s = this._signatures[i];
            //PY makes copy of s, but this is because the json procedure damages the object which doesnt happen in Crypto.dumps in JS
            Dweb.transport.p_add(this._hash, s.date, s.signature, s.signedby, null, verbose);
        }
        return this; // For chaining

    }

    __setattr__(name, value) {
        // Call chain is ...  or constructor > _setdata > _setproperties > __setattr__
        // catch equivalent of getters and setters here
        let verbose = false;
        if (name === "links") {  // Assume its a SB TODO make dependent on which table
            let links = value;
            for (let len = links.length, i=0; i<len; i++) {
                links[i] = new StructuredBlock(null, links[i], verbose);
            }
            this[name] = links;
        } else {
            super.__setattr__(name, value);
        }
    }

    p_path(patharr, verbose, successmethod) {
        // We cant use a function here, since the closure means it would apply to the object calling this, not the object loaded.
        // successmethod is an array [ nameofmethod, args... ]
        // Warning - may change the signature of this as discover how its used.
        if (verbose) { console.log("sb.p_path",patharr, successmethod, "links=",this.links); }
        if (patharr && patharr.length && this.links && this.links.length ) { // Have a path and can do next bit of it on this sb
            let next = patharr.shift(); // Takes first element of patharr, leaves patharr as rest
            if (verbose) { console.log("StructuredBlock:path next=",next); }
            let obj = this.link(next);   //TODO handle error if not found
            return obj.p_fetch(verbose).then(() => obj.p_path(patharr, verbose))
        } else if (patharr && patharr.length) {
            throw new Error("Cant follow path"+patharr);
        } else {  // Reached end of path, can apply success
            //TODO-IPFS unsure if have this correct
            //if (success) { success(undefined); } //note this wont work as success defined on different object as "this"
            if (successmethod) {
                let methodname = successmethod.shift();
                if (verbose) { console.log("p_path success:",methodname, successmethod); }
                this[methodname](...successmethod); // Spreads successmethod into args, like *args in python
            }
            return new Promise((resolve, reject)=> resolve(null));  // I think this should be a noop - fetched already
        }
    }

    dirty() {
        super.dirty();
        this._signatures = [];
    }

    link(name) {    // Note python version allows call by number as well as name
        let links = this.links;
        for (let len = links.length, i=0; i<len; i++) {
            if (links[i].name === name) {
                return links[i]
            }
        }
        console.log("Didn't find",name);
        return null;    // If not found
    }

    content(verbose) {
        console.assert(!this._needsfetch, "Must load before call content");
        if (this.data) { return this.data; }
        if (this.links) {
            let res = "";
            for (let i in this.links) {
                //noinspection JSUnfilteredForInLoop
                let l = this.links[i];
                res = res + l.content(verbose)  //Each link is a SB
            }
            return res;
        }
        console.log("ERR - object has no content, not even empty data");
        //Not supporting hash/fetch as async
        //(this.hash and Dweb.transport.rawfetch(hash = self.hash, verbose=verbose, **options)) or # Hash must point to raw data, not another SB
    }
    file() { console.assert(false, "XXX Undefined function StructuredBlock.file"); }
    size() { console.assert(false, "XXX Undefined function StructuredBlock.size"); }

    sign(commonlist, verbose) {
        /*
         Add a signature to a StructuredBlock
         Note if the SB has a _acl field it will be encrypted first, then the hash of the encrypted block used for signing.
         :param CommonList commonlist:   List its going on - has a ACL with a private key
         :return: sig so that CommonList can add to _list
         */
        if (!this._hash) this.p_store(verbose);  // Sets _hash immediately which is needed for signatures
        if (!commonlist._publichash) commonlist.p_store(verbose);    // Set _publichash immediately (required for Signature.sign)
        let sig = Signature.sign(commonlist, this._hash, verbose)
        this._signatures.push(sig);
        return sig;  // so that CommonList can add to _list
    }
    verify() { console.assert(false, "XXX Undefined function StructuredBlock.verify"); }


    earliestdate(){    // Set the _date field to the earliest date of any signature or null if not found
        if (!this._signatures) {
            this._date = null;
        } else {
            if (!this._date) {
                this._date = this._signatures[0]["date"];
                for (let i = 1; this._signatures.length > i; i++) {
                    if ( this._date > this._signatures[i]["date"]) {
                        this._date = this._signatures[i]["date"];
                    }
                }
            }
        }
        return this._date;
    }

    static compare(a, b) {
        if (a.earliestdate() > b.earliestdate()) { return 1; }
        if (b.earliestdate() > a.earliestdate()) { return -1; }
        return 0;
    }

    static test(transport, document, verbose) {
        if (verbose) console.log("StructuredBlock.test")
        return new Promise((resolve, reject) => {
            let el = document.getElementById("myList.0");
            console.log("XXX@make assert: el=", el);
            try {
                let teststr = "The well structured block"
                let sb = new StructuredBlock(null, {"data": teststr});
                let sb2;
                if (verbose) {
                    console.log("StructuredBlock.test sb=", sb);
                }
                sb.p_store(verbose)
                    .then(() => sb2 = new StructuredBlock(sb._hash, null))   // Creates, doesnt fetch
                    .then(() => sb2.p_fetch())
                    .then(() => {
                        if (verbose) console.assert(sb2.data === teststr, "SB should round trip", sb2.data, "!==", teststr)
                    })
                    /* //TODO-IPFS create a test set of SB's that have a path
                    .then(() => sb.p_path(["langs", "readme.md"], verbose, ["p_elem", el, verbose, null]))
                    //To debug, uncomment the el.textContent line in Transportable.p_elem
                     */
                    .then(() => {
                        if (verbose) console.log("StructuredBlock.test promises complete")
                        resolve({sb: sb, sb2: sb2});
                    })
                    .catch((err) => {
                        console.log("Error in StructuredBlock.test", err);   // Log since maybe "unhandled" if just throw
                        reject(err);
                    })
            } catch (err) {
                console.log("Caught exception in StructuredBlock.test", err)
                raise(err)
            }
        })
    }
}exports = module.exports = StructuredBlock;
