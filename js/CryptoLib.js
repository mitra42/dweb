//const AccessControlList = require("./AccessControlList"); // Including this for some reason makes the result unavailable, maybe a loop ?
//const KeyChain = require("./KeyChain"); // Including this for some reason makes the result unavailable, maybe a loop ?

//IPFS packages needed
const multihashes = require('multihashes');

//Other packages needed
const sodium = require("libsodium-wrappers");
const crypto = require ('crypto');
const Dweb = require("./Dweb");

//CryptoLib = {}
// ==== Crypto.py - Encapsulate all the Cryptography =========
// This was the libsodium version using Blake2
//CryptoLib.Curlhash = function(data) { return "BLAKE2."+ sodium.crypto_generichash(32, data, null, 'urlsafebase64'); }
//Specific to IPFS
exports.Curlhash = function(data) {
    if (Dweb.transport.hashtype === "BLAKE2") {
        return "BLAKE2."+ sodium.crypto_generichash(32, data, null, 'urlsafebase64');
    } else {    //TransportIPFS
        let b2 = (data instanceof Buffer) ? data : new Buffer(data);
        let b3 = crypto.createHash('sha256').update(b2).digest();
        let hash = multihashes.toB58String(multihashes.encode(b3, 'sha2-256'));  //TODO-IPFS-Q unclear how to make generic
        return "/ipfs/" + hash
    }
};
exports._signable = function(date, data) {
        /*
         Returns a string suitable for signing and dating, current implementation includes date and storage hash of data.
         Called by signature, so that same thing signed as compared

         :param date: Date on which it was signed
         :param data: Storage hash of data signed (as returned by Transport layer) - will convert to str if its unicode
         :return: Signable or comparable string
         COPIED TO JS 2017-05-23
         */
        return date.toISOString() + data;
    };

exports.signature = function(keypair, date, hash, verbose) {
        /*
        Pair of verify(), signs date and data using public key function.

        :param keypair: Key that be used for signature
        :param date: Date that signing (usually now)
        :return: signature that can be verified with verify
        COPIED FROM PYTHON 2017-05-23 excluding RSA and WordHashKey support
        */
        console.assert(keypair && date && hash);
        let signable = Dweb.CryptoLib._signable(date, hash); // A string we can sign
        if (keypair._key.sign.privateKey) {
            //if (keypair._key instanceof nacl.signing.SigningKey):
            return sodium.crypto_sign(signable, keypair._key.sign.privateKey, "urlsafebase64");
            //Can implement and uncomment next line if seeing problems verifying things that should verify ok - tests immediate verification
            //keypair._key.verify_key.verify(signable, nacl.encoding.URLSafeBase64Encoder.decode(sig))
        } else {
            Dweb.utils.ToBeImplementedException("signature for key =",keypair._key);
        }
    };
exports.verify = function() { console.assert(false, "XXX Undefined function CryptoLib.verify"); };
exports.b64dec = function(data) { return sodium.from_urlsafebase64(data); };    //Encode arbitrary data from b64
exports.b64enc = function(data) { return sodium.to_urlsafebase64(data);; };     //Encode arbitrary data to b64

exports.dumps = function(obj) { return JSON.stringify(obj); };   // Uses toJSON methods on objects (equivalent of dumps methods on python)
exports.loads = function(str) { return JSON.parse(str); };

exports.decryptdata = function(value, verbose) {
        /*
         Takes a dictionary that may contain { acl, encrypted } and returns the decrypted data.
         No assumption is made about what is in the decrypted data

         :param value:
         :return:
         */
        if (value.encrypted) {
            let hash = value.acl;
            let kc = Dweb.KeyChain.find(hash);  // Matching KeyChain or None
            if (kc) {
                return kc.decrypt(value.encrypted, verbose) // Exception: DecryptionFail - unlikely since publichash matches
            } else {
                //(hash, data, master, keypair, keygen, mnemonic, verbose, options)
                let acl = new Dweb.AccessControlList(hash, null, null, null, false, null, verbose);  // TODO-AUTHENTICATION probably add person - to - person version
                console.log("XXX@65 - TODO-AUTHENTICATION probably not loaded may need function to go async");
                return acl.decrypt(value.encrypted, null, verbose);
            }
        } else {
            return value;
        }
    };


exports.randomkey = function() { return sodium.randombytes_buf(sodium.crypto_secretbox_KEYBYTES); };

exports.sym_encrypt = function() { console.assert(false, "XXX Undefined function CryptoLib.sym_encrypt"); };
exports.sym_decrypt = function() { console.assert(false, "XXX Undefined function CryptoLib.sym_decrypt"); };

exports.test = function(verbose) {
     // First test some of the lower level functionality - create key etc
    if (verbose) console.log("CryptoLib.test starting");
    let qbf="The quick brown fox ran over the lazy duck";
    let key = sodium.randombytes_buf(sodium.crypto_shorthash_KEYBYTES);
    let shash_u64 = sodium.crypto_shorthash('test', key, 'urlsafebase64'); // urlsafebase64 is support added by mitra
    key = null;
    let hash_hex = sodium.crypto_generichash(32, qbf, key, 'hex'); // Try this with null as the key
    let hash_64 = sodium.crypto_generichash(32, qbf, key, 'base64'); // Try this with null as the key
    let hash_u64 = sodium.crypto_generichash(32, qbf, key, 'urlsafebase64'); // Try this with null as the key
    if (verbose) { console.log("hash_hex = ",shash_u64, hash_hex, hash_64, hash_u64); }
    if (hash_u64 !== "YOanaCqfg3UsKoqlNmVG7SFwLgDyB3aToEmLCH-vOzs=") { console.log("ERR Bad blake2 hash"); }
    let signingkey = sodium.crypto_sign_keypair();
    if (verbose) { console.log("test: SigningKey=", signingkey); }
    let seedstr = "01234567890123456789012345678901";
    let seed = sodium.from_string(seedstr);
    let boxkey = sodium.crypto_box_seed_keypair(seed);
    //FAILS - No round trip yet: if (verbose) { console.log("XXX@57 to_string=",sodium.to_string(boxkey.privateKey)); }
};
//exports = module.exports = CryptoLib;

