const CryptoLib = require("./CryptoLib");

class Transport {
    //noinspection JSUnusedLocalSymbols
    constructor(verbose, options) { }
    setup() { console.assert(false, "XXX Undefined function Transport.setup"); }
    _lettertoclass() { console.assert(false, "XXX Undefined function Transport._lettertoclass"); }
    info() { console.assert(false, "XXX Undefined function Transport.info"); }
    async_rawfetch() { console.assert(false, "XXX Undefined function Transport.rawfetch"); }
    //noinspection JSUnusedGlobalSymbols
    async_fetch() { console.assert(false, "XXX Undefined function Transport.fetch"); }
    async_rawlist() { console.assert(false, "XXX Undefined function Transport.rawlist"); }
    async_list() { console.assert(false, "XXX Undefined function Transport.list"); }
    //noinspection JSUnusedGlobalSymbols
    async_rawreverse() { console.assert(false, "XXX Undefined function Transport.rawreverse"); }
    //noinspection JSUnusedGlobalSymbols
    async_reverse() { console.assert(false, "XXX Undefined function Transport.reverse"); }
    async_rawstore() { console.assert(false, "XXX Undefined function Transport.rawstore"); }
    async_store() { console.assert(false, "XXX Undefined function Transport.store"); }
    //noinspection JSUnusedLocalSymbols
    async_rawadd(hash, date, signature, signedby, verbose) { console.assert(false, "XXX Undefined function Transport.rawadd"); }

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