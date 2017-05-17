// Javascript library for dweb
// The crypto uses https://github.com/jedisct1/libsodium.js but https://github.com/paixaop/node-sodium may also be suitable if we move to node

//var dwebserver = 'localhost';
const dwebserver = '192.168.1.156';
const dwebport = '4243';
const Dweb = {}; // Note const just means it cant be assigned to a new dict, but dict can be modified
Dweb.keychains = [];
// Constants
const KEYPAIRKEYTYPESIGN = 1;
const KEYPAIRKEYTYPEENCRYPT = 2;
const KEYPAIRKEYTYPESIGNANDENCRYPT = 3;

//TODO-ASYNC-SIGN - sign and signandstore
//TODO-ASYNC - search on TODO-ASYNC
//TODO-ASYNC - fix objbrowser's path
// ==== OBJECT ORIENTED JAVASCRIPT ===============

// These are equivalent of python exceptions, will log and raise alert in most cases - exceptions aren't caught
function SecurityWarning(msg, self) {
    console.log(msg, self);
    alert(msg);
}

// Utility functions

function mergeTypedArraysUnsafe(a, b) { // Take care of inability to concatenate typed arrays
    //http://stackoverflow.com/questions/14071463/how-can-i-merge-typedarrays-in-javascript also has a safe version
    const c = new a.constructor(a.length + b.length);
    c.set(a);
    c.set(b, a.length);
    return c;
}
//TODO document from here down


class Transport {
    //noinspection JSUnusedLocalSymbols
    constructor(verbose, options) { }
    setup() { console.log("XXX Undefined function Transport.setup"); }
    _lettertoclass() { console.log("XXX Undefined function Transport._lettertoclass"); }
    info() { console.log("XXX Undefined function Transport.info"); }
    async_rawfetch() { console.log("XXX Undefined function Transport.rawfetch"); }
    //noinspection JSUnusedGlobalSymbols
    async_fetch() { console.log("XXX Undefined function Transport.fetch"); }
    async_rawlist() { console.log("XXX Undefined function Transport.rawlist"); }
    async_list() { console.log("XXX Undefined function Transport.list"); }
    //noinspection JSUnusedGlobalSymbols
    async_rawreverse() { console.log("XXX Undefined function Transport.rawreverse"); }
    //noinspection JSUnusedGlobalSymbols
    async_reverse() { console.log("XXX Undefined function Transport.reverse"); }
    async_rawstore() { console.log("XXX Undefined function Transport.rawstore"); }
    async_store() { console.log("XXX Undefined function Transport.store"); }
    //noinspection JSUnusedLocalSymbols
    async_rawadd(hash, date, signature, signedby, verbose) { console.log("XXX Undefined function Transport.rawadd"); }

    async_add(hash, date, signature, signedby, obj, verbose, success, error) {
        if (obj && !hash) hash = obj._hash;
        return this.async_rawadd(hash, date, signature, signedby, verbose, success, error);
    }

    static _add_value(hash, date, signature, signedby, verbose) {
        let store = {"hash": hash, "date": date, "signature": signature, "signedby": signedby};
        return CryptoLib.dumps(store);
    }
}
class TransportHttpBase extends Transport {
    constructor(ipandport, verbose, options) {
        super(verbose, options);
        this.ipandport = ipandport;
        this.baseurl = "http://" + ipandport[0] + ":" + ipandport[1] + "/";
    }
    async_load(command, hash, verbose, success, error) {
        // Locate and return a block, based on its multihash
        // Call chain for list is mb.load > CL.fetchlist > THttp.rawlist > Thttp.load > CL|MB.fetchlist.success > callers.succes
        if (verbose) { console.log("TransportHTTP async_load:",command, ":hash=", hash); }
        let url = this.url(command, hash);
        if (verbose) { console.log("TransportHTTP:async_load: url=",url); }
        $.ajax({
            type: "GET",
            url: url,
            success: function(data) {
                if (verbose) { console.log("TransportHTTP:", command, hash, ": returning data len=", data.length); }
                // Dont appear to need to parse JSON data, its decoded already
                if (success) { success(data); }
            },
            error: function(xhr, status, error) {
                console.log("TransportHTTP:", command, ": error", status, "error=",error);
                alert("TODO Block failure status="+status+" "+command+" error="+error);
                if (error) { error(xhr, status, error);}
            },
        });
    }
    async_post(command, hash, type, data, verbose, success, error) {
        // Locate and return a block, based on its multihash
        if (verbose) { console.log("TransportHTTP post:", command,":hash=", hash); }
        let url = this.url(command, hash);
        if (type) {
            url += "/" + type;
        }
        if (verbose) { console.log("TransportHTTP:post: url=",url); }
        if (verbose) { console.log("TransportHTTP:post: data=",data); }
        $.ajax({
            type: "POST",
            url: url,
            data: { "data": data},
            success: function(msg) {
                if (verbose) { console.log("TransportHTTP:", command, hash, ": returning data len=", msg.length); }
                // Dont appear to need to parse JSON data, its decoded already
                if (success) { success(msg); }
            },
            error: function(xhr, status, error) {
                console.log("TransportHTTP:", command, "error", status, "error=",error, "data=", data);
                alert("TODO post "+command+" failure status="+status+" error="+error);
                if (error) { error(xhr, status, error);}
            },
        });
    }
    info() { console.log("XXX Undefined function Transport.info"); }

