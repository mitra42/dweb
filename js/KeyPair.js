const sodium = require("libsodium-wrappers");
//Uncomment to debug, check urlsafe occurs: console.log("XXX@keypair:2",sodium)
const SmartDict = require("./SmartDict");
const Dweb = require("./Dweb");

class KeyPair extends SmartDict {
    // This class is (partially) pulled from Crypto.py
    constructor(hash, data, verbose) {
        super(hash, data, verbose);    // SmartDict takes data=json or dict
        this.table = "kp";
    }

    static keygen(keytype, mnemonic, seed, verbose) {
        // keyclass parameter (from Python) not supported as only support Libsodium=NACL keys
        if (verbose) { console.log("Generating keypair"); }
        if (mnemonic) {
            //TODO Mnemonic libraries are either non-BIP39 or have node dependencies - need to rewrite one of them
            if (mnemonic === "coral maze mimic half fat breeze thought champion couple muscle snack heavy gloom orchard tooth alert cram often ask hockey inform broken school cotton") { // 32 byte
                seed = "01234567890123456789012345678901";
                console.log("Faking mnemonic encoding for now")
            } else {
                console.log("MNEMONIC STILL TO BE IMPLEMENTED");    //TODO-mnemonic
            }
        }
        let key = {};
        console.assert(sodium.crypto_box_SEEDBYTES === sodium.crypto_sign_SEEDBYTES, "KeyPair.keygen assuming seed lengths same");
        key.seed = seed || sodium.randombytes_buf(sodium.crypto_box_SEEDBYTES);
        if (keytype === Dweb.KEYPAIRKEYTYPESIGN || keytype === Dweb.KEYPAIRKEYTYPESIGNANDENCRYPT) {
            key.sign = sodium.crypto_sign_seed_keypair(key.seed); // Object { publicKey: Uint8Array[32], privateKey: Uint8Array[64], keyType: "ed25519" }
        }
        if (keytype === Dweb.KEYPAIRKEYTYPEENCRYPT || keytype === Dweb.KEYPAIRKEYTYPESIGNANDENCRYPT) {
            key.encrypt = sodium.crypto_box_seed_keypair(key.seed); // Object { publicKey: Uint8Array[32], privateKey: Uint8Array[64] } <<maybe other keyType
            // note this doesnt have the keyType field
            //console.log("XXX write this into KeyPair.js line 32", key.encrypt);
        }
        if (verbose) { console.log("key generated:",key); }
        return new KeyPair(null, {"key": key}, verbose);
    }
    __setattr__(name, value) { // Superclass SmartDict to catch "setter"s
        let verbose = false;
        if (name === "key") {
            this.key_setter(value);
        } else if (name === "private") {
            console.log("XXX Undefined function KeyPair.private.setter");
        } else if (name === "public") {
            console.log("XXX Undefined function KeyPair.public.setter");
        } else {
            super.__setattr__(name, value);
        }
    }

    key_setter(value) {
        if (typeof value === "string") {
            this._importkey(value);
        } else {
            this._key = value;
        }
    }
    preflight(dd) {
        if (this._key_has_private(dd._key) && !dd._acl && !this._allowunsafestore) {
            Dweb.SecurityWarning("Probably shouldnt be storing private key",dd);
        }
        if (dd.key) { //Based on whether the CommonList is master, rather than if the key is (key could be master, and CL not)
            dd.key = this._key_has_private(dd._key) ? this.privateexport : this.publicexport;
        }
        return super.preflight(dd)
    }


