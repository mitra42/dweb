exports.TransportHTTP = require('./TransportHTTP');
exports.StructuredBlock = require('./StructuredBlock');
exports.MutableBlock = require('./MutableBlock');
exports.KeyChain = require('./KeyChain');


// Javascript library for dweb
// The crypto uses https://github.com/jedisct1/libsodium.js but https://github.com/paixaop/node-sodium may also be suitable if we move to node

exports.utils = {}; //utility functions

exports.dwebserver = 'localhost';
//exports.dwebserver = '192.168.1.156';
exports.dwebport = '4243';
exports.keychains = [];

// Constants    //TODO move these to KeyPair
exports.KEYPAIRKEYTYPESIGN = 1;
exports.KEYPAIRKEYTYPEENCRYPT = 2;
exports.KEYPAIRKEYTYPESIGNANDENCRYPT = 3;

//TODO-ASYNC-SIGN - sign and signandstore
//TODO-ASYNC - search on TODO-ASYNC
//TODO-ASYNC - fix objbrowser's path
// ==== OBJECT ORIENTED JAVASCRIPT ===============

// These are equivalent of python exceptions, will log and raise alert in most cases - exceptions aren't caught

exports.utils.SecurityWarning = function(msg, self) {
    console.log(msg, self);
    alert(msg);
};

exports.utils.ToBeImplementedException = function(...args) {
    console.assert(false, ...args);
    //alert(msg);
};

// Utility functions

exports.utils.mergeTypedArraysUnsafe = function(a, b) { // Take care of inability to concatenate typed arrays
    //http://stackoverflow.com/questions/14071463/how-can-i-merge-typedarrays-in-javascript also has a safe version
    const c = new a.constructor(a.length + b.length);
    c.set(a);
    c.set(b, a.length);
    return c;
};
//TODO document from here down

// ==== UI related functions, not dWeb specific =========
//noinspection JSUnusedGlobalSymbols
exports.utils.togglevisnext = function(elem) {   // Hide the next sibling object and show the one after, or vica-versa,
    let el1 = elem.nextSibling;
    let el2 = el1.nextSibling;
    if (el1.style.display === "none") {
        el1.style.display = "";
        el2.style.display = "none";
    } else {
        el1.style.display = "none";
        el2.style.display = "";
    }
};

//noinspection JSUnusedGlobalSymbols
exports.utils.async_objbrowserfetch = function(el) {
    let verbose = false;
    let source = el.source;
    let parent = el.parentNode;
    parent.removeChild(el); //Remove elem from parent
    source.async_load(true, function(msg) { source.objbrowser(source._hash, null, parent, false );}, null);
};

// ==== NON OBJECT ORIENTED FUNCTIONS ==============

exports.async_dwebfile = function(table, hash, path, successmethod, error) {
    // Simple utility function to load into a hash without dealing with individual objects
    // successmethod - see "path()" for definition.
    let verbose = false;
    if (path && (path.length > 0)) {
        path = path.split('/');
    }
    if (verbose) { console.log("Dweb.async_dwebfile",table,hash,path,successmethod);}
    if (table === "mb") {
        //(hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose)
        const mb = new exports.MutableBlock(hash, null, false, null, false, null, null, null, verbose, null);
        // Call chain is mb.load > CL.fetchlist > THttp.rawlist > Thttp.load > MB.fetchlist.success > caller.success
        // for dwebfile:mb, we want to apply the success function to the file - which is in the content after fetchlist
        mb.async_loadandfetchlist(verbose, function(msg) { mb.async_path(path, verbose, successmethod, error);}, error);
        // Note success is applied once after list is fetched, content isn't loaded before that.
    } else if (table === "sb") {
        const sb = new exports.StructuredBlock(hash, null, verbose);
        sb.async_load(verbose, function(msg) {sb.async_path(path, verbose, successmethod, error);}, error);
    } else {
        alert("dwebfile called with invalid table="+table);
    }
};

exports.async_dwebupdate = function(hash, type, data, successmethod, error) {
    let verbose = false;
    //(hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose)
    let mbm = new exports.MutableBlock(hash, null, true, null, false, null, null, null, verbose, null);
    mbm.async_update( type, data, verbose,
        function(msg){
            if (successmethod) {
                let methodname = successmethod.shift();
                //if (verbose) console.log("async_elem",methodname, successmethod);
                mbm[methodname](...successmethod); // Spreads successmethod into args, like *args in python
            }
        },
        error);
};

exports.async_dweblist = function(div, hash, verbose, success, successmethodeach, error) {
    //Retrieve a list, and create <li> elements of div to hold it.
    //success, if present, is run after list retrieved, asynchronous with elements retrieved
    //successeach, is run on each object in the list.
    verbose = false;
    //(hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose)
    const mb = new exports.MutableBlock(hash, null, false, null, false, null, null, null, verbose, null);
    // Call chain is mb.load > CL.fetchlist > THttp.rawlist > Thttp.load > MB.fetchlist.success
    mb.async_loadandfetchlist(verbose,
        function(msg) {
            mb.async_elem(div, verbose, successmethodeach, error); // async_elem loads the block
            if (success) {success(null);}    // Note success will fire async with list elements being loaded
        },
        error);
};
// ======== EXPERIMENTAL ZONA ==================

//TODO BROWSER----
//-data collapsable

exports.transport = exports.TransportHTTP.setup([exports.dwebserver, exports.dwebport], {});