    url(command, hash) {
        let url = this.baseurl + command;
        if (hash) {
            url += "/" + hash;
        }
        return url;
    }

}
class TransportHttp extends TransportHttpBase {

    constructor(ipandport, verbose, options) {
        super(ipandport, options);
        this.options = options; // Dictionary of options, currently unused
    }

    static setup(ipandport, options) {
        let verbose = false;    //TODO check if should be in args
        return new TransportHttp(ipandport, verbose, options);
    }
    async_rawfetch(self, hash, verbose, success, error) {    //TODO merge with transport.list
        // Locate and return a block, based on its multihash
        this.async_load("rawfetch", hash, verbose, success, error);
    }
    async_rawlist(self, hash, verbose, success, error) {
        // obj being loaded
        // Locate and return a block, based on its multihash
        // Call chain is mb.load > CL.fetchlist > THttp.rawlist > Thttp.load > CL|MB.fetchlist.success > callers.success
        this.async_load("rawlist", hash, verbose, success, error);
    }
    rawreverse() { console.log("XXX Undefined function TransportHTTP.rawreverse"); }

    async_rawstore(self, data, verbose, success, error) {
        //PY: res = self._sendGetPost(True, "rawstore", headers={"Content-Type": "application/octet-stream"}, urlargs=[], data=data, verbose=verbose)
        this.async_post("rawstore", null, null, data, verbose, success, error) // Returns immediately
    }

    async_rawadd(self, hash, date, signature, signedby, verbose, success, error) {
        if (verbose) console.log("rawadd", hash, date, signature, signedby);
        let value = Transport._add_value( hash, date, signature, signedby, verbose)+ "\n";
        //async_post(self, command, hash, type, data, verbose, success, error)
        this.async_post("rawadd", null, "application/json", value, verbose, success, error); // Returns immediately
    }

    async_update(self, hash, type, data, verbose, success, error) {
        this.async_post("update", hash, type, data, verbose, success, error);
    }
}

const transport = TransportHttp.setup([dwebserver, dwebport], {});

