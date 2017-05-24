const SmartDict = require("./SmartDict");
const Signature = require("./Signature");
const Dweb = require("./Dweb");

// ######### Parallel development to StructuredBlock.py ########

class StructuredBlock extends SmartDict {
    constructor(hash, data, verbose) {
        super(hash, data, verbose); // _hash is _hash of SB, not of data
        this._signatures = [];
        this._date = null;  // Updated in _earliestdate when loaded
        this.table = "sb";  // Note this is cls.table on python but need to separate from dictionary
    }
    async_store(verbose, success, error) {
        /*
         Store content if not already stored (note it must have been stored prior to signing)
         Store any signatures in the Transport layer
         */
        if (!this._hash) {
            super.async_store(verbose, success, error);    //Sets self._hash doesnt store if hasnt changed
        }
        for (let i in this._signatures) {
            let s = this._signatures[i];
            //PY makes copy of s, but this is because the json procedure damages the object which doesnt happen in Crypto.dumps in JS
            Dweb.transport.async_add(this._hash, s.date, s.signature, s.signedby, null, verbose, success, error);
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

    async_path(patharr, verbose, successmethod, error) {
        // We cant use a function here, since the closure means it would apply to the object calling this, not the object loaded.
        // successmethod is an array [ nameofmethod, args... ]
        // Warning - may change the signature of this as discover how its used.
        if (verbose) { console.log("sb.async_path",patharr, successmethod, "links=",this.links); }
        if (patharr && patharr.length && this.links.length ) { // Have a path and can do next bit of it on this sb
            let next = patharr.shift(); // Takes first element of patharr, leaves patharr as rest
            if (verbose) { console.log("StructuredBlock:path next=",next); }
            let obj = this.link(next);   //TODO handle error if not found
            obj.async_load(verbose, function(msg) { obj.async_path(patharr, verbose, successmethod, error); }, error);
        } else if (patharr && patharr.length) {
            console.log("ERR Can't follow path",patharr);
            if (error) error(undefined);
        } else {  // Reached end of path, can apply success
            //if (success) { success(undefined); } //note this wont work as success defined on different object as "this"
            if (successmethod) {
                let methodname = successmethod.shift();
                if (verbose) { console.log("async_path success:",methodname, successmethod); }
                this[methodname](...successmethod); // Spreads successmethod into args, like *args in python
            }
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
    file() { console.log("XXX Undefined function StructuredBlock.file"); }
    size() { console.log("XXX Undefined function StructuredBlock.size"); }

    sign(commonlist, verbose) {
        /*
         Add a signature to a StructuredBlock
         Note if the SB has a _acl field it will be encrypted first, then the hash of the encrypted block used for signing.
         :param CommonList commonlist:   List its going on - has a ACL with a private key
         :return: self
         */
        if (!this._hash) this.async_store(verbose);  // Sets _hash immediately which is needed for signatures
        if (!commonlist._publichash) commonlist.async_store(verbose);    // Set _publichash immediately (required for Signature.sign)
        this._signatures.push(Signature.sign(commonlist, this._hash, verbose));
        return this;  // For chaining
    }
    verify() { console.log("XXX Undefined function StructuredBlock.verify"); }


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

}exports = module.exports = StructuredBlock;
