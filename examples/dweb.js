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
                self.onloaded(msg, verbose, options);
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

    load(self, command, hash, path, verbose, options) {
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
                self.onloaded(data, verbose, options);
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
        this.load(self, "rawfetch", hash, [], verbose, options);    //TODO-PATH
    }

    rawlist(self, hash, verbose, options) {
        // obj being loaded
        // options: are passed to class specific onloaded
        // Locate and return a block, based on its multihash
        this.load(self, "rawlist", hash, [], verbose, options); //TODO-PATH
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
}

// ######### Parallel development to Block.py ########

class Block extends Transportable {
    constructor(hash, data) {
        super(hash, data);
        this.table = 'b';
    }

    onloaded(data, verbose, options) {
        // Called after block succeeds, can pass options through
        // copies at Block, MutableBlock
        if (verbose) { console.log("Block:onloaded:Storing _data to", options["dom_id"]); }
        this._data = data;
        storeto(data, verbose, options) // TODO storeto handle img, or other non-HTML as reqd
    }

    size() { alert("Undefined function Block.size"); }
    content() { alert("Undefined function Block.content"); }

}

// ######### Parallel development to StructuredBlock.py ########

class StructuredBlock extends SmartDict {
    constructor(hash) { //TODO-REFACTOR make all calls call hash,null
        super(hash, null); // _hash is _hash of SB, not of data
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
                let sb = new StructuredBlock();
                sb._setproperties(links[i]);    // Can recurse down the path
                links[i] = sb;
            }
            this[name] = links;
        } else {
            super.__setattr__(name, value);
        }
    }

    onloaded(data, verbose, options) {  // Equivalent of _setdata in Python
        console.log("StructuredBlock:onloaded data len=", data.length, options)
        this._setdata(JSON.parse(data))   // Actually calls super, and calls _setproperties()
        //this._data = data;

        let sb = this;
        while (options.path && options.path.length && this.links.length ) { // Have a path and can do it on sb
            let next = options["path"].shift(); // Takes first element of path, leaves path as rest
            console.log("StructuredBlock:onloaded next path=",next);
            sb = sb.link(next);   //TODO handle error of not found
        }
        // At this point sb points as far down the path as we could go without loading.
        if (options.path && options.path.length) {  // We still have path to explore, but no links on loaded sb
                sb.load(verbose, options);  // passes shorter path and any dom arg load and to its onloaded
        } else {  // Walked to end of path, can handle
                console.log("StructuredBlock.onloaded storing len=",sb.data.length);
                storeto(sb.data, verbose, options);  // See if options say to store in a DIV for example
        }
    }
    dirty() {
        super.dirty();
        this._signatures = new Array(); //TODO-REFACTOR Not sure whether should be null or Signatures([])
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
    }
    //TODO need to be able to verify signatures
    sign() { alert("Undefined function Signature.sign"); }
    verify() { alert("Undefined function Signature.verify"); }
}

// ######### Parallel development to MutableBlock.py ########

class MutableBlock {
    // TODO Build MutableBlock - allow fetch of signatures, and fetching them
    // TODO allow fetching of most recent
    // { _hash, _key, _current: StructuredBlock, _list: [ StructuredBlock*]

    constructor(hash) {
        // Note python __init__ also allows constructing with key, or with neither key nor hash
        this._hash = hash;       // Could be None
        this._key = null;
        this._current = null;
        this._list = new Array();
    }

    load(verbose, options) {   // Python can also fetch based on just having key
        transport.rawlist(this, this._hash, verbose, options);
    }