// ######### Parallel development to CommonBlock.py ########

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
        transport.async_rawstore(this, data, verbose,
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
            transport.async_rawfetch(this, this._hash, verbose,
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

class SmartDict extends Transportable {
    constructor(hash, data, verbose, options) {
        // data = json string or dict
        super(hash, data); // _hash is _hash of SB, not of data - will call _setdata (which usually set fields), -note does not fetch the has, but sets _needsfetch
        this._setproperties(options);   // Note this will override any properties set with data
    }
    __setattr__(name, value) { // Call chain is ... success or constructor > _setdata > _setproperties > __setattr__
        // Subclass this to catch any field (other than _data) which has its own setter
        //TODO Need a javascript equivalent way of transforming date
        // if (name[0] != "_") {
        //    if "date" in name and isinstance(value,basestring):
        //        value = dateutil.parser.parse(value)
        //}
        //TODO - instead of calling "setter" automatically, assuming that __setattr__ in each class does so.
        this[name] = value; //TODO: Python-Javascript: In Python can assume will get methods of property e.g. _data, in javascript need to be explicit here, or in caller.
    }
    _setproperties(dict) { // Call chain is ... onloaded or constructor > _setdata > _setproperties > __setattr__
        if (dict) { // Ignore dict if null
            for (let prop in dict) {
                //noinspection JSUnfilteredForInLoop
                this.__setattr__(prop, dict[prop]);
            }
        }
    }
    preflight(dd) { // Called on outgoing dictionary of outgoing data prior to sending - note order of subclassing can be significant
        let res = {};
        for (let i in dd) {
            if (i.indexOf('_') !== 0) { // Ignore any attributes starting _
                if (dd[i] instanceof Transportable) {
                    res[i] = dd[i].async_store(false, null, null)._hash  // store(verbose, success, error) - will set hash, then store obj in background
                } else {
                    res[i] = dd[i];
                }
            }
        }
        // Note table is a object attribute in JS, so copied above (in Python its a class attribute that needs copying
        return res
    }

    _getdata() {
        let dd = {};
        for (let i in this) {
            //noinspection JSUnfilteredForInLoop
            dd[i] = this[i];    // This just copies the attributes not functions
        }
        let res = CryptoLib.dumps(this.preflight(dd));
        if (this._acl) { //Need to encrypt
            let encdata = this._acl.encrypt(res, true);  // data, b64
            let dic = { "encrypted": encdata, "acl": this._acl._publichash, "table": this.table};
            res = CryptoLib.dumps(dic);
        }
        return res
    }    // Should be being called on outgoing _data includes dumps and encoding etc

    _setdata(value) {
        // Note SmartDict expects value to be a dictionary, which should be the case since the HTTP requester interprets as JSON
        // Call chain is ...  or constructor > _setdata > _setproperties > __setattr__
        if (value) {    // Skip if no data
            if (typeof value === 'string') {    // Assume it must be JSON
                value = JSON.parse(value);
            }
            // value should be a dict by now, not still json as it is in Python
            //TODO-AUTHENTICTION - decrypt here
            this._setproperties(value); // Note value should not contain a "_data" field, so wont recurse even if catch "_data" at __setattr__()
        }
    }

    objbrowser(hash, path, ul, verbose) {
        let hashpath = path ? [hash, path].join("/") : hash;
    //OBSdwebobj(ul, hashpath) {    //TODO - note this is under dev works on SB and MB, needs to work on KeyChain, AccessControlList etc
        // ul is either the id of the element, or the element itself.
        //TODO-follow link arrow
        //console.log("dwebobj",ul)
        if (typeof ul === 'string') {
            ul = document.getElementById(ul);
        }
        let li = document.createElement("li");
        li.source = this;
        li.className = "propobj";
        ul.appendChild(li);
        //li.innerHTML = "<B>StructuredBlock:</B>" + hashpath;
        let t1 = document.createTextNode(this.constructor.name+": "+hashpath);
        let sp1 = document.createElement('span');
        sp1.className = "classname"; // Confusing!, sets the className of the span to "classname" as it holds a className
        sp1.appendChild(t1);
        li.appendChild(sp1);

        //Loop over dict fields
        let ul2 = document.createElement("ul");
        ul2.className="props";
        li.appendChild(ul2);
        //noinspection JSUnfilteredForInLoop
        for (let prop in this) {
            //noinspection JSUnfilteredForInLoop
            if (this[prop]) {
                //noinspection JSUnfilteredForInLoop
                let text = this[prop].toString();
                if (text !== "" && prop !== "_hash") {    // Skip empty values; _hash (as shown above);
                    let li2 = document.createElement("li");
                    li2.className='prop';
                    ul2.appendChild(li2);
                    //li2.innerHTML = "Field1"+prop;
                    //noinspection JSUnfilteredForInLoop
                    let fieldname = document.createTextNode(prop);
                    let spanname = document.createElement('span');
                    spanname.appendChild(fieldname);
                    spanname.className='propname';
                    //TODO - handle Links by nested list
                    li2.appendChild(spanname);
                    //if ((prop == "links") || (prop == "_list")) {  //StructuredBlock
                    //noinspection JSUnfilteredForInLoop
                    if ( ["links", "_list", "_signatures", "_current"].includes(prop) ) { //<span>...</span><ul proplinks>**</ul>
                        let spanval;
                        spanval = document.createElement('span');
                        spanval.appendChild(document.createTextNode("..."));
                        li2.appendChild(spanval);
                        let ul3 = document.createElement("ul");
                        ul3.className = "proplinks";
                        ul3.style.display = 'none';
                        spanname.setAttribute('onclick',"togglevisnext(this);");
                        //spanname.setAttribute('onclick',"console.log(this.nextSibling)");

                        li2.appendChild(ul3);
                        //TODO make this a loop
                        //noinspection JSUnfilteredForInLoop
                        if (Array.isArray(this[prop])) {
                            //noinspection JSUnfilteredForInLoop
                            for (let l1 in this[prop]) {
                                //noinspection JSUnfilteredForInLoop,JSUnfilteredForInLoop,JSUnfilteredForInLoop,JSUnfilteredForInLoop
                                this[prop][l1].objbrowser(hash, (path ? path + "/":"")+this[prop][l1].name, ul3, verbose);
                            }
                        } else {
                            //noinspection JSUnfilteredForInLoop
                            if (this[prop]._hash) {
                                //noinspection JSUnfilteredForInLoop,JSUnfilteredForInLoop
                                this[prop].objbrowser(this[prop]._hash, null, ul3, verbose)
                            } else {
                                //noinspection JSUnfilteredForInLoop
                                this[prop].objbrowser(hash, path, ul3, verbose);
                            }
                        }
                    } else {    // Any other field
                        let spanval;
                        if (prop === "hash") {
                            //noinspection ES6ConvertVarToLetConst
                            spanval = document.createElement('a');
                            //noinspection JSUnfilteredForInLoop
                            spanval.setAttribute('href','/file/b/'+this[prop]+"?contenttype="+this["Content-type"]);
                        } else {
                            // Group of fields where display then add behavior or something
                            //noinspection ES6ConvertVarToLetConst
                            spanval = document.createElement('span');
                            if (prop === "_needsfetch") {
                                li2.setAttribute('onclick','async_objbrowserfetch(this.parentNode.parentNode);');
                            }
                        }
                        //noinspection JSUnfilteredForInLoop
                        spanval.appendChild(document.createTextNode(this[prop]));
                        spanval.className='propval';
                        li2.appendChild(spanval);
                    }
                    //this.__setattr__(prop, dict[prop]);
                }
             }
        }

    }
}

// ######### Parallel development to Block.py ########

class Block extends Transportable {
    constructor(hash, data) {
        super(hash, data);
        this.table = 'b';
    }
    size() { console.log("XXX Undefined function Block.size"); }
    content() {
        console.assert(!this._needsfetch,"Block should be loaded first as content is sync");
        return this._data;
    }

}

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
            transport.async_add(this._hash, s.date, s.signature, s.signedby, null, verbose, success, error);
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
        if (!this._hash) {
            this.async_store(verbose);  // Sets _hash which is needed for signatures    //TODO-ASYNC not going to work as makes sign async
        }
        this._signatures.push(Signature.sign(commonlist, this._hash, verbose));
        return this  // For chaining
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

}

// ######### Parallel development to SignedBlock.py which also has SignedBlocks and Signatures classes ########

class Signature extends SmartDict {
    constructor(hash, dic, verbose) {
        super(hash, dic, verbose);
        //console.log("Signature created",this.hash);
        //TODO turn s.date into java date
        //if isinstance(s.date, basestring):
        //    s.date = dateutil.parser.parse(s.date)
        this.table = "sig";
    }
    //TODO need to be able to verify signatures
     static sign(commonlist, hash, verbose) {
        let date = datetime.now();  //TODO-DATE //TODO-ASYNC
        let signature = CryptoLib.signature(commonlist.keypair, date, hash);
        console.assert(commonlist._publichash, "CL should have been stored before call to Signature.sign"); // If encounter this, make sure caller stores CL first
        //Python does: if (!commonlist._publichash) commonlist.async_store(verbose, null, null)
        // But this would require making this async.
        return new Signature(null, {"date": date, "signature": signature, "signedby": commonlist._publichash})
    }

    verify() { console.log("XXX Undefined function Signature.verify"); }
}

// ######### Parallel development to MutableBlock.py ########

class CommonList extends SmartDict {
    constructor(hash, data, master, keypair, keygen, mnemonic, verbose, options) {
        // data = json string, or dict
        //TODO implmenent mnemonic, keypair, keygen
        //console.log("CL(", data, master, options,")");
        super(hash, data, verbose, options);
        this._list = [];   // Array of signatures
        if (keygen || mnemonic) {
            this.keypair = KeyPair.keygen(this.keytype(), mnemonic, null, verbose);
        } else {
            this._setkeypair(keypair, verbose);
        }
        this._master = master;  // Note this must be AFTER _setkeypair since that sets based on keypair found and _async_storepublic for example wants to force !master
        if (!this._master) { this._publichash = hash; }
    }
    keytype() { return KEYPAIRKEYTYPESIGN; }

    __setattr__(name, value) {
        // Call chain is ...  or constructor > _setdata > _setproperties > __setattr__
        // catch equivalent of getters and setters here
        let verbose = false;
        if (name === "keypair") {
            this._setkeypair(value, verbose);
        } else {
            super.__setattr__(name, value);
        }
    }

    _setkeypair(value, verbose) {
        // Call chain is ...  or constructor > _setdata > _setproperties > __setattr__ > _setkeypair
        if (value && ! (value instanceof KeyPair)) {
            value = new KeyPair(null, {"key":value}, verbose);  // Synchronous value will be decoded, not fetched
        }
        this.keypair = value;
        this._master = value && value.has_private();
    }

    preflight(dd) {
        if (dd.keypair) {
            if (dd._master && !dd._acl && !this._allowunsafestore) {
                SecurityWarning("Probably shouldnt be storing private key", dd);
            }
            dd.keypair = dd._master ? dd.keypair.privateexport() : dd.keypair.publicexport();
        }
        let publichash = dd._publichash; // Save before preflight
        dd = super.preflight(dd);  // Edits dd in place
        if (dd._master) { // Only store on Master, on !Master will be None and override storing hash as _publichash
            dd._publichash = publichash;   // May be None, have to do this AFTER the super call as super filters out "_*"  #TODO-REFACTOR_PUBLICHASH
        }
        return dd;
    }

    fetch() {
        console.log("XXX Undefined function CommonList.fetch replace carefully with load");
    }

    async_load(verbose, success, error) {   // Python can also fetch based on just having key
        if (this._needsfetch) { // Only load if need to
            if (verbose) { console.log("CommonList.load:",this._hash)}
            this._needsfetch = false;
            // Need to fetch body and only then fetchlist since for a list the body might include the publickey whose hash is needed for the list
            let self = this;
            transport.async_rawfetch(this, this._hash, verbose,
                                    function(data) {
                                        if (data) {self._setdata(JSON.parse(data))}
                                        if (success) { success(undefined);}
                                        },
                                    error);
        } else {
            if (success) {success(undefined);} // Pass to success as if loaded, and see what action reqd
        }
    }

    async_fetchlist(verbose, success, error) {
        // Load a list, note it does not load the individual items, just the Signatures. To do that, provide a "success" to loop over htem afterwards.
        // Call chain is mb.load > CL.fetchlist > THttp.rawlist > Thttp.load > CL|MB.fetchlist.success > callers.success
        let self = this;
        transport.async_rawlist(this, this._hash, verbose,
            function(lines) {
                //lines = JSON.parse(lines))   Should already by a list
                console.log("CommonList:async_fetchlist.success", self._hash, lines.length);
                self._list = [];
                for (let i in lines) {
                    //TODO verify signature
                    //if CryptoLib.verify(s):
                    //noinspection JSUnfilteredForInLoop
                    let s = new Signature(null, lines[i], verbose);        // Signature ::= {date, hash, privatekey etc }
                    self._list.push(s);
                }
                if (success) {success(undefined);}
            },
            error);
    }
    async_loadandfetchlist(verbose, success, error) {
        // Utility function to simplify nested functions
        let self=this;
        this.async_load(verbose,
            function(msg) { self.async_fetchlist(verbose, success, error) },
            error);
    }
    blocks(verbose) {
        let results = {};   // Dictionary of { SHA... : StructuredBlock(hash=SHA... _signatures:[Signature*] ] ) }
        for (let i in this._list) {
            let s = this._list[i];
            if (! results[s.hash]) {
                results[s.hash] = new StructuredBlock(s.hash, null, verbose);  //TODO Handle cases where its not a SB
            }
            results[s.hash]._signatures.push(s);
        }
        let sbs = [];      // [ StructuredBlock* ]
        for (let k in results) {
            sbs.push(results[k]);      // Array of StructuredBlock
        }
        //TODO sort list
        sbs.sort(StructuredBlock.compare); // Could inline: sbs.sort(function(a, b) { ... }
        return sbs;
    }
    _async_storepublic() { //verbose,success, error
        console.log("Intentionally XXX Undefined function CommonList._async_storepublic - should implement in subclasses");
    }
    async_store(verbose, success, error) {  // Based on python
        if (verbose) { console.log("CL.store", this); }
        if (this._master && ! this._publichash) {
            this._async_storepublic(verbose, success, error); //Stores asynchronously, but hash set immediately
        }
        if ( ! (this._master && this.dontstoremaster)) {
            super.async_store(verbose, success, error);    // Transportable.store(verbose)
        } else {
            if (success) { success(null); }
        }
        return this;
    }

    publicurl() { console.log("XXX Undefined function CommonList.publicurl"); }   // For access via web
    privateurl() { console.log("XXX Undefined function CommonList.privateurl"); }   // For access via web

    async_signandstore(obj, verbose, success, error) {
        /*
        Sign and store a StructuredBlock on a list - via the SB's signatures - see add for doing independent of SB

        :param StructuredBlock obj:
        :param verbose:
        :param options:
        :return:
        */
        let self = this;
        this.async_load(verbose,
            function(msg) {
                console.assert(self._master, "ForbiddenException: Signing a new entry when not a master list");
                // The obj.store stores signatures as well (e.g. see StructuredBlock.store)
                obj.sign(self, verbose).async_store(verbose, success, error);
            },
            error);
        return this; // For chaining
    }
    add() { console.log("XXX Undefined function CommonList.add"); }   // For storing data

}

class MutableBlock extends CommonList {
    // { _hash, _key, _current: StructuredBlock, _list: [ StructuredBlock*]

    constructor(hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose, options) {
        //CL.constructor: hash, data, master, keypair, keygen, mnemonic, verbose
        if (verbose) { console.log("MutableBlock(",hash, data, master, keypair, keygen, mnemonic, verbose, options, ")"); }
        super(hash, data, master, keypair, keygen, mnemonic, verbose, options);
        this.contentacl = contentacl;
        this._current = new StructuredBlock(contenthash, null, verbose);
        this.table = "mb"
    }

    async_elem(el, verbose, successmethodeach, error) {
        if (this._needsfetch) {
            let self = this;
            this.async_load(verbose, function(msg){self.async_elem(el, verbose, successmethodeach, error);}, null);
        } else {
            // this._current should be setup, it might not be loaded, but async_elem can load it
            this._current.async_elem(el, verbose, successmethodeach, error);    // Typically _current will be a SB
        }
    }
    async_fetchlist(verbose, success, error) {  // Check callers of fetchlist and how pass parameters
        // Call chain is mb.load > MB.fetchlist > THttp.rawlist > Thttp.list > MB.fetchlist.success > caller's success
        let self = this;
        super.async_fetchlist(verbose,
            function(unused) {
                // Called after CL.async_fetchlist has unpacked data into Signatures in _list
                let sig = self._list[self._list.length-1];  // Get most recent
                self._current = new StructuredBlock(sig.hash, null, verbose);   // Store in _current
                if (success) { success(undefined);}  // Note success is applied to the MB, not to the content, and the content might not have been loaded.
            },
            error)
    }
    async_updatelist(ul, verbose, successmethodeach, error) {
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
                function(msg) { i.async_elem(li, verbose, successmethodeach, error); },
                error);
        }
    }
    async_update(type, data, verbose, success, error) {  // Send new data for this item to dWeb
        transport.async_update(this, this._hash, type, data, verbose, success, error);
    }
    _async_storepublic(verbose, success, error) {
        // Note that this returns immediately after setting hash, so caller may not need to wait for success
        //(hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose, options)
        let mb = new MutableBlock(null, null, false, this.keypair, false, null, null, null, verbose, {"name": this.name});
        mb.async_store(verbose, success, error);    // Returns immediately but sets _hash first
        return mb._hash;
    }

    contentacl() { console.log("XXX Undefined function MutableBlock.contentacl setter and getter"); }   // Encryption of content
    fetch() { console.log("XXX Undefined function MutableBlock.fetch"); }   // Split into load/onload
    content() {
        console.assert(!this._needsfetch, "Content is asynchronous, must load first");
        return this._current.content();
    }

    file() { console.log("XXX Undefined function MutableBlock.store"); }   // Retrieving data
    async_signandstore(verbose, success, error) {
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
    async_path(patharr, verbose, successmethod, error) {
        if (verbose) { console.log("mb.async_path",patharr,successmethod); }
        //sb.async_path(patharr, verbose, successmethod, error) {
        let curr = this._current;
        curr.async_load(verbose,
            function(msg) { curr.async_path(patharr, verbose, successmethod, error);},
            error);
    }

    static async_new(acl, contentacl, name, _allowunsafestore, content, signandstore, verbose, success, error) {
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
        if (verbose) { console.log("MutableBlock.async_new: Creating MutableBlock", name); }
        // (hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose)
        let mblockm = new MutableBlock(null, null, true, null, true, null, null, contentacl, verbose, {"name": name}); // (name=name  // Create a new block with a new key
        mblockm._acl = acl;              //Secure it
        mblockm._current.data = content;  //Preload with data in _current.data
        mblockm._allowunsafestore = _allowunsafestore;
        if (_allowunsafestore) {
            mblockm.keypair._allowunsafestore = true;
        }
        mblockm.async_store(verbose,
               function(msg) { //success
                    if (signandstore && content) {
                        mblockm.async_signandstore(verbose, null, error); //Sign it - this publishes it
                    }
                    if (verbose) { console.log("Created MutableBlock hash=", mblockm._hash); }
                    if (success) { success(msg); }  // So success here so done even when "if" above is false
               },
               error
            );
        return mblockm  // Returns prior to async_signandstore with hash set
    }

}

