const TransportIPFS = require('./TransportIPFS');
//const Block= require('./Block')
const Dweb = require('./Dweb');

// Utility packages (ours) Aand one-loners
const makepromises = require('./utils/makepromises');
function delay(ms, val) { return new Promise(resolve => {setTimeout(() => { resolve(val); },ms)})}

// Fake a browser like environment for some tests
const jsdom = require("jsdom");
const { JSDOM } = jsdom;        //TODO - figure out what this does, dont understand the Javascript
htmlfake = '<!DOCTYPE html><ul><li id="myList.0">Failed to load sb via StructuredBlock</li><li id="myList.1">Failed to load mb via MutableBlock</li><li id="myList.2">Failed to load sb via dwebfile</li><li id="myList.3">Failed to load mb via dwebfile</li></ul>';
const dom = new JSDOM(htmlfake);
//console.log("XXX@8",dom.window.document.getElementById("myList.0").textContent); // Before loading = "Failed to load sb via StructuredBlock"
document = dom.window.document;   // Note in JS can't see "document" like can in python


let verbose = false;
let blk;
let blk2;
let sb;

    TransportIPFS.setup({}, verbose, {})
    .then((t) => {
        if (verbose) console.log("setup returned and transport set - including annoationList");
        Dweb.transport = t;
    })
    .then(() => TransportIPFS.test(Dweb.transport, verbose))
    .then(() => Dweb.Block.test(Dweb.transport, verbose))
    .then(() => Dweb.StructuredBlock.test(Dweb.transport, document, verbose))
    .then((testobjs) => sb = testobjs.sb)
    .then(() => Dweb.MutableBlock.test(sb, Dweb.transport, verbose))
    .then(() => Dweb.CryptoLib.test(verbose))
    .then(() => verbose = true)
    .then(() => Dweb.KeyChain.test(verbose))
    .then(() => console.log("delaying 10 secs"))
    .then(() => delay(10000))
    .then(()=>console.log("Completed test"))
    .catch((err) => console.log("Test failed", err))


/* path tests not done ... old ones
 console.log("Now test path using dwebfile and sb =======");
 verbose=false;
 Dweb.async_dwebfile("sb", sbhash, "langs/readme.md", ["async_elem", "myList.2", verbose, null, null], null);
 console.log("Now test path using dwebfile and mb =======");
 Dweb.async_dwebfile("mb", mbhash, "langs/readme.md", ["async_elem", "myList.3", verbose, null, null], null);
 console.log("END testing previouslyworking()");

 */