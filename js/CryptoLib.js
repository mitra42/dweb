//const AccessControlList = require("./AccessControlList"); // Including this for some reason makes the result unavailable, maybe a loop ?
//const KeyChain = require("./KeyChain"); // Including this for some reason makes the result unavailable, maybe a loop ?

//IPFS packages needed (none currently)

//Other packages needed
const sodium = require("libsodium-wrappers");
const crypto = require ('crypto');
const Dweb = require("./Dweb");

//CryptoLib = {}
// ==== Crypto.py - Encapsulate all the Cryptography =========
// This was the libsodium version using Blake2
//Specific to IPFS
exports.b64dec = function(data) { return sodium.from_urlsafebase64(data); };    //Encode arbitrary data from b64
exports.b64enc = function(data) { return sodium.to_urlsafebase64(data); };     //Encode arbitrary data to b64

exports.p_decryptdata = function(value, verbose) {
    /*
     Takes a
     checks if encrypted and returns immediately if not
     Otherwise if can find the ACL's hash in our KeyChain then decrypt with it.
     Else returns a promise that resolves to the data
     No assumption is made about what is in the decrypted data

     Chain is SD.p_fetch > CryptoLib.p_decryptdata > ACL.decrypt > SD.setdata

         :param value: object from parsing incoming JSON that may contain {acl, encrypted}
         :return: data or promise that resolves to data
         :errors: AuthenticationError if cant decrypt
     */
    if (! value.encrypted) {
        return value;
    } else {
        let aclhash = value.acl;
        let kc = Dweb.KeyChain.find(aclhash);  // Matching KeyChain or None
        if (kc) {
            return kc.decrypt(value.encrypted, verbose) // Exception: DecryptionFail - unlikely since publichash matches
        } else {
            //ACL(hash, data, master, keypair, keygen, mnemonic, verbose, options)
            let acl = new Dweb.AccessControlList(aclhash, null, null, null, false, null, verbose);  // TODO-AUTHENTICATION probably add person - to - person version
            return acl.p_fetch_then_list_then_elements(verbose) // Will load blocks in sig as well
                .then(() => acl.decrypt(value.encrypted, null, verbose))  // Resolves to data
                .catch((err) => { console.log("Unable to decrypt:",value); throw(err);});
        }
    }
};


exports.randomkey = function() { return sodium.randombytes_buf(sodium.crypto_secretbox_KEYBYTES); };

exports.sym_encrypt = function(data, sym_key, b64) {
    // May need to handle different forms of sym_key for now assume urlbase64 encoded string
    sym_key = sodium.from_urlsafebase64(sym_key);
    const nonce = sodium.randombytes_buf(sodium.crypto_secretbox_NONCEBYTES);
    const ciphertext = sodium.crypto_secretbox_easy(data, nonce, sym_key, "uint8array");  // message, nonce, key, outputFormat
    const combined = Dweb.utils.mergeTypedArraysUnsafe(nonce, ciphertext);
    return b64 ? sodium.to_urlsafebase64(combined) : sodium.to_string(combined);
};



exports.sym_decrypt = function(data, sym_key, outputformat) {
//        sodium.crypto_secretbox_open_easy(data, nonce, key, outputFormat)
    console.assert(data, "Cryptolib.sym_decrypt: meaningless to decrypt undefined, null or empty strings");
    // Note may need to convert data from unicode to str
    if (typeof(data) === "string") {   // If its a string turn into a Uint8Array
        data = sodium.from_urlsafebase64(data);
    }
    let nonce = data.slice(0,sodium.crypto_box_NONCEBYTES);
    data = data.slice(sodium.crypto_box_NONCEBYTES);
    return sodium.crypto_secretbox_open_easy(data, nonce, sym_key, outputformat);
};

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