class AccessControlList extends CommonList {
    // Obviously ! This class hasnt' been implemented, currently just placeholder for notes etc

    constructor(hash, data, master, keypair, keygen, mnemonic, verbose, options) {
        super(hash, data, master, keypair, keygen, mnemonic, verbose, options);
        this.table = "acl";
    }
    _async_storepublic(verbose, success, error) { // See KeyChain for example
        console.log("XXX Undefined function AccessControlList._async_storepublic");
        //mb = new MutableBlock(keypair=this.keypair, name=this.name)
    }

}

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
    keytype() { return KEYPAIRKEYTYPESIGNANDENCRYPT; }  // Inform keygen

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

// ==== Crypto.py - Encapsulate all the Cryptography =========
class CryptoLib {
    static Curlhash(data) { return "BLAKE2."+ sodium.crypto_generichash(32, data, null, 'urlsafebase64'); }
    static signature(keypair, date, hash) {
        console.log("XXX Undefined function CryptoLib.signature"); //TODO-ASYNC-SIGN
        return "XYZZY TODO-ASYNC-SIGN undefined function signature";
    }
    static verify() { console.log("XXX Undefined function CryptoLib.verify"); }
    static b64dec() { console.log("XXX Undefined function CryptoLib.b64dec"); }
    static b64enc() { console.log("XXX Undefined function CryptoLib.b64enc"); }

