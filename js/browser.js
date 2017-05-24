// Stub to run browserify on
// This makes them available as "sodium" and "Dweb" from test.html etc
window.Dweb = require('./Dweb');    //TODO move inner calls in Dweb to save locally
window.sodium = require("libsodium-wrappers");  // Needed for cryptotest
