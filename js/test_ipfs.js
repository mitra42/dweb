const TransportIPFS = require('./TransportIPFS');
const Block= require('./Block')
const Dweb = require('./Dweb');

// Utility packages (ours) Aand one-loners
const makepromises = require('./utils/makepromises');
function delay(ms, val) { return new Promise(resolve => {setTimeout(() => { resolve(val); },ms)})}
function consolearr(arr) { return (arr && arr.length >0) ? [arr.length+" items inc:", arr[-1]] : arr}


let verbose = true;
let blk;

    TransportIPFS.setup({}, verbose, {})
    .then((t) => {
        if (verbose) console.log("setup returned and transport set - including annoationList");
        Dweb.transport = t;
    })
    .then(() => TransportIPFS.test(Dweb.transport))
    .then(() => {blk = new Block(null,"The dirty old chicken")})
    .then(() => blk.p_store(verbose))
/*    .then(() => {
        let blk2 = new Block(blk._hash, null);
        blk2.p_fetch(verbose);
        return(blk2)
        })
    .then((blk2) => console.log("XXX@27",blk2))
 */
    .then(() => console.log("delaying 10 secs"))
    .then(() => delay(10000))
    .then(()=>console.log("Completed test"))
    .catch((err) => console.log("Test failed", err))