    static dumps(obj) { return JSON.stringify(obj); }   // Uses toJSON methods on objects (equivalent of dumps methods on python)

    static decryptdata() { console.log("XXX Undefined function CryptoLib.decryptdata"); }
    static randomkey() { console.log("XXX Undefined function CryptoLib.randomkey"); }
    static sym_encrypt() { console.log("XXX Undefined function CryptoLib.sym_encrypt"); }
    static sym_decrypt() { console.log("XXX Undefined function CryptoLib.sym_decrypt"); }
}

class KeyPair extends SmartDict {
    // This class is (partially) pulled from Crypto.py
    constructor(hash, data, verbose) {
        super(hash, data, verbose);    // SmartDict takes data=json or dict
        this.table = "kp";
    }

    static keygen(keytype, mnemonic, seed, verbose) {
        // keyclass parameter (from Python) not supported as only support Libsodium=NACL keys
        if (verbose) { console.log("Generating keypair"); }
        if (mnemonic) {
            //TODO Mnemonic libraries are either non-BIP39 or have node dependencies - need to rewrite one of them
            if (mnemonic === "coral maze mimic half fat breeze thought champion couple muscle snack heavy gloom orchard tooth alert cram often ask hockey inform broken school cotton") { // 32 byte
                seed = "01234567890123456789012345678901";
                console.log("Faking mnemonic encoding for now")
            } else {
                console.log("MNEMONIC STILL TO BE IMPLEMENTED");    //TODO-mnemonic
            }
        }
        let key = {};
        console.assert(sodium.crypto_box_SEEDBYTES === sodium.crypto_sign_SEEDBYTES, "KeyPair.keygen assuming seed lengths same");
        key.seed = seed || sodium.randombytes_buf(sodium.crypto_box_SEEDBYTES);
        if (keytype === KEYPAIRKEYTYPESIGN || keytype === KEYPAIRKEYTYPESIGNANDENCRYPT) {
            key.sign = sodium.crypto_sign_seed_keypair(key.seed); // Object { publicKey: Uint8Array[32], privateKey: Uint8Array[64], keyType: "ed25519" } <<maybe other keyType
        }
        if (keytype === KEYPAIRKEYTYPEENCRYPT || keytype === KEYPAIRKEYTYPESIGNANDENCRYPT) {
            key.encrypt = sodium.crypto_box_seed_keypair(key.seed); // Object { publicKey: Uint8Array[32], privateKey: Uint8Array[64], keyType: "ed25519" } <<maybe other keyType
        }
        if (verbose) { console.log("key generated:",key); }
        return new KeyPair(null, {"key": key}, verbose);
    }
    __setattr__(name, value) { // Superclass SmartDict to catch "setter"s
        let verbose = false;
        if (name === "key") {
            this.key_setter(value);
        } else if (name === "private") {
            console.log("XXX Undefined function KeyPair.private.setter");
        } else if (name === "public") {
            console.log("XXX Undefined function KeyPair.public.setter");
        } else {
            super.__setattr__(name, value);
        }
    }

