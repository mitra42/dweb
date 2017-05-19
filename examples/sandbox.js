/**
 * Created by mitra on 16/5/17.
 */

Sandbox2 = require("./sandbox2.js");

foo = new Sandbox2;
console.log(foo.myname);
var sodium = require('libsodium-wrappers');
console.log(sodium.to_hex(sodium.crypto_generichash(64, 'test')));