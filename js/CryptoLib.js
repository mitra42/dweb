const sodium = require("libsodium-wrappers");

// ==== Crypto.py - Encapsulate all the Cryptography =========
class CryptoLib {
    static Curlhash(data) { return "BLAKE2."+ sodium.crypto_generichash(32, data, null, 'urlsafebase64'); }
    static signature(keypair, date, hash) {
        console.log("XXX Undefined function CryptoLib.signature"); //TODO-ASYNC-SIGN
        return "XYZZY TODO-ASYNC-SIGN undefined function signature";
    }
    static verify() { console.log("XXX Undefined function CryptoLib.verify"); }
    static b64dec() { console.log("XXX Undefined function CryptoLib.b64dec"); }
    static b64enc() { console.log("XXX Undefined function CryptoLib.b64enc"); }

    static dumps(obj) { return JSON.stringify(obj); }   // Uses toJSON methods on objects (equivalent of dumps methods on python)

    static decryptdata() { console.log("XXX Undefined function CryptoLib.decryptdata"); }
    static randomkey() { console.log("XXX Undefined function CryptoLib.randomkey"); }
    static sym_encrypt() { console.log("XXX Undefined function CryptoLib.sym_encrypt"); }
    static sym_decrypt() { console.log("XXX Undefined function CryptoLib.sym_decrypt"); }
}

exports = module.exports = CryptoLib;