    key_setter(value) {
        if (typeof value === "string") {
            this._importkey(value);
        } else {
            this._key = value;
        }
    }
    preflight(dd) {
        if (this._key_has_private(dd._key) && !dd._acl && !this._allowunsafestore) {
            SecurityWarning("Probably shouldnt be storing private key",dd);
        }
        if (dd.key) { //Based on whether the CommonList is master, rather than if the key is (key could be master, and CL not)
            dd.key = this._key_has_private(dd._key) ? this.privateexport : this.publicexport;
        }
        return super.preflight(dd)
    }


    _importkey(value) {
        //First tackle standard formats created by exporting functionality on keys
        // Call route is ... data.setter > ...> key.setter > _importkey

        //TODO - Note fingerprint different from Python - this stores the key, change the Python
        if (typeof value === "object") {    // Should be array, not dict
            for (let i in value) {
                //noinspection JSUnfilteredForInLoop
                this._importkey(value[i]);
            }
        } else {
            let arr = value.split(':',2);
            let tag = arr[0];
            let hash = arr[0];
            let seed = sodium.from_urlsafebase64(hash);
            //See https://github.com/jedisct1/libsodium.js/issues/91 for issues
            if (!this._key) { this._key = {}}   // Only handles NACL style keys
            if (tag === "NACL PUBLIC")           { console.log("XXX _importkey: Cant (yet) import Public key"+value);
            } else if (tag === "NACL PRIVATE")   { console.log("XXX _importkey: Cant (yet) import Private key"+value);
            } else if (tag === "NACL SIGNING")   { console.log("XXX _importkey: Cant (yet) import Signing key"+value);
            } else if (tag === "NACL SEED")      { console.log("XXX _importkey: Cant (yet) import Seed key"+value);
            } else if (tag === "NACL VERIFY")    {
                this._key["sign"] = {"publicKey": sodium.from_urlsafebase64(hash)};
            } else                              { console.log("XXX _importkey: Cant (yet) import "+value); }
        }
    }

