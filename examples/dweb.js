// Javascript library for dweb

var dwebserver = 'localhost';
//var dwebserver = '192.168.1.156';
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
        // optioms: are passed to class specific onloaded
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
        if (verbose) { console.log("TransportHTTP load:",command, ":hash=", hash, "path=", path, "options=", options); }
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

    block(self, hash, verbose, options) {    //TODO merge with transport.list
        // Locate and return a block, based on its multihash
        // options: are passed to class specific onloaded
        // Locate and return a block, based on its multihash
        this.load(self, "block", hash, [], verbose, options);    //TODO-PATH
    }

    list(self, hash, verbose, options) {
        // obj being loaded
        // options: are passed to class specific onloaded
        // Locate and return a block, based on its multihash
        this.load(self, "list", hash, [], verbose, options); //TODO-PATH
    }

    url(command, hash) {
        var url = this.baseurl + command + "/" + hash;
        return url;
    }
}

var transport = TransportHttp.setup([dwebserver, dwebport], {});

class Block {
    constructor(hash, data) {
        this._hash = hash;  // Hash of the _data
        this._data = data;  // The data being stored
        this._table = 'b';  // Table hash found in, TODO might want to move to _table python
    }

    block(verbose, options) {
        transport.block(this, this._hash, verbose, options);
        // Block fetched in the background - dont assume loaded here, see onloaded
    }

    onloaded(data, verbose, options) {
        // Called after block succeeds, can pass options through
        // copies at Block, MutableBlock
        if (verbose) { console.log("Block:onloaded:Storing _data to", options["dom_id"]); }
        this._data = data;
        if (options["dom_id"]) {
                    document.getElementById(options["dom_id"]).innerHTML = this._data;
        } // TODO make it handle img, or other non-HTML as reqd
    }
}

class StructuredBlock extends Block { //TODO can subclass SmartDict if used elsewhere
    constructor(hash) { //TODO support other things in construction
        super(hash, null); // _hash is _hash of SB, not of data
        this._table = "sb"; // Note this is cls.table on python but need to separate from dictionary
    }
    _setproperties(dict) {
        for (let prop in dict) {
            if (prop == "links") {  // Assume its a SB TODO make dependent on which table
                let links = dict[prop];
                for (let len = links.length, i=0; i<len; i++) {
                    let sb = new StructuredBlock();
                    sb._setproperties(links[i]);    // Can recurse down the path
                    links[i] = sb;
                }
                this[prop] = links;
            } else {
                this[prop] = dict[prop];
            }
        }
    }
    link(name) {
        let links = this.links;
        for (let len = links.length, i=0; i<len; i++) {
            if (links[i].name == name) {
                return links[i]
            }
        }
        console.log("Didn't find",name);
        return null;    // If not found
    }
    load(verbose, options) {
        // Locate and return a block, based on its multihash
        if (verbose) { console.log("Fetching StructuredBlock hash=",this._hash,"options=",options); }
        this.block(verbose, options);
        // Block fetched in the background - dont assume loaded here
    }
    onloaded(data, verbose, options) {
        console.log("StructuredBlock:onloaded data len=", data.length, options)
        this._data = data;
        this._setproperties(JSON.parse(data));
        if (options.path && options.path.length) {  //TODO-PATH unclear if want a path or a list - start with a list
            let next = options["path"].shift(); // Takes first element of path, leaves path as rest
            let sb = this.link(next);   //TODO handle error of not found
            sb.load(verbose, options);  // passes shorter path and any dom arg load and to its onloaded
        } else { // dom_id etc are done on the leaf, not the intermediaries
                storeto(this.data, verbose, options);  // See if options say to store in a DIV for example
        }
    }
}
class Signature {
    constructor(dic) {
        this.date = dic["date"];
        this.hash = dic["hash"];
        this.publickey = dic["publickey"];
        this.signature = dic["signature"]
        //console.log("Signature created",this.hash);
    }
    //TODO need to be able to verify signatures
}

class SignedBlock {
    // TODO Build Signed Block - allow retrieval of SB from it

    constructor(hash) { // Python also handles, structuredblock=None, signatures=None, verbose=False, **options):
        // Adapted from Python SignedBlock
        // if structuredblock and not isinstance(structuredblock, StructuredBlock):
        //     structuredblock = StructuredBlock(structuredblock) # Handles dict or json of dict
        this._structuredblock = null; // Would be from structuredblock if passed
        this._hash = hash;              // Hash of structured block
        this._signatures = new Array(); //Would initialize to Signatures(signatures or [])
        this._date = null;
    }

    load(verbose, options) {
        if (this._structuredblock) {
            this._structuredblock.onloaded(options);
        } else {
            let sb = new StructuredBlock(this._hash);
            sb.load(verbose, options);    // Asynchronous load - calls SB.onloaded
        }
    }


    earliestdate() {
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

class MutableBlock {
    // TODO Build MutableBlock - allow fetch of signatures, and fetching them
    // TODO allow fetching of most recent
    // { _hash, _key, _current: SignedBlock, _list: [ SignedBlock*]

    constructor(hash) {
        // Note python __init__ also allows constructing with key, or with neither key nor hash
        this._hash = hash;       // Could be None
        this._key = null;
        this._current = null;
        this._list = new Array();
    }

    load(verbose, options) {   // Python can also fetch based on just having key
        transport.list(this, this._hash, verbose, options);
    }

    onloaded(lines, verbose, options) {
        let results = {};   // Dictionary of { SHA... : SignedBlock(hash=SHA... _signatures:[Signature*] ] ) }
        for (let i in lines) {
            let s = new Signature(lines[i]);        // Signature ::= {date, hash, privatekey etc }
            if (! results[s.hash]) {
                results[s.hash] = new SignedBlock(s.hash);
            }
            //TODO turn s.date into java date
            //if isinstance(s.date, basestring):
            //    s.date = dateutil.parser.parse(s.date)
            //TODO verify signature
            //if CryptoLib.verify(s):
            results[s.hash]._signatures.push(s);
        }
        let sbs = new Array();      // [ SignedBlock* ]
        for (let k in results) {
            sbs.push(results[k]);      // Array of SignedBlock
        }
        //TODO sort list
        sbs.sort(SignedBlock.compare); // Could inline: sbs.sort(function(a, b) { ... }
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
