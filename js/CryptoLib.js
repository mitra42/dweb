const sodium = require("libsodium-wrappers");
const Dweb = require("./Dweb");

// ==== Crypto.py - Encapsulate all the Cryptography =========
class CryptoLib {
    static Curlhash(data) { return "BLAKE2."+ sodium.crypto_generichash(32, data, null, 'urlsafebase64'); }

    static _signable(date, data) {
        /*
         Returns a string suitable for signing and dating, current implementation includes date and storage hash of data.
         Called by signature, so that same thing signed as compared

         :param date: Date on which it was signed
         :param data: Storage hash of data signed (as returned by Transport layer) - will convert to str if its unicode
         :return: Signable or comparable string
         COPIED TO JS 2017-05-23
         */
        return date.toISOString() + data;
    }

    static signature(keypair, date, hash, verbose) {
        /*
        Pair of verify(), signs date and data using public key function.

        :param keypair: Key that be used for signature
        :param date: Date that signing (usually now)
        :return: signature that can be verified with verify
        COPIED FROM PYTHON 2017-05-23 excluding RSA and WordHashKey support
        */
        let signable = CryptoLib._signable(date, hash); // A string we can sign
        if (keypair._key.sign.privateKey) {
            //if (keypair._key instanceof nacl.signing.SigningKey):
            return sodium.crypto_sign(signable, keypair._key.sign.privateKey, "urlsafebase64");
            //Can implement and uncomment next line if seeing problems verifying things that should verify ok - tests immediate verification
            //keypair._key.verify_key.verify(signable, nacl.encoding.URLSafeBase64Encoder.decode(sig))
        } else {
            //console.log("XXX@CryptoLib.signature write test for this key", keypair._key)
            Dweb.utils.ToBeImplementedException("signature for key =",keypair._key);
        }
    }
    static verify() { console.assert(false, "XXX Undefined function CryptoLib.verify"); }
    static b64dec() { console.assert(false, "XXX Undefined function CryptoLib.b64dec"); }
    static b64enc() { console.assert(false, "XXX Undefined function CryptoLib.b64enc"); }

    static dumps(obj) { return JSON.stringify(obj); }   // Uses toJSON methods on objects (equivalent of dumps methods on python)

    static decryptdata() { console.assert(false, "XXX Undefined function CryptoLib.decryptdata"); }
    static randomkey() { console.assert(false, "XXX Undefined function CryptoLib.randomkey"); }
    static sym_encrypt() { console.assert(false, "XXX Undefined function CryptoLib.sym_encrypt"); }
    static sym_decrypt() { console.assert(false, "XXX Undefined function CryptoLib.sym_decrypt"); }
}

exports = module.exports = CryptoLib;

