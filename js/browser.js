// Stub to run browserify on
// This makes them available as "sodium" and "Dweb" from test.html etc
window.Dweb = require('./Dweb');    //TODO move inner calls in Dweb to save locally
window.sodium = require("libsodium-wrappers");  // Needed for cryptotest
window.ZZ1 = "Hello there";
//window.IIFDB = require('ipfs-iiif-db');
window.TransportIPFS = require('./TransportIPFS');
window.ZZ3 = "Goodbye";
//window.TransportHTTP = require('./TransportHTTP');
