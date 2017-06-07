//const AccessControlList = require("./AccessControlList"); // Including this for some reason makes the result unavailable, maybe a loop ?
//const KeyChain = require("./KeyChain"); // Including this for some reason makes the result unavailable, maybe a loop ?
//TODO-IPFS gradually uncomment file as required

//IPFS packages needed
const multihashes = require('multihashes');

/*TODO-IPFS
const sodium = require("libsodium-wrappers");
const Dweb = require("./Dweb");
*/
const crypto = require ('crypto')

CryptoLib = {}
// ==== Crypto.py - Encapsulate all the Cryptography =========
// This was the libsodium version using Blake2
//CryptoLib.Curlhash = function(data) { return "BLAKE2."+ sodium.crypto_generichash(32, data, null, 'urlsafebase64'); }
//Specific to IPFS
CryptoLib.Curlhash = function(data) {
    let b2 = (data instanceof Buffer) ? data : new Buffer(data);
    let b3 = crypto.createHash('sha256').update(b2).digest();
    hash = multihashes.toB58String(multihashes.encode(b3, 'sha2-256'));  //TODO-IPFS-Q unclear how to make generic
    return "/ipfs/"+hash
}
/*TODO-IPFS
CryptoLib._signable = function(date, data) {
        /*
         Returns a string suitable for signing and dating, current implementation includes date and storage hash of data.
         Called by signature, so that same thing signed as compared

         :param date: Date on which it was signed
         :param data: Storage hash of data signed (as returned by Transport layer) - will convert to str if its unicode
         :return: Signable or comparable string
         COPIED TO JS 2017-05-23
         *-/
        return date.toISOString() + data;
    }

CryptoLib.signature = function(keypair, date, hash, verbose) {
        /*
        Pair of verify(), signs date and data using public key function.

        :param keypair: Key that be used for signature
        :param date: Date that signing (usually now)
        :return: signature that can be verified with verify
        COPIED FROM PYTHON 2017-05-23 excluding RSA and WordHashKey support
        *-/
        let signable = CryptoLib._signable(date, hash); // A string we can sign
        if (keypair._key.sign.privateKey) {
            //if (keypair._key instanceof nacl.signing.SigningKey):
            return sodium.crypto_sign(signable, keypair._key.sign.privateKey, "urlsafebase64");
            //Can implement and uncomment next line if seeing problems verifying things that should verify ok - tests immediate verification
            //keypair._key.verify_key.verify(signable, nacl.encoding.URLSafeBase64Encoder.decode(sig))
        } else {
            Dweb.utils.ToBeImplementedException("signature for key =",keypair._key);
        }
    }
CryptoLib.verify = function() { console.assert(false, "XXX Undefined function CryptoLib.verify"); }
CryptoLib.b64dec = function() { console.assert(false, "XXX Undefined function CryptoLib.b64dec"); }
CryptoLib.b64enc = function() { console.assert(false, "XXX Undefined function CryptoLib.b64enc"); }

CryptoLib.dumps = function(obj) { return JSON.stringify(obj); }   // Uses toJSON methods on objects (equivalent of dumps methods on python)
CryptoLib.loads = function(str) { return JSON.parse(str); }

CryptoLib.decryptdata = function(value, verbose) {
        /*
         Takes a dictionary that may contain { acl, encrypted } and returns the decrypted data.
         No assumption is made about what is in the decrypted data

         :param value:
         :return:
         *-/
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
    }


CryptoLib.randomkey = function() { console.assert(false, "XXX Undefined function CryptoLib.randomkey"); }
CryptoLib.sym_encrypt = function() { console.assert(false, "XXX Undefined function CryptoLib.sym_encrypt"); }
CryptoLib.sym_decrypt = function() { console.assert(false, "XXX Undefined function CryptoLib.sym_decrypt"); }
*/ //TODO-IPFS end of section to work through
exports = module.exports = CryptoLib;

