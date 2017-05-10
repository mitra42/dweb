// Javascript library for dweb
// The crypto uses https://github.com/jedisct1/libsodium.js but https://github.com/paixaop/node-sodium may also be suitable if we move to node

//var dwebserver = 'localhost';
const dwebserver = '192.168.1.156';
const dwebport = '4243';
const Dweb = {} // Note const just means it cant be assigned to a new dict, but dict can be modified
Dweb.keychains = [];
// Constants
const KEYPAIRKEYTYPESIGN = 1
const KEYPAIRKEYTYPEENCRYPT = 2
var KEYPAIRKEYTYPESIGNANDENCRYPT = 2    // Currently unsupported

// ==== OBJECT ORIENTED JAVASCRIPT ===============

// These are equivalent of python exceptions, will log and raise alert in most cases - exceptions aren't caught
function SecurityWarning(msg, self) {
    console.log(msg, self);
    alert(msg);
}

// Utility functions

function mergeTypedArraysUnsafe(a, b) { // Take care of inability to concatenate typed arrays
    //http://stackoverflow.com/questions/14071463/how-can-i-merge-typedarrays-in-javascript also has a safe version
    var c = new a.constructor(a.length + b.length);
    c.set(a);
    c.set(b, a.length);
    return c;
}
//TODO document from here down


class TransportHttp {

    constructor(ipandport, options) {
        this.ipandport = ipandport;
        this.options = options; // Dictionary of options, currently unused
        this.baseurl = "http://" + ipandport[0] + ":" + ipandport[1] + "/";
    }

    static setup(ipandport, options) {
        return new TransportHttp(ipandport, options);
    }
    post(self, command, hash, type, data, verbose, options) {
        // obj being loaded
        // options: are passed to class specific onloaded
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
                if (verbose) { console.log("TransportHTTP:", command, ": returning data len=", msg.length); }
                // Dont appear to need to parse JSON data, its decoded already
                self.onposted(hash, msg, verbose, options);
            },
            error: function(xhr, status, error) {
                console.log("TransportHTTP:", command, "error", status, "error=",error);
                alert("TODO post "+command+" failure status="+status+" error="+error);
            },
        });
    }

    update(self, hash, type, data, verbose, options) {
        this.post(self, "update", hash, type, data, verbose, options);
    }

    load(self, command, hash, path, listreturned, verbose, options) {
        // self is the obj being loaded (yes this is intentional ! its not Javascript's "this")
        // options: are passed to class specific onloaded
        // Locate and return a block, based on its multihash
        if (verbose) { console.log("TransportHTTP load:",command, ":hash=", hash, "options=", options); }
        let url = this.url(command, hash);
        if (verbose) { console.log("TransportHTTP:list: url=",url); }
        $.ajax({
            type: "GET",
            url: url,
            success: function(data) {
                if (verbose) { console.log("TransportHTTP:", command, ": returning data len=", data.length); }
                // Dont appear to need to parse JSON data, its decoded already
                if (listreturned) {
                    // Call chain is mb.load > onloaded > CL.fetchlist > THttp.rawlist > Thttp.load > CL|MB.onlisted > options
                    self.onlisted(hash, data, verbose, options);
                } else {
                    self.onloaded(hash, data, verbose, options);
                }
            },
            error: function(xhr, status, error) {
                console.log("TransportHTTP:", command, ": error", status, "error=",error);
                alert("TODO Block failure status="+status+" "+command+" error="+error);
            },
        });
    }

    rawfetch(self, hash, verbose, options) {    //TODO merge with transport.list
        // Locate and return a block, based on its multihash
        // options: are passed to class specific onloaded
        // Locate and return a block, based on its multihash
        this.load(self, "rawfetch", hash, [], false, verbose, options);    //TODO-PATH
    }

    rawlist(self, hash, verbose, options) {
        // obj being loaded
        // options: are passed to class specific onloaded
        // Locate and return a block, based on its multihash
        // Call chain is mb.load > onloaded > CL.fetchlist > THttp.rawlist > Thttp.load > CL|MB.onlisted > options
        this.load(self, "rawlist", hash, [], true, verbose, options); //TODO-PATH
    }

    rawstore(self, data, verbose, options) {
        //PY: res = self._sendGetPost(True, "rawstore", headers={"Content-Type": "application/octet-stream"}, urlargs=[], data=data, verbose=verbose)
        this.post(self, "rawstore", null, null, data, verbose, options) // Returns immediately
    }

    rawreverse() { console.log("Undefined function TransportHTTP.rawreverse"); }
    rawadd() { console.log("Undefined function TransportHTTP.rawstore"); }


    url(command, hash) {
        var url = this.baseurl + command;
        if (hash) {
            url += "/" + hash;
        }
        return url;
    }
}