    _importkey(value) {
        //First tackle standard formats created by exporting functionality on keys
        // Call route is ... data.setter > ...> key.setter > _importkey

        //TODO - Note fingerprint different from Python - this stores the key, change the Python
        if (typeof value === "object") {    // Should be array, not dict
            for (let i in value) {
                //noinspection JSUnfilteredForInLoop
                this._importkey(value[i]);
            }
        } else {
            let arr = value.split(':',2);
            let tag = arr[0];
            let hash = arr[0];
            let seed = sodium.from_urlsafebase64(hash);
            //See https://github.com/jedisct1/libsodium.js/issues/91 for issues
            if (!this._key) { this._key = {}}   // Only handles NACL style keys
            if (tag === "NACL PUBLIC")           { console.log("XXX _importkey: Cant (yet) import Public key"+value);
            } else if (tag === "NACL PRIVATE")   { console.log("XXX _importkey: Cant (yet) import Private key"+value);
            } else if (tag === "NACL SIGNING")   { console.log("XXX _importkey: Cant (yet) import Signing key"+value);
            } else if (tag === "NACL SEED")      { console.log("XXX _importkey: Cant (yet) import Seed key"+value);
            } else if (tag === "NACL VERIFY")    {
                this._key["sign"] = {"publicKey": sodium.from_urlsafebase64(hash)};
            } else                              { console.log("XXX _importkey: Cant (yet) import "+value); }
        }
    }

    publicexport() {    // TODO probably change this on Python version as well
        let res = [];
        if (this._key.encrypt) { res.push("NACL PUBLIC:"+sodium.to_urlsafebase64(this._key.encrypt.publicKey)) }
        if (this._key.sign) { res.push("NACL VERIFY:"+sodium.to_urlsafebase64(this._key.sign.publicKey)) }
    }

    key() { console.log("XXX Undefined function KeyPair.key"); }
    private() { console.log("XXX Undefined function KeyPair.private"); }    //TODO private is a reserved word in JS
    public() { console.log("XXX Undefined function KeyPair.public"); }  //TODO public is a reserved word in JS
    mnemonic() { console.log("XXX Undefined function KeyPair.mnemonic"); }
    _exportkey() { console.log("XXX Undefined function KeyPair._exportkey"); }

    privateexport() {
        // Matches functionality in Python BUT uses NACL SEED when know seed
        let key = this._key;
        if (key.seed) {
            return "NACL SEED:" +sodium.to_urlsafebase64(key.seed);
        } else {
            console.assert(false, "XXX Undefined function KeyPair.privateexport.public", key);  //TODO should export full set of keys prob as JSON
        }
    }



    static _key_has_private(key) {
        if ((key.encrypt && key.encrypt.privateKey) || (key.sign && key.sign.privateKey) || key.seed) { return true; }
        if ((key.encrypt && key.encrypt.publicKey) || (key.sign && key.sign.publicKey)) { return false; }
        console.log("_key_hash_private doesnt recognize",key);
    }

    naclprivate() { return this._key.encrypt.privateKey; }
    naclpublic() { return this._key.encrypt.publicKey; }
    naclpublicexport() { console.log("XXX Undefined function KeyPair.naclpublicexport"); }

    has_private() {
        return KeyPair._key_has_private(this._key)
    }
    encrypt(data, b64, signer) {
        /*
         Encrypt a string, the destination string has to include any information needed by decrypt, e.g. Nonce etc

         :param data:
         :b64 bool:  Trye if want result encoded
         :signer AccessControlList or KeyPair: If want result signed (currently ignored for RSA, reqd for NACL)
         :return: str, binary encryption of data
         */
        // Assumes nacl.public.PrivateKey or nacl.signing.SigningKey
        console.assert(signer, "Until PyNaCl bindings have secretbox we require a signer and have to add authentication");
        //box = nacl.public.Box(signer.keypair.naclprivate, self.naclpublic)
        //return box.encrypt(data, encoder=(nacl.encoding.URLSafeBase64Encoder if b64 else nacl.encoding.RawEncoder))
        const nonce = sodium.randombytes_buf(sodium.crypto_box_NONCEBYTES);
        const ciphertext = sodium.crypto_box_easy(data, nonce, this.naclpublic(), signer.keypair.naclprivate(), "uint8array"); //(message, nonce, publicKey, secretKey, outputFormat)

        const combined = Dweb.utils.mergeTypedArraysUnsafe(nonce, ciphertext);
        return b64 ? sodium.to_urlsafebase64(nonce) : sodium.to_string(combined);
    }
    decrypt() { console.log("XXX Undefined function KeyPair.decrypt"); }
}

exports = module.exports = KeyPair;
