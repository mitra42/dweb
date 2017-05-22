// ######### Parallel development to CommonBlock.py ########
const CryptoLib = require("./CryptoLib");
const Dweb = require("./Dweb");

class Transportable {
    // Based on Transportable class in python - generic base for anything transportable.

    constructor(hash, data) {
        this._hash = hash;  // Hash of the _data
        this._setdata(data); // The data being stored - note _setdata usually subclassed
        if (hash && !data) { this._needsfetch = true; }
    }

    _setdata(value) {
        this._data = value;  // Default behavior, assumes opaque bytes, and not a dict - note subclassed in SmartDict
    }
    _getdata() {
        return this._data;  // Default behavior - opaque bytes
    }

    async_store(verbose, success, error) {    // Python has a "data" parameter to override this._data but probably not needed
        if (verbose) console.log("Transportable.store", this);
        let data = this._getdata();
        if (verbose) console.log("Transportable.store data=", data);
        this._hash = CryptoLib.Curlhash(data); //store the hash since the HTTP is async
        let self = this;
        Dweb.transport.async_rawstore(this, data, verbose,
            function(msg) {
                if (msg !== self._hash) {
                    console.log("ERROR Hash returned ",msg,"doesnt match hash expected",self._hash);
                    if (error) { error(); }
                } else {
                    if (success) { success(msg)}
                }
            },
            error); // Returns immediately BEFORE storing
        if (verbose) { console.log("Transportable.store hash=", this._hash); }
        return this;    // For chaining, hash is valid, but note not yet stored
    }

    dirty() {   // Flag as dirty so needs uploading - subclasses may delete other, now invalid, info like signatures
        this._hash = null;
    }

    fetch() { console.log("XXX Undefined function Transportable.fetch"); } // Replaced by load

    async_load(verbose, success, error) {
        // Asynchronous equiv of fetch
        // Runs success whether needs to load or not as will often load and then do something.
        if (verbose) { console.log("Transportable.load hash=",this._hash); }
        if (this._needsfetch) { // Only load if need to
            let self = this;
            Dweb.transport.async_rawfetch(this, this._hash, verbose,
                function(data) {
                    if (data) {self._setdata(data)}
                    if (success) { success(undefined);} //Not passing data as stored above
                },
                error);
            this._needsfetch = false;    // Set false before return so not multiply fetched
        } else {
            if(success) { success(null); }
        }
        // Block fetched in the background - dont assume loaded here - see success for actions post-load
    }

    file() { console.log("XXX Undefined function Transportable.file"); }
    url() { console.log("XXX Undefined function Transportable.url"); }
    content() { console.log("Intentionally undefined function Transportable.content - superclass should define"); }
    async_updatelist() { console.log("Intentionally undefined function Transportable.async_updatelist - meaningless except on CL"); }

    // ==== UI method =====

    async_elem(el, verbose, successmethodeach, error) {
        // Called from success methods
        //successeach is function to apply to each element, will be passed "this" for the object being stored at the element.
        if (this._needsfetch) {
            let self = this;
            this.async_load(verbose, function(msg){self.async_elem(el, verbose, successmethodeach, error)}, error);
        } else {
            if (typeof el === 'string') {
                el = document.getElementById(el);
            }
            let data = this.content(verbose);
            if (typeof data === 'string') {
                if (verbose) { console.log("elem:Storing data to element",el,encodeURI(data.substring(0,20))); }
                el.innerHTML = data;
                if (successmethodeach) {
                    let methodname = successmethodeach.shift();
                    //if (verbose) console.log("async_elem",methodname, successmethodeach);
                    this[methodname](...successmethodeach); // Spreads successmethod into args, like *args in python
                }
            } else if (Array.isArray(data)) {
                if (verbose) { console.log("elem:Storing list of len",data.length,"to element",el);}
                this.async_updatelist(el, verbose, successmethodeach, error);  //Note cant do success on updatelist as multi-thread //TODO using updatelist not replacing
            } else {
                console.log("ERROR: unknown type of data to elem",typeof data, data);
            }
        }
    }

    //noinspection JSUnusedGlobalSymbols
    tell(data, hash, verbose, options) {  //TODO change fingerprint, wont take some of these args
        // Can be included in a successfunction to callback
        // This might get refactored as understand how to use it - currently unused (comment here if that changes)
        let context = {"notifier": this, "data": data, "hash": hash};
        let notified = options[0];
        let method = options[1];
        let newoptions = options[2];
        notified[method](context, verbose, newoptions);
    }
}
exports = module.exports = Transportable;