    onloaded(lines, verbose, options) {
        let results = {};   // Dictionary of { SHA... : StructuredBlock(hash=SHA... _signatures:[Signature*] ] ) }
        for (let i in lines) {
            let s = new Signature(null, lines[i]);        // Signature ::= {date, hash, privatekey etc }
            if (! results[s.hash]) {
                results[s.hash] = new StructuredBlock(s.hash);
            }
            //TODO turn s.date into java date
            //if isinstance(s.date, basestring):
            //    s.date = dateutil.parser.parse(s.date)
            //TODO verify signature
            //if CryptoLib.verify(s):
            results[s.hash]._signatures.push(s);
        }
        let sbs = new Array();      // [ StructuredBlock* ]
        for (let k in results) {
            sbs.push(results[k]);      // Array of StructuredBlock
        }
        //TODO sort list
        sbs.sort(StructuredBlock.compare); // Could inline: sbs.sort(function(a, b) { ... }
        this._current = sbs[sbs.length-1];
        this._list = sbs;
        if (options.path && options.path.length) {  //TODO-PATH unclear if want a path or a list - start with a list
            this._current.load(verbose, options);
        } else { // dom_id etc are done on the leaf, not the intermediaries
            if (options["dom_id"]) {
                if (verbose) { console.log("MutableBlock:onloaded:Storing data to", options["dom_id"]); }
                let ul = document.getElementById(options["dom_id"]);
                this.updatelist(ul, verbose);
            } // TODO make it handle img, or other non-HTML as reqd based on this._dict["Content-type"]
        }
    }

    updatelist(ul, verbose) {
        while (ul.hasChildNodes()) {
            ul.removeChild(ul.lastChild);
        }
        for (let ii in this._list) {     // Signed Blocks
            let i = this._list[ii];
            let li = document.createElement("li");
            ul.appendChild(li);
            i.load(verbose, { "elem": li });
        }
    }
}

class MutableBlockMaster {
    // TODO - allow to drive editor (MCE)
    constructor(hash) {
        // Note python __init__ also allows constructing with key, or with neither key nor hash
        this._hash = hash;       // Could be None
        this._key = null;
        this._current = null;
        this._list = new Array();
    }
    update(type, data, verbose, options) {
        transport.update(this, this._hash, type, data, verbose, options);
    }
    onloaded(data, verbose, options) {
        // Called after block succeeds, can pass options through
        // copies at Block, MutableBlock
        if (verbose) { console.log("MBM:onloaded:Storing _data to", options["dom_id"]); }
        this._data = data;
        storeto(data, verbose, options)  // See if options say to store in a DIV for example
    }
}

// ==== LIBRARY FUNCTIONS =======================
function storeto(data, verbose, options) {
    //TODO replace parts above that check dom_id
    // Can be called to check if options have instructions what to do with data
    // Its perfectly legitimate to call this, and nothing gets done with the data
    if (options.dom_id) {
        if (verbose) { console.log("onloaded:Storing data to", options.dom_id); }
        document.getElementById(options.dom_id).innerHTML = data;
    } // TODO make it handle img, or other non-HTML as reqd based on this["Content-type"]
    if (options.elem) {
        if (verbose) { console.log("onloaded:Storing data to element"); }
        options.elem.innerHTML = data;
    } // TODO make it handle img, or other non-HTML as reqd based on this["Content-type"]
}

// ==== NON OBJECT ORIENTED FUNCTIONS ==============

function dwebfile(table, hash, path, options) {
    // Simple utility function to load into a hash without dealing with individual objects
    if (path && (path.length > 0)) {
        options.path = path.split('/');
    }
    if (table == "mb") {
        var MorSb = new MutableBlock(hash); //TODO-KEY check all similar calls to make sure MutableBlock still takes parm 0 = hash
    } else if (table == "sb") {
        var MorSb = new StructuredBlock(hash);
    } else {
        alert("dwebfile called with invalid table="+table);
    }
    MorSb.load(true, options);
}

function dwebupdate(hash, type, data, options) {
    mbm = new MutableBlockMaster(hash);  //TODO-KEY check all similar calls to make sure MutableBlock still takes parm 0 = hash
    mbm.update(type, data, true, options);
}

function dweblist(div, hash) {
    var mb = new MutableBlock(hash);  //TODO-KEY check all similar calls to make sure MutableBlock still takes parm 0 = hash
    mb.load(true, {"dom_id": div});
}

<!-- alert("dweb.js loaded"); -->
<!-- https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes -->
