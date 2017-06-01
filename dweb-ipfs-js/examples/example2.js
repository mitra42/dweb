// This example is to give a simple set of tests that incrementally run through the APIs I'm expecting to use for Dweb
'use strict';

// Other packages
const fs = require('fs')
const os = require('os')
const path = require('path')
const promisify = require('promisify-es6'); //TODO remove as obsoleted by makepromises


// IPFS packages
const CID = require('cids');                // Content IDs
const Block = require('ipfs-block');        // Blocks (hash + data)
const multihash = require('multihashes');   // Multihash - binary representation including type of hash
const IPFS = require('ipfs');               // This might obviate need for some of the others, but not sure.

// Utility packages (ours)
const makepromises = require('../utils/makepromises')
// Dweb packages (ours)

/*
 * Create a new IPFS instance, using default repo (fs) on default path (~/.ipfs)
 */
//const repodir = path.join(os.tmpdir() + '/' + new Date().toString())
const repodir = '/tmp/ipfs' + Math.random()
console.log("Storing to",repodir);


let ipfs
// (Earlier version and example1 Rewritten as a promise with promisify inline


ipfs = new IPFS({
    repo: repodir,
    init: false,
    start: false,
    EXPERIMENTAL: {
        pubsub: true
    }
})

// Note many (but not all) ipfs functionality already promisify's as of (as of 2017-05-27)
// DO: version, start, init, dag.*, pubsub
// DONT block.*
const promises_needed = [ { block: ["put", "get"] }]
const promisified = {ipfs:{}}
makepromises(ipfs, promisified.ipfs, promises_needed); // Has to be after ipfs defined
//console.log(promisified.ipfs);



// (Earlier version and example1 Rewritten as a promise with promisify inline

// This chunk starts up IPFS
function start() {
    return new Promise((resolve, reject) => {
        ipfs.version()
            .then((version) => console.log("Version=", version))
            .then((unused) => ipfs.init({emptyRepo: true, bits: 2048}))
            .then((unused) => ipfs.start())
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
        promisified.ipfs.block.put(blob)
            .then((block) => {
                //console.log(block);
                let cid = block.cid;
                //console.log("CID=",cid);
                return cid;
            })
            .then((cid) => promisified.ipfs.block.get(cid))
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
        ipfs.dag.put(mydata, {format: 'dag-cbor', hashAlg: 'sha2-256'})
        //.then((cid) => { console.log("DAG PUT=",cid); return(cid); })
            .then((cid)=>ipfs.dag.get(cid))
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



// (Earlier version and example1 Rewritten as a promise with promisify inline

const msg1 = "Did you hear that"
const receiveMsg = (msg) => {
    console.log("Subscribe received",msg.data.toString());
    console.assert(msg.data.toString() === msg1, "Should hear msg1 back from publish")
}


// This chunk starts up IPFS
function pubsubtest() {
    return new Promise((resolve, reject) => {
        let topic = "A place to gossip";
        console.log("pubsubtest starting")
        ipfs.pubsub.subscribe(topic, receiveMsg);   // Not a promise it sets up receiveMsg as a listener
        ipfs.pubsub.publish(topic, new Buffer(msg1))
            .then((unused) => {
                if (ipfs.isOnline()) console.log('pubsubtest Exiting');
                resolve(undefined);
            })    //TODO throw error if not online
            .catch((err) => {
                console.log("UNCAUGHT ERROR in start", err);
                reject(err)
            })
    })
}


//Serial just one
//start().then((unused) => pubsubtest())

//Serial all of them
//start().then((res) => blocktest(res)).then((unused) => dagtest(unused)).then((unused) => pubsubtest())

// or Parallel all of them
start().then((unused) => Promise.all([ blocktest(""), dagtest("STARTING DAG"), pubsubtest() ]))


/* Pending input from David & Matt
 const cid = new CID(1, 'dag-pb', multihash);  //TODO- what is this ?
 */

