// Javascript library for dweb

//var dwebserver = 'localhost';
var dwebserver = '192.168.1.156';
var dwebport = '4243';

// ==== OBJECT ORIENTED JAVASCRIPT ===============


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
        let url = this.url(command, hash)  + "/" + type;
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
        // obj being loaded
        // optioms: are passed to class specific onloaded
        // Locate and return a block, based on its multihash
        verbose=true;
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
                    self.onlisted(hash, data, verbose, options);
                } else {
                    self.onloaded(hash, data, verbose, options);
                }
            },
            error: function(xhr, status, error) {
                console.log("TransportHTTP:", command, ": error", status, "error=",error);
                alert("TODO Block failure status="+status+" error="+error);
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
        this.load(self, "rawlist", hash, [], true, verbose, options); //TODO-PATH
    }

    url(command, hash) {
        var url = this.baseurl + command + "/" + hash;
        return url;
    }
}

var transport = TransportHttp.setup([dwebserver, dwebport], {});


// ######### Parallel development to CommonBlock.py ########

class Transportable {
    // Based on Transportable class in python - generic base for anything transportable.

    constructor(hash, data) {
        this._hash = hash;  // Hash of the _data
        this._setdata(data); // The data being stored
        if (hash && !data) { this._needsfetch = true; }
    }

    _setdata(value) {
        this._data = value;  // Default behavior, assumes opaque bytes, and not a dict
    }
    //UNDEFINED FUNCTIONS in PYTHON: store, dirty, fetch, file, url
    store() { alert("Undefined function Transportable.store"); }

    dirty() {   // Flag as dirty so needs uploading - subclasses may delete other, now invalid, info like signatures
        this._hash = null;
    }

    fetch() { alert("Undefined function Transportable.fetch"); } // Replaced by load

    load(verbose, options) {    // Asynchronous equic of fetch, has to specify what to do via options
        if (verbose) { console.log("Transportable.load hash=",this._hash,"options=",options); }
        if (this._needsfetch) { // Only load if need to
            transport.rawfetch(this, this._hash, verbose, options);
            this._needsfetch = false
        }
        // Block fetched in the background - dont assume loaded here, see onloaded
    }

    file() { alert("Undefined function Transportable.file"); }
    url() { alert("Undefined function Transportable.url"); }

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
            console.log("XXX142",typeof data, data);

        }
    }

    storeto(data, hash, path, verbose, options) {
        // Can be called to check if options have instructions what to do with data
        // Its perfectly legitimate to call this, and nothing gets done with the data
        if (verbose) { console.log("storeto: options=", options); }
        for (let k in options) {
            console.log("XXX156",k,typeof this[k],options[k]);
            if (["fetchbody", "fetchlist", "path"].includes(k)) {   //TODO-STORETO implement these as functions instead of hardcoded in onloaded or onlisted
                console.log("XXX-TODO - option",k,"not implemented on",this.constructor.name);
            } else {
                // Calls elem, objbrowser and soon fetchlist fetchbody fetchblocks - all with standard interface
                this[k](data, hash, path, verbose, options[k]);
            }
        }
    }
}

class SmartDict extends Transportable {
    constructor(hash, data) {
        super(hash, data); // _hash is _hash of SB, not of data
        // Note this does not set fields (with _setproperties) unlike Python version which sets it in _data.setter
    }
    __setattr__(name, value) {
        //TODO Need a javascript equivalent way of transforming date
        // if (name[0] != "_") {
        //    if "date" in name and isinstance(value,basestring):
        //        value = dateutil.parser.parse(value)
        //}
        return this[name] = value; //TODO: Python-Javascript: In Python can assume will get methods of property e.g. _data, in javascript need to be explicit here, or in caller.
    }
    _setproperties(dict) { // < _setdata < constructor or onloaded
        for (let prop in dict) {
            this.__setattr__(prop, dict[prop]);
        }
    }
    preflight() { alert("Undefined function SmartDict.preflight"); }    // Should be being called on outgoing _data
    _getdata() { alert("Undefined function SmartDict._getdata"); }    // Should be being called on outgoing _data includes dumps and encoding etc

    _setdata(value) {   // Note SmartDict expects value to be a dictionary, which should be the case since the HTTP requester interprets as JSON
        if (value) {    // Skip if no data
            // value should be a dict by now, not still json as it is in Python
            //TODO-AUTHENTICTION - decrypt here
            this._setproperties(value); // Note value should not contain a "_data" field, so wont recurse even if catch "_data" at __setattr__()
        }
    }

