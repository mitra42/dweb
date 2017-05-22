const CryptoLib = require("./CryptoLib");

class Transport {
    //noinspection JSUnusedLocalSymbols
    constructor(verbose, options) { }
    setup() { console.log("XXX Undefined function Transport.setup"); }
    _lettertoclass() { console.log("XXX Undefined function Transport._lettertoclass"); }
    info() { console.log("XXX Undefined function Transport.info"); }
    async_rawfetch() { console.log("XXX Undefined function Transport.rawfetch"); }
    //noinspection JSUnusedGlobalSymbols
    async_fetch() { console.log("XXX Undefined function Transport.fetch"); }
    async_rawlist() { console.log("XXX Undefined function Transport.rawlist"); }
    async_list() { console.log("XXX Undefined function Transport.list"); }
    //noinspection JSUnusedGlobalSymbols
    async_rawreverse() { console.log("XXX Undefined function Transport.rawreverse"); }
    //noinspection JSUnusedGlobalSymbols
    async_reverse() { console.log("XXX Undefined function Transport.reverse"); }
    async_rawstore() { console.log("XXX Undefined function Transport.rawstore"); }
    async_store() { console.log("XXX Undefined function Transport.store"); }
    //noinspection JSUnusedLocalSymbols
    async_rawadd(hash, date, signature, signedby, verbose) { console.log("XXX Undefined function Transport.rawadd"); }

    async_add(hash, date, signature, signedby, obj, verbose, success, error) {
        if (obj && !hash) hash = obj._hash;
        return this.async_rawadd(hash, date, signature, signedby, verbose, success, error);
    }

    static _add_value(hash, date, signature, signedby, verbose) {
        let store = {"hash": hash, "date": date, "signature": signature, "signedby": signedby};
        return CryptoLib.dumps(store);
    }
}
exports = module.exports = Transport;