var transport = TransportHttp.setup([dwebserver, dwebport], {});

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

    store(verbose, options) {    // Python has a "data" parameter to override this._data but probably not needed
        if (verbose) { console.log("Transportable.store",this, options);}
        let data = this._getdata();
        if (verbose) { console.log("Transportable.store data=",data);}
        this._hash = CryptoLib.Curlhash(data); //store the hash since the HTTP is async, "onposted" should check the hash returned
        options.checkhash = true;   // Make sure check hash in store
        transport.rawstore(this, data, verbose, options);  // Returns immediately BEFORE storing
        if (verbose) { console.log("Transportable.store hash=", this._hash); }
        return this;
    }

    dirty() {   // Flag as dirty so needs uploading - subclasses may delete other, now invalid, info like signatures
        this._hash = null;
    }

    fetch() { console.log("Undefined function Transportable.fetch"); } // Replaced by load

    load(verbose, options) {    // Asynchronous equiv of fetch, has to specify what to do via options
        if (verbose) { console.log("Transportable.load hash=",this._hash,"options=",options); }
        if (this._needsfetch) { // Only load if need to
            transport.rawfetch(this, this._hash, verbose, options);
            this._needsfetch = false
        }
        // Block fetched in the background - dont assume loaded here, see onloaded
    }

    file() { console.log("Undefined function Transportable.file"); }
    url() { console.log("Undefined function Transportable.url"); }

    // ==== UI method =====

    elem(data, hash, path, verbose, el) {
        // Called from storeto based on options
        if (typeof el === 'string') {
            el = document.getElementById(el);
        }
        if (typeof data === 'string') {
            if (verbose) { console.log("onloaded:Storing data to element",el,encodeURI(data.substring(0,20))); }
            el.innerHTML = data;
        } else if (Array.isArray(data)) {
            if (verbose) { console.log("onloaded:Storing list of len",data.length,"to element",el);}
            this.updatelist(el, verbose);   //TODO-STORETO using updatelist not replacing
        } else {
            console.log("ERROR: unknown type of data to elem",typeof data, data);
        }
    }

    checkhash(data, hash, path, verbose, options) { // Called by storeto
            if (data != this._hash) {
                console.log("ERROR Hash returned ",data,"doesnt match hash expected",this._hash);
            }
            delete options.checkhash;
    }

    storeto(data, hash, path, verbose, options) {
        // Can be called to check if options have instructions what to do with data
        // Its perfectly legitimate to call this, and nothing gets done with the data
        if (verbose) { console.log("storeto: options=", options); }
        for (let k in options) {
            if (["path"].includes(k)) {   //TODO-STORETO implement these as functions instead of hardcoded in onloaded or onlisted
                console.log("ERROR-TODO - option",k,"not implemented on",this.constructor.name);
                //alert("UNIMPLEMENTED "+this.constructor.name+"."+k);
                //1/0;
            } else {
                // Calls elem, objbrowser and soon fetchblocks - all with standard interface
                this[k](data, hash, path, verbose, options[k]);
            }
        }
    }
}

