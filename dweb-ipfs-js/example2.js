// This example is to give a simple set of tests that incrementally run through the APIs I'm expecting to use for Dweb
'use strict';

// Other pagages
const fs = require('fs')
const os = require('os')
const path = require('path')
const promisify = require('promisify-es6');

// IPFS packages
const CID = require('cids');                // Content IDs
const Block = require('ipfs-block');        // Blocks (hash + data)
const multihash = require('multihashes');   // Multihash - binary representation including type of hash
const IPFS = require('ipfs');               // This might obviate need for some of the others, but not sure.



/*
 * Create a new IPFS instance, using default repo (fs) on default path (~/.ipfs)
 */
//const repodir = path.join(os.tmpdir() + '/' + new Date().toString())
const repodir = '/tmp/ipfs' + Math.random()
console.log("Storing to",repodir);
const ipfs = new IPFS({
    repo: repodir,
    init: false,
    start: false,
    EXPERIMENTAL: {
        pubsub: false
    }
})


// (Earlier version and example1 Rewritten as a promise with promisify inline

// This chunk starts up IPFS
function start() {
    return new Promise((resolve, reject) => {
        promisify(ipfs.version)()
            .then((version) => console.log("Version=", version))
            .then((unused) => promisify(ipfs.init)({emptyRepo: true, bits: 2048}))
            .then((unused) => promisify(ipfs.start)())
            .then((unused) => {
                if (ipfs.isOnline()) console.log('IPFS node is now ready and online');
                resolve("MY MESSAGE");
            })    //TODO throw error if not online
            .catch((err) => {
                console.log("UNCAUGHT ERROR in start", err);
                reject(err)
            })
    })
}

// This chunk tests block storage
function blocktest(message) {
    let blobtxt = 'a serialized object'
    const blob = new Buffer(blobtxt);
    let cid;    // Holds id of block stored
    return new Promise((resolve, reject) => {
        console.log("MESSAGE=",message)
        promisify(ipfs.block.put)(blob)
            .then((block) => {
                //console.log(block);
                let cid = block.cid;
                //console.log("CID=",cid);
                return cid;
            })
            .then((cid) => promisify(ipfs.block.get)(cid))
            .then((result) => {
                //console.log(result);
                let data = result.data.toString();
                console.log("Block Data=", data);
                resolve(data);
            })
            //.then((data) => console.assert(data === blobtxt, "Should round trip ok"))
            .catch((err) => {
                console.log("UNCAUGHT ERROR IN BLOCKTEST", err)
                reject(err)
            })
    })
}
function dagtest(message) {
    let mydata = { name: 'Foo Bar', address: 'last shack on right'}
    return new Promise((resolve, reject) => {
        console.log("Starting dagtest",message);
        promisify(ipfs.dag.put)(mydata, {format: 'dag-cbor', hashAlg: 'sha2-256'})
        //.then((cid) => { console.log("DAG PUT=",cid); return(cid); })
            .then((cid)=>promisify(ipfs.dag.get)(cid))
            .then((result)=>{
                //console.log(result.value);
                console.assert(result.value.name === mydata.name, "DAG should survive roundtrip");
                console.log("DAG finishing");
            })
            .catch((err) => {
                console.log("UNCAUGHT ERROR IN BLOCKTEST", err)
                reject(err)
            })
    })
}


//Serial
//start().then((res) => blocktest(res)).then((unused) => dagtest(unused))

// or Parallel
start().then((unused) => Promise.all([ blocktest(""), dagtest("STARTING DAG") ]))

/* Pending input from David & Matt
 const cid = new CID(1, 'dag-pb', multihash);  //TODO- what is this ?
 */