    publicexport() {    // TODO probably change this on Python version as well
        let res = [];
        if (this._key.encrypt) { res.push("NACL PUBLIC:"+sodium.to_urlsafebase64(this._key.encrypt.publicKey)) }
        if (this._key.sign) { res.push("NACL VERIFY:"+sodium.to_urlsafebase64(this._key.sign.publicKey)) }
    }

    key() { console.log("XXX Undefined function KeyPair.key"); }
    private() { console.log("XXX Undefined function KeyPair.private"); }    //TODO private is a reserved word in JS
    public() { console.log("XXX Undefined function KeyPair.public"); }  //TODO public is a reserved word in JS
    mnemonic() { console.log("XXX Undefined function KeyPair.mnemonic"); }
    _exportkey() { console.log("XXX Undefined function KeyPair._exportkey"); }
    privateexport() { console.log("XXX Undefined function KeyPair.privateexport"); }

    static _key_has_private(key) {
        if ((key.encrypt && key.encrypt.privateKey) || (key.sign && key.sign.privateKey) || key.seed) { return true; }
        if ((key.encrypt && key.encrypt.publicKey) || (key.sign && key.sign.publicKey)) { return false; }
        console.log("_key_hash_private doesnt recognize",key);
    }

    naclprivate() { return this._key.encrypt.privateKey; }
    naclpublic() { return this._key.encrypt.publicKey; }
    naclpublicexport() { console.log("XXX Undefined function KeyPair.naclpublicexport"); }