    objbrowser(data, hash, path, verbose, ul) {
        if (path) {
            var hashpath = [hash, path].join("/");
        } else {
            var hashpath = hash;
        }
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
                if (text != "" && prop != "_hash") {    // Skip empty values; _hash (as shown above);
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
                                //console.log("XXX@216",prop,this[prop][l1]);
                                this[prop][l1].objbrowser(null, hash, path + "/"+this[prop][l1].name, verbose, ul3);
                            }
                        } else {
                            this[prop].objbrowser(null, hash, path, verbose, ul3);
                        }
                    } else {    // Any other field
                        if (prop == "hash") {
                            var spanval = document.createElement('a');
                            spanval.setAttribute('href','/file/b/'+this[prop]+"?contenttype="+this["Content-type"]);
                        } else {
                            // Group of fields where display then add behavior or something
                            var spanval = document.createElement('span');
                            if (prop == "_needsfetch") {
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

    size() { alert("Undefined function Block.size"); }
    content() { alert("Undefined function Block.content"); }

}

// ######### Parallel development to StructuredBlock.py ########

class StructuredBlock extends SmartDict {
    constructor(hash, data) {
        super(hash, data); // _hash is _hash of SB, not of data
        this._signatures = new Array()
        this._date = null;  // Updated in _earliestdate when loaded
        this.table = "sb";  // Note this is cls.table on python but need to separate from dictionary
    }
    store() { alert("Undefined function StructuredBlock.store"); }

    __setattr__(name, value) {  // Called by _setproperties < _setdata < constructor or onloaded.
        //catch equivalent of getters and setters here
        if (name == "links") {  // Assume its a SB TODO make dependent on which table
            let links = value;
            for (let len = links.length, i=0; i<len; i++) {
                let sb = new StructuredBlock(null, links[i]);
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
            if (links[i].name == name) {
                return links[i]
            }
        }
        console.log("Didn't find",name);
        return null;    // If not found
    }

    content() { alert("Undefined function StructuredBlock.store"); }
    file() { alert("Undefined function StructuredBlock.store"); }
    size() { alert("Undefined function StructuredBlock.store"); }
    path() { alert("Undefined function StructuredBlock.store"); }   // Done in onloaded, asynchronous recursion.
    sign() { alert("Undefined function StructuredBlock.store"); }
    verify() { alert("Undefined function StructuredBlock.store"); }


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
    constructor(hash, dic) {
        super(hash, dic);
        //console.log("Signature created",this.hash);
        //TODO turn s.date into java date
        //if isinstance(s.date, basestring):
        //    s.date = dateutil.parser.parse(s.date)
    }
    //TODO need to be able to verify signatures
    sign() { alert("Undefined function Signature.sign"); }
    verify() { alert("Undefined function Signature.verify"); }
}

// ######### Parallel development to MutableBlock.py ########


class CommonList extends SmartDict {
    constructor(hash, data, master) {
        //TODO note python allows constructor with use of mnemonic, keypair, keygen and pub/private
        super(hash, data);
        this._master = master;
        this._list = new Array();   // Array of signatures
    }
    _setkeypair() { alert("Undefined function CommonList._setkeypair"); }
    preflight() { alert("Undefined function CommonList.preflight"); }   // For storing data
    fetch() { alert("Undefined function CommonList.fetch"); }   // Split into load and onloaded

    load(verbose,  options) {   // Python can also fetch based on just having key
        if (this._needsfetch) { // Only load if need to
            if (verbose) { console.log("CommonList.load:",this._hash,options)}
            this._needsfetch = false
            if (options.fetchbody) {
                options.fetchbody = false;  // Dont refetch
                transport.rawfetch(this, this._hash, verbose, options);  // TODO this is only correct if its NOT master
            } else if (options.fetchlist) { // Cant fetch list to fetched body, as need hash of list
                options.fetchlist = false;  // Dont refetch
                transport.rawlist(this, this._hash, verbose, options);  // TODO this is only correct if its NOT master
            }
        }
    }


    onloaded(hash, data, verbose, options) { // Body loaded
        console.log("CommonList:onloaded data len=", data.length, options)
        this._setdata(JSON.parse(data))   // Actually calls super._setdata > _setproperties() > __setattr__
        //this._data = data;
        if (options.fetchlist) {
            options.fetchlist = false; // Done it here, dont do it again
            transport.rawlist(this, this._hash, verbose, options);  // TODO this is only correct if its NOT master
            return false; // Not complete doing rawlist
        } else {
            return true;
        }
    }
    onlisted(hash, lines, verbose, options) { // Body loaded
        console.log("CommonList:onlisted", hash, lines.length, options)
        //lines = JSON.parse(lines))   Should already by a list
        this._list = []
        for (let i in lines) {
            //TODO verify signature
            //if CryptoLib.verify(s):
            let s = new Signature(null, lines[i]);        // Signature ::= {date, hash, privatekey etc }
            this._list.push(s)
        }
        if (options.fetchblocks) {
            options.fetchblocks = false; // Done it here, dont do it again
            alert("CommonList.onlisted options=fetchblocks not implemented")
        }
        return true; // This layer handled, can do superclass stuff rather than wait for deeper loads
    }
    onposted(hash, data, verbose, options) {
        // This isn't used much yet, so for now just stores data, may be better as a struc of some kind
        console.log("CommonList:onposted data len=", data.length, options);
        this.storeto(data, hash, null, verbose, options) // TODO storeto handle img, or other non-HTML as reqd
    }

    blocks(fetchblocks, verbose) {
        let results = {};   // Dictionary of { SHA... : StructuredBlock(hash=SHA... _signatures:[Signature*] ] ) }
        for (let i in this._list) {
            let s = this._list[i];
            if (! results[s.hash]) {
                results[s.hash] = new StructuredBlock(s.hash, null);  //TODO Handle cases where its not a SB
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
    store() { alert("Undefined function CommonList.store"); }   // For storing data
    publicurl() { alert("Undefined function CommonList.publicurl"); }   // For access via web
    privateurl() { alert("Undefined function CommonList.privateurl"); }   // For access via web
    signandstore() { alert("Undefined function CommonList.signandstore"); }   // For storing data
    add() { alert("Undefined function CommonList.add"); }   // For storing data

}
class MutableBlock extends CommonList {
    // { _hash, _key, _current: StructuredBlock, _list: [ StructuredBlock*]

    constructor(hash, data, master) {
        super(hash, null, master);
        // Note python __init__ also allows constructing with key, or with neither key nor hash
        this._current = null;
    }

    onlisted(hash, lines, verbose, options) {
        let handled = super.onlisted(hash, lines, verbose, options);
        if (handled) {  // Should always be handled until fetchblocks implemented
            let sig = this._list[this._list.length-1];
            this._current = new StructuredBlock(sig.hash, null);
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
        console.log("XXX493",blocks);
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

    contentacl() { alert("Undefined function MutableBlock.contentacl setter and getter"); }   // Encryption of content
    fetch() { alert("Undefined function MutableBlock.fetch"); }   // Split into load/onload/onlisted
    content() { alert("Undefined function MutableBlock.store"); }   // Retrieving data
    file() { alert("Undefined function MutableBlock.store"); }   // Retrieving data
    signandstore() { alert("Undefined function MutableBlock.signandstore"); }   // Retrieving data
    path() { alert("Undefined function MutableBlock.path"); }   // Built into onloaded
    new() { alert("Undefined function MutableBlock.new"); }   // Utility function for creating mb

}
// ==== UI related functions, not dWeb specific =========
function togglevisnext(elem) {   // Hide the next sibling object and show the one after, or vica-versa,
    el1 = elem.nextSibling;
    el2 = el1.nextSibling;
    if (el1.style.display == "none") {
        el1.style.display = "";
        el2.style.display = "none";
    } else {
        el1.style.display = "none";
        el2.style.display = "";
    }
}

function dofetch(el) {
    source = el.source;
    console.log("XXX",source);
    parent = el.parentNode;
    parent.removeChild(el); //Remove elem from parent
    source.load(true, {"objbrowser": parent});
}

// ==== NON OBJECT ORIENTED FUNCTIONS ==============

function dwebfile(table, hash, path, options) {
    // Simple utility function to load into a hash without dealing with individual objects
    if (path && (path.length > 0)) {
        options.path = path.split('/');
    }
    if (table == "mb") {
        var mb = new MutableBlock(hash, null, false);
        options.fetchlist = true;
        options.fetchbody = true;
        mb.load(true, options); //verbose, fetchbody, fetchlist, !fetchblocks
    } else if (table == "sb") {
        var sb = new StructuredBlock(hash, null);
        sb.load(true, options);
    } else {
        alert("dwebfile called with invalid table="+table);
    }
}

function dwebupdate(hash, type, data, options) {
    mbm = new MutableBlock(hash, null, true);
    mbm.update(type, data, true, options);  //TODO failing as result is HTML but treated as Javascript - can intercept post
}

function dweblist(div, hash) {
    var mb = new MutableBlock(hash, null, false);
    options = {}
    options.fetchlist = true;
    options.fetchbody = true;
    options.elem = div;
    mb.load(true, options); //verbose, fetchbody, fetchlist, !fetchblocks
}
// ======== EXPERIMENTAL ZONA ==================

//TODO BROWSER----
//-data collapsable