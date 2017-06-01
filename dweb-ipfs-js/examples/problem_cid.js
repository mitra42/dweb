// Ths illustrates the problem with CID

'use strict';


// IPFS packages
const CID = require('cids');                // Content IDs
const multihash = require('multihashes');   // Multihash - binary representation including type of hash
const cid = new CID(1, 'dag-pb', multihash)
console.log("CID=",cid)