class SmartDict extends Transportable {
    constructor(hash, data, verbose, options) {
        // data = json string or dict
        super(hash, data); // _hash is _hash of SB, not of data - will call _setdata (which usually set fields), -note does not fetch the has, but sets _needsfetch
        this._setproperties(options);   // Note this will override any properties set with data
    }
    __setattr__(name, value) { // Call chain is ... onloaded or constructor > _setdata > _setproperties > __setattr__
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
            for (var prop in dict) {
                this.__setattr__(prop, dict[prop]);
            }
        }
    }
    preflight(dd) { // Called on outgoing dictionary of outgoing data prior to sending - note order of subclassing can be significant
        let res = {};
        for (var i in dd) {
            if (i.indexOf('_') !== 0) { // Ignore any attributes starting _
                if (dd[i] instanceof Transportable) {
                    res[i] = dd[i].store(false, null)._hash  // store(verbose, options) - this will set hash, then store obj in background
                } else {
                    res[i] = dd[i];
                }
            }
        }
        // Note table is a object attribute in JS, so copied above (in Python its a class attribute that needs copying
        return res
    }

    _getdata() {
        let dd = {}
        for (var i in this) {
            dd[i] = this[i];    // This *should* copy just the attributes, need to check dosnt copy functions (it might)
        }
        let res = CryptoLib.dumps(this.preflight(dd));
        if (this._acl) { //Need to encrypt
            let encdata = this._acl.encrypt(res, true)  // data, b64
            let dic = { "encrypted": encdata, "acl": this._acl._publichash, "table": this.table}
            res = CryptoLib.dumps(dic);
        }
        return res
    }    // Should be being called on outgoing _data includes dumps and encoding etc

    _setdata(value) {
        // Note SmartDict expects value to be a dictionary, which should be the case since the HTTP requester interprets as JSON
        // Call chain is ... onloaded or constructor > _setdata > _setproperties > __setattr__
        if (value) {    // Skip if no data
            if (typeof value === 'string') {    // Assume it must be JSON
                value = JSON.parse(value);
            }
            // value should be a dict by now, not still json as it is in Python
            //TODO-AUTHENTICTION - decrypt here
            this._setproperties(value); // Note value should not contain a "_data" field, so wont recurse even if catch "_data" at __setattr__()
        }
    }

    objbrowser(data, hash, path, verbose, ul) {
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
        sp1.className = "classname" // Confusing!, sets the className of the span to "classname" as it holds a className
        sp1.appendChild(t1);
        li.appendChild(sp1);

        //Loop over dict fields
        let ul2 = document.createElement("ul");
        ul2.className="props";
        li.appendChild(ul2);
        for (let prop in this) {
            if (this[prop]) {
                let text = this[prop].toString();
                if (text !== "" && prop !== "_hash") {    // Skip empty values; _hash (as shown above);
                    let li2 = document.createElement("li");
                    li2.className='prop';
                    ul2.appendChild(li2);
                    //li2.innerHTML = "Field1"+prop;
                    let fieldname = document.createTextNode(prop)
                    let spanname = document.createElement('span');
                    spanname.appendChild(fieldname);
                    spanname.className='propname';
                    //TODO - handle Links by nested list
                    li2.appendChild(spanname);
                    //if ((prop == "links") || (prop == "_list")) {  //StructuredBlock
                    if ( ["links", "_list", "_signatures", "_current"].includes(prop) ) { //<span>...</span><ul proplinks>**</ul>
                        spanval = document.createElement('span');
                        spanval.appendChild(document.createTextNode("..."))
                        li2.appendChild(spanval);
                        let ul3 = document.createElement("ul");
                        ul3.className = "proplinks";
                        ul3.style.display = 'none';
                        spanname.setAttribute('onclick',"togglevisnext(this);");
                        //spanname.setAttribute('onclick',"console.log(this.nextSibling)");

                        li2.appendChild(ul3);
                        //TODO make this a loop
                        if (Array.isArray(this[prop])) {
                            for (let l1 in this[prop]) {
                                this[prop][l1].objbrowser(null, hash, (path ? path + "/":"")+this[prop][l1].name , verbose, ul3);
                            }
                        } else {
                            if (this[prop]._hash) {
                                this[prop].objbrowser(null, this[prop]._hash, null, verbose, ul3)
                            } else {
                                this[prop].objbrowser(null, hash, path, verbose, ul3);
                            }
                        }
                    } else {    // Any other field
                        if (prop === "hash") {
                            var spanval = document.createElement('a');
                            spanval.setAttribute('href','/file/b/'+this[prop]+"?contenttype="+this["Content-type"]);
                        } else {
                            // Group of fields where display then add behavior or something
                            var spanval = document.createElement('span');
                            if (prop === "_needsfetch") {
                                li2.setAttribute('onclick','dofetch(this.parentNode.parentNode);');
                            }
                        }
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

    onloaded(hash, data, verbose, options) {
        // Called after block succeeds, can pass options through
        // copies at Block, MutableBlock
        if (verbose) { console.log("Block:onloaded",options); }
        this._data = data;
        this.storeto(data, hash, null, verbose, options) // TODO storeto handle img, or other non-HTML as reqd
    }

    size() { console.log("Undefined function Block.size"); }
    content() { console.log("Undefined function Block.content"); }

}

// ######### Parallel development to StructuredBlock.py ########

class StructuredBlock extends SmartDict {
    constructor(hash, data, verbose) {
        super(hash, data, verbose); // _hash is _hash of SB, not of data
        this._signatures = new Array()
        this._date = null;  // Updated in _earliestdate when loaded
        this.table = "sb";  // Note this is cls.table on python but need to separate from dictionary
    }
    store(verbose, options) { console.log("Undefined function StructuredBlock.store"); }

    __setattr__(name, value) {
        // Call chain is ... onloaded or constructor > _setdata > _setproperties > __setattr__
        // catch equivalent of getters and setters here
        let verbose = false;
        if (name === "links") {  // Assume its a SB TODO make dependent on which table
            let links = value;
            for (let len = links.length, i=0; i<len; i++) {
                let sb = new StructuredBlock(null, links[i], verbose);
                links[i] = sb;
            }
            this[name] = links;
        } else {
            super.__setattr__(name, value);
        }
    }

    onloaded(hash, data, verbose, options) {  // Equivalent of _setdata in Python
        console.log("StructuredBlock:onloaded data len=", data.length, options)
        this._setdata(JSON.parse(data))   // Actually calls super, and calls _setproperties()
        //this._data = data;

        let sb = this;
        let pathstr = options.path && options.path.join('/');
        if (verbose && options.path) { console.log("sb.onloaded walking path",pathstr);}
        while (options.path && options.path.length && this.links.length ) { // Have a path and can do it on sb
            let next = options["path"].shift(); // Takes first element of path, leaves path as rest
            console.log("StructuredBlock:onloaded next path=",next);
            sb = sb.link(next);   //TODO handle error of not found
        }
        // At this point sb points as far down the path as we could go without loading.
        if (options.path && options.path.length) {  // We still have path to explore, but no links on loaded sb
                sb.load(verbose, options);  // passes shorter path and any dom arg load and to its onloaded
        } else {  // Walked to end of path, can handle
                console.log("StructuredBlock.onloaded storing len=",sb.data && sb.data.length);
                this.storeto(sb.data, hash, pathstr, verbose, options);  // See if options say to store in a DIV for example
        }
    }

    dirty() {
        super.dirty();
        this._signatures = Signatures([]);
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

    content() { console.log("Undefined function StructuredBlock.content"); }
    file() { console.log("Undefined function StructuredBlock.file"); }
    size() { console.log("Undefined function StructuredBlock.size"); }
    path() { console.log("Undefined function StructuredBlock.path"); }   // Done in onloaded, asynchronous recursion.
    sign() { console.log("Undefined function StructuredBlock.sign"); }
    verify() { console.log("Undefined function StructuredBlock.verify"); }


    earliestdate() {    // Set the _date field to the earliest date of any signature or null if not found
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
        this.table = "sig"
    }
    //TODO need to be able to verify signatures
    sign() { console.log("Undefined function Signature.sign"); }
    verify() { console.log("Undefined function Signature.verify"); }
}

// ######### Parallel development to MutableBlock.py ########

class CommonList extends SmartDict {
    constructor(hash, data, master, keypair, keygen, mnemonic, verbose, options) {
        // data = json string, or dict
        //TODO implmenent mnemonic, keypair, keygen
        //console.log("CL(", data, master, options,")");
        super(hash, data, verbose, options);
        this._list = new Array();   // Array of signatures
        if (keygen || mnemonic) {
            this.keypair = KeyPair.keygen(this.keytype(), mnemonic, null, verbose);
        } else {
            this._setkeypair(keypair, verbose);
        }
        this._master = master;  // Note this must be AFTER _setkeypair since that sets based on keypair found and _storepublic for example wants to force !master
        if (!this._master) { this._publichash = hash; }
    }
    keytype() { return KEYPAIRKEYTYPESIGN; }

    __setattr__(name, value) {
        // Call chain is ... onloaded or constructor > _setdata > _setproperties > __setattr__
        // catch equivalent of getters and setters here
        let verbose = false;
        if (name === "keypair") {
            this._setkeypair(value, verbose);
        } else {
            super.__setattr__(name, value);
        }
    }

    _setkeypair(value, verbose) {
        // Call chain is ... onloaded or constructor > _setdata > _setproperties > __setattr__ > _setkeypair
        if (value && ! (value instanceof KeyPair)) {
            value = KeyPair(value, null, verbose);
        }
        this.keypair = value;
        this._master = value && value.has_private() //TODO-STORE Note there may be a race condition here if KeyPair is loading asynchronously
    }

    preflight(dd) {
        if (dd.keypair) {
            if (dd.master && !dd._acl && !this._allowunsafestore) {
                SecurityWarning("Probably shouldnt be storing private key", dd);
            }
            dd.keypair = dd.master ? dd.keypair.privateexport() : dd.keypair.publicexport();
        }
        let publichash = dd._publichash // Save before preflight
        dd = super.preflight(dd)  // Edits dd in place
        if (dd.master) { // Only store on Master, on !Master will be None and override storing hash as _publichash
            dd._publichash = publichash   // May be None, have to do this AFTER the super call as super filters out "_*"  #TODO-REFACTOR_PUBLICHASH
        }
        return dd
    }

    fetch(fetchbody, fetchlist, fetchblocks, verbose, options) {
        console.log("Undefined function CommonList.fetch replace carefully with load");
    }   // Split into load and onloaded

    load(verbose,  options) {   // Python can also fetch based on just having key
        if (this._needsfetch) { // Only load if need to
            if (verbose) { console.log("CommonList.load:",this._hash,options)}
            this._needsfetch = false
            // Need to fetch body and only then fetchlist since for a list the body might include the publickey whose hash is needed for the list
            transport.rawfetch(this, this._hash, verbose, options);  // TODO this is only correct if its NOT master
        } else {
            this.onloaded(this._hash, null, verbose, options);    // Pass to onloaded as if loaded, and see what action reqd
        }
    }

    fetchlist(data, hash, path, verbose, options) {  // Interface chosen so callable from storeto if in options
        // Call chain is mb.load > onloaded > CL.fetchlist > THttp.rawlist > Thttp.load > CL|MB.onlisted > options
        transport.rawlist(this, this._hash, verbose, options);  // TODO this is only correct if its NOT master
    }

    onloaded(hash, data, verbose, options) { // Body loaded
        console.log("CommonList:onloaded data len=", data ? data.length : "null", options)
        if (data) {
            this._setdata(JSON.parse(data))   //  // Call chain is ... onloaded or constructor > _setdata > _setproperties > __setattr__
            this.storeto(data, hash, null, verbose, options);
        } else {
            this.storeto(null, hash, null, verbose, options);   //TODO This data may need to be the contents?
        }
    }

    onlisted(hash, lines, verbose, options) { // Body loaded
        // Call chain is mb.load > onloaded > CL.fetchlist > THttp.rawlist > Thttp.load > CL|MB.onlisted > options
        console.log("CommonList:onlisted", hash, lines.length, options)
        //lines = JSON.parse(lines))   Should already by a list
        this._list = []
        for (let i in lines) {
            //TODO verify signature
            //if CryptoLib.verify(s):
            let s = new Signature(null, lines[i], verbose);        // Signature ::= {date, hash, privatekey etc }
            this._list.push(s)
        }
        if (options.fetchblocks) {
            options.fetchblocks = false; // Done it here, dont do it again
            console.log("CommonList.onlisted options=fetchblocks not implemented")
        }
        return true; // This layer handled, can do superclass stuff rather than wait for deeper loads
    }
    onposted(hash, data, verbose, options) {
        // onposted isn't used much. Currently returns the hash of data stored, but might be better as a struc
        this.storeto(data, hash, null, verbose, options) // TODO storeto handle img, or other non-HTML as reqd
    }

    blocks(fetchblocks, verbose) {
        let results = {};   // Dictionary of { SHA... : StructuredBlock(hash=SHA... _signatures:[Signature*] ] ) }
        for (let i in this._list) {
            let s = this._list[i];
            if (! results[s.hash]) {
                results[s.hash] = new StructuredBlock(s.hash, null, verbose);  //TODO Handle cases where its not a SB
            }
            results[s.hash]._signatures.push(s);
        }
        let sbs = new Array();      // [ StructuredBlock* ]
        for (let k in results) {
            sbs.push(results[k]);      // Array of StructuredBlock
        }
        //TODO sort list
        sbs.sort(StructuredBlock.compare); // Could inline: sbs.sort(function(a, b) { ... }
        return sbs;
    }
    _storepublic(verbose, options) {
        console.log("Intentionally undefined function CommonList._storepublic - should implement in subclasses");
    }
    store(verbose, options) {  // Based on python
        options = options || {};
        if (verbose) { console.log("CL.store", this, "options=", options); }
        if (this._master && ! this._publichash) {
            this._storepublic(verbose, );
        }
        if ( ! (this._master && options.dontstoremaster)) {
            delete options.dontstoremaster;
            super.store(verbose, options);    // Transportable.store(verbose, options)
        }
        return this;
    }

    publicurl() { console.log("Undefined function CommonList.publicurl"); }   // For access via web
    privateurl() { console.log("Undefined function CommonList.privateurl"); }   // For access via web
    signandstore() { console.log("Undefined function CommonList.signandstore"); }   // For storing data
    add() { console.log("Undefined function CommonList.add"); }   // For storing data

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

    onlisted(hash, lines, verbose, options) {
        // Call chain is mb.load > onloaded > CL.fetchlist > THttp.rawlist > Thttp.load > CL|MB.onlisted > options
        let handled = super.onlisted(hash, lines, verbose, options);
        if (handled) {  // Should always be handled until fetchblocks implemented
            let sig = this._list[this._list.length-1];
            this._current = new StructuredBlock(sig.hash, null, verbose);
            if (options.path && options.path.length) {  //TODO-PATH unclear if want a path or a list - start with a list
                this._current.load(verbose, options);
            } else { // elem, objbrowser etc are done on the leaf, not the intermediaries
                this.storeto(lines, hash, null, verbose, options);
            }
        }
    }
    updatelist(ul, verbose) {
        while (ul.hasChildNodes()) {
            ul.removeChild(ul.lastChild);
        }
        let blocks = this.blocks(false, verbose);
        for (let ii in blocks) {     // Signed Blocks
            let i = blocks[ii];
            let li = document.createElement("li");
            ul.appendChild(li);
            i.load(verbose, { "elem": li });
        }
    }
    update(type, data, verbose, options) {  // Send new data for this item to dWeb
        transport.update(this, this._hash, type, data, verbose, options);
    }
    _storepublic(verbose, options) {
        // options are fields of MB, not things to do after store()
        //(hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose, options)
        let opt2 = options || {}
        opt2.name = this.name;
        let mb = new MutableBlock(null, null, false, this.keypair, false, null, null, null, verbose, opt2);
        mb.store(verbose, null);    // Returns immediately but sets _hash first
        return mb._hash;
    }

    contentacl() { console.log("Undefined function MutableBlock.contentacl setter and getter"); }   // Encryption of content
    fetch() { console.log("Undefined function MutableBlock.fetch"); }   // Split into load/onload/onlisted
    content() { console.log("Undefined function MutableBlock.store"); }   // Retrieving data
    file() { console.log("Undefined function MutableBlock.store"); }   // Retrieving data
    signandstore(verbose, options) { console.log("Undefined function MutableBlock.signandstore"); }   // Retrieving data    //TODO-STORE need this
    path() { console.log("Undefined function MutableBlock.path"); }   // Built into onloaded

    static new(acl, contentacl, name, _allowunsafestore, content, signandstore, verbose, options) {
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
        if (verbose) { console.log("MutableBlock.new: Creating MutableBlock", name); }
        // (hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose)
        let opt2 = options || {};
        opt2.name = name;
        let mblockm = new MutableBlock(null, null, true, null, true, null, null, contentacl, verbose, opt2); // (name=name  // Create a new block with a new key
        mblockm._acl = acl;              //Secure it
        mblockm._current.data = content;  //Preload with data in _current.data
        mblockm._allowunsafestore = _allowunsafestore;
        if (_allowunsafestore) {
            mblockm.keypair._allowunsafestore = true;
        }
        mblockm.store(verbose, options);
        if (signandstore && content) {
            mblockm.signandstore(verbose, options); //Sign it - this publishes it
        }
        if (verbose) { console.log("Created MutableBlock hash=", mblockm._hash); }
        return mblockm
    }

}

class AccessControlList extends CommonList {
    // Obviously ! This class hasnt' been implemented, currently just placeholder for notes etc
    constructor() {
        this.table = "acl";
    }
    _storepublic(verbose, options) { // See KeyChain for example
        console.log("Undefined function AccessControlList._storepublic");
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
    static new(mnemonic, keygen, name, verbose) {
        let kc = new KeyChain(null, { "name": name }, false, null, keygen, mnemonic, verbose);
        kc.store(verbose, {});    // Verbose, options
        KeyChain.addkeychains(kc);
        kc.load(verbose, {"fetchlist": {} });    //Was fetching blocks, but now done by "keys"
        //if verbose: print "Created keychain for:", kc.keypair.private.mnemonic
        //if verbose and not mnemonic: print "Record these words if you want to access again"
        return kc
    }
    keytype() { return KEYPAIRKEYTYPESIGNANDENCRYPT; }  // Inform keygen

    keys() { console.log("Undefined property KeyChain.keys"); }
    add() { console.log("Undefined function KeyChain.add"); }

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
    decrypt() { console.log("Undefined function KeyChain.decrypt"); }
    accesskey() { console.log("Undefined property KeyChain.accesskey"); }

    static addkeychains(keychains) {
        //Add keys I can view under to ACL
        //param keychains:   Array of keychains
        if (typeof keychains === "Array") {
            Dweb.keychains = Dweb.keychains + keychains;
        } else {
            Dweb.keychains.push(keychains);
        }
    }

    find() { console.log("Undefined function KeyChain.find"); }

    _storepublic(verbose, options) { // Based on python CL._storepublic, but done in each class in JS
        console.log("KeyChain._storepublic");
        let kc = new KeyChain(null, {"name": this.name}, false, this.keypair, false, null, verbose);
        this._publichash = kc.store(verbose, options)._hash;  //returns immediately with precalculated hash
    }

    store(verbose, options) {
        // CommonList.store(verbose, options)
        options.dontstoremaster = true;
        return super.store(verbose, options)  // Stores public version and sets _publichash - never returns
    }
    fetch() { console.log("Intentionally undefined function MutableBlock.fetch use load/onloaded/onlisted"); }   // Split into load/onload/onlisted

    _findbyclass() { console.log("Undefined function KeyChain._findbyclass"); }
    myviewerkeys() { console.log("Undefined function KeyChain.myviewerkeys"); }
    mymutableBlocks() { console.log("Undefined function KeyChain.mymutableBlocks"); }

}

// ==== Crypto.py - Encapsulate all the Cryptography =========
class CryptoLib {
    static Curlhash(data) { return "BLAKE2."+ sodium.crypto_generichash(32, data, null, 'urlsafebase64'); }
    static dumps(obj) { return JSON.stringify(obj); }   // Uses toJSON methods on objects (equivalent of dumps methods on python)
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
            if (mnemonic == "coral maze mimic half fat breeze thought champion couple muscle snack heavy gloom orchard tooth alert cram often ask hockey inform broken school cotton") { // 32 byte
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
            console.log("Undefined function KeyPair.private.setter");
        } else if (name === "public") {
            console.log("Undefined function KeyPair.public.setter");
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
        if (dd_key) { //Based on whether the CommonList is master, rather than if the key is (key could be master, and CL not)
            dd.key = this._key_has_private(dd._key) ? self.privateexport : self.publicexport;
        }
        return super.preflight(dd)
    }


    _importkey(value) {
        //First tackle standard formats created by exporting functionality on keys
        //TODO - Note fingerprint different from Python - this stores the key, change the Python
        if (typeof value === "Array") {
            for (let i in value) {
                this._importkey(value);
            }
        } else {
            let arr = value.split(':',2)
            let tag = arr[0];
            let hash = arr[0];
            let seed = sodium.from_urlsafebase64(hash);
            //See https://github.com/jedisct1/libsodium.js/issues/91 for issues

            if (tag == "NACL PUBLIC")           { alert("Cant (yet) import Public key"+value);
            } else if (tag == "NACL PRIVATE")   { alert("Cant (yet) import Private key"+value);
            } else if (tag == "NACL SIGNING")   { alert("Cant (yet) import Signing key"+value);
            } else if (tag == "NACL VERIFY")    { alert("Cant (yet) import Verify key"+value);
            } else if (tag == "NACL SEED")      { alert("Cant (yet) import Seed key"+value);
            } else                              { alert("Cant (yet) import "+value); }
        }
    }

    publicexport() {    // TODO probably change this on Python version as well
        let res = [];
        if (this._key.encrypt) { res.push("NACL PUBLIC:"+sodium.to_urlsafebase64(this._key.encrypt.publicKey)) }
        if (this._key.sign) { res.push("NACL VERIFY:"+sodium.to_urlsafebase64(this._key.sign.publicKey)) }
    }

    key() { console.log("Undefined function KeyPair.key"); }
    private() { console.log("Undefined function KeyPair.private"); }
    public() { console.log("Undefined function KeyPair.public"); }
    mnemonic() { console.log("Undefined function KeyPair.mnemonic"); }
    _exportkey() { console.log("Undefined function KeyPair._exportkey"); }
    privateexport() { console.log("Undefined function KeyPair.privateexport"); }

    static _key_has_private(key) {
        if ((key.encrypt && key.encrypt.privateKey) || (key.sign && key.sign.privateKey) || key.seed) { return true; }
        if ((key.encrypt && key.encrypt.publicKey) || (key.sign && key.sign.publicKey)) { return false; }
        console.log("_key_hash_private doesnt recognize",key);
    }

    naclprivate() { return this._key.encrypt.privateKey; }
    naclpublic() { return this._key.encrypt.publicKey; }
    naclpublicexport() { console.log("Undefined function KeyPair.naclpublicexport"); }

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
        console.log("XXX@948",nonce);
        console.log("XXX@950",ciphertext);
        console.log("XXX@950",combined);
        return b64 ? sodium.to_urlsafebase64(nonce) : sodium.to_string(combined);
    }
    decrypt() { console.log("Undefined function KeyPair.decrypt"); }
}
// ==== UI related functions, not dWeb specific =========
function togglevisnext(elem) {   // Hide the next sibling object and show the one after, or vica-versa,
    el1 = elem.nextSibling;
    el2 = el1.nextSibling;
    if (el1.style.display === "none") {
        el1.style.display = "";
        el2.style.display = "none";
    } else {
        el1.style.display = "none";
        el2.style.display = "";
    }
}

function dofetch(el) {
    source = el.source;
    parent = el.parentNode;
    parent.removeChild(el); //Remove elem from parent
    source.load(true, {"objbrowser": parent});
}

// ==== NON OBJECT ORIENTED FUNCTIONS ==============

function dwebfile(table, hash, path, options) {
    // Simple utility function to load into a hash without dealing with individual objects
    // options are what to do with data, not fields for MB
    let verbose = false;
    if (path && (path.length > 0)) {
        options.path = path.split('/');
    }
    if (table === "mb") {
        //(hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose, options)
        var mb = new MutableBlock(hash, null, false, null, false, null, null, null, verbose, null);
        // Call chain is mb.load > onloaded > CL.fetchlist > THttp.rawlist > Thttp.load > CL|MB.onlisted > options
        mb.load(true, { "fetchlist": options}); // for dwebfile, we want to apply the optiosn to the file - which is in the content after fetchlist
    } else if (table === "sb") {
        var sb = new StructuredBlock(hash, null, verbose);
        sb.load(true, options);
    } else {
        alert("dwebfile called with invalid table="+table);
    }
}

function dwebupdate(hash, type, data, options) {
    // Options refer to what to do with data, not fields on mb
    verbose = false;
    //(hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose, options)
    mbm = new MutableBlock(hash, null, true, null, false, null, null, null, verbose, null);
    mbm.update(type, data, true, options);  //TODO failing as result is HTML but treated as Javascript - can intercept post
}

function dweblist(div, hash) {
    //(hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose)
    var mb = new MutableBlock(hash, null, false, null, false, null, null, null, verbose, null);
    options = {}
    options.fetchlist = {"elem": div };
    // Call chain is mb.load > onloaded > CL.fetchlist > THttp.rawlist > Thttp.load > CL|MB.onlisted > options
    mb.load(true, options);
}
// ======== EXPERIMENTAL ZONA ==================

//TODO BROWSER----
//-data collapsable