    has_private() {
        return KeyPair._key_has_private(this._key)
    }
    encrypt(data, b64, signer) {
        /*
        Encrypt a string, the destination string has to include any information needed by decrypt, e.g. Nonce etc

        :param data:
        :b64 bool:  Trye if want result encoded
        :signer AccessControlList or KeyPair: If want result signed (currently ignored for RSA, reqd for NACL)
        :return: str, binary encryption of data
        */
        // Assumes nacl.public.PrivateKey or nacl.signing.SigningKey
        console.assert(signer, "Until PyNaCl bindings have secretbox we require a signer and have to add authentication");
        //box = nacl.public.Box(signer.keypair.naclprivate, self.naclpublic)
        //return box.encrypt(data, encoder=(nacl.encoding.URLSafeBase64Encoder if b64 else nacl.encoding.RawEncoder))
        const nonce = sodium.randombytes_buf(sodium.crypto_box_NONCEBYTES);
        const ciphertext = sodium.crypto_box_easy(data, nonce, this.naclpublic(), signer.keypair.naclprivate(), "uint8array"); //(message, nonce, publicKey, secretKey, outputFormat)

        const combined = mergeTypedArraysUnsafe(nonce, ciphertext);
        return b64 ? sodium.to_urlsafebase64(nonce) : sodium.to_string(combined);
    }
    decrypt() { console.log("XXX Undefined function KeyPair.decrypt"); }
}
// ==== UI related functions, not dWeb specific =========
//noinspection JSUnusedGlobalSymbols
function togglevisnext(elem) {   // Hide the next sibling object and show the one after, or vica-versa,
    let el1 = elem.nextSibling;
    let el2 = el1.nextSibling;
    if (el1.style.display === "none") {
        el1.style.display = "";
        el2.style.display = "none";
    } else {
        el1.style.display = "none";
        el2.style.display = "";
    }
}

//noinspection JSUnusedGlobalSymbols
function async_objbrowserfetch(el) {
    verbose = false;
    let source = el.source;
    let parent = el.parentNode;
    parent.removeChild(el); //Remove elem from parent
    source.async_load(true, function(msg) { source.objbrowser(source._hash, null, parent, false );}, null);
}

// ==== NON OBJECT ORIENTED FUNCTIONS ==============

function async_dwebfile(table, hash, path, successmethod, error) {
    // Simple utility function to load into a hash without dealing with individual objects
    // successmethod - see "path()" for definition.
    let verbose = true;
    if (path && (path.length > 0)) {
        path = path.split('/');
    }
    if (verbose) { console.log("async_dwebfile",table,hash,path,successmethod);}
    if (table === "mb") {
        //(hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose)
        const mb = new MutableBlock(hash, null, false, null, false, null, null, null, verbose, null);
        // Call chain is mb.load > CL.fetchlist > THttp.rawlist > Thttp.load > MB.fetchlist.success > caller.success
        // for dwebfile:mb, we want to apply the success function to the file - which is in the content after fetchlist
        mb.async_loadandfetchlist(verbose, function(msg) { mb.async_path(path, verbose, successmethod, error);}, error);
        // Note success is applied once after list is fetched, content isn't loaded before that.
    } else if (table === "sb") {
        const sb = new StructuredBlock(hash, null, verbose);
        sb.async_load(verbose, function(msg) {sb.async_path(path, verbose, successmethod, error);}, error);
    } else {
        alert("dwebfile called with invalid table="+table);
    }
}

function async_dwebupdate(hash, type, data, successmethod, error) {
    verbose = false;
    //(hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose)
    let mbm = new MutableBlock(hash, null, true, null, false, null, null, null, verbose, null);
    mbm.async_update( type, data, verbose,
        function(msg){
            if (successmethod) {
                let methodname = successmethod.shift();
                //if (verbose) console.log("async_elem",methodname, successmethod);
                mbm[methodname](...successmethod); // Spreads successmethod into args, like *args in python
            }
        },
        error);
}

function async_dweblist(div, hash, verbose, success, successmethodeach, error) {
    //Retrieve a list, and create <li> elements of div to hold it.
    //success, if present, is run after list retrieved, asynchronous with elements retrieved
    //successeach, is run on each object in the list.
    verbose = false;
    //(hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose)
    const mb = new MutableBlock(hash, null, false, null, false, null, null, null, verbose, null);
    // Call chain is mb.load > CL.fetchlist > THttp.rawlist > Thttp.load > MB.fetchlist.success
    mb.async_loadandfetchlist(verbose,
        function(msg) {
            mb.async_elem(div, verbose, successmethodeach, error); // async_elem loads the block
            if (success) {success(null);}    // Note success will fire async with list elements being loaded
        },
        error);
}
// ======== EXPERIMENTAL ZONA ==================

//TODO BROWSER----
//-data collapsable

