const CryptoLib = require("./CryptoLib");

class Transport {
    //noinspection JSUnusedLocalSymbols
    constructor(verbose, options) { }
    setup() { console.assert(false, "XXX Undefined function Transport.setup"); }
    _lettertoclass() { console.assert(false, "XXX Undefined function Transport._lettertoclass"); }
    info() { console.assert(false, "XXX Undefined function Transport.info"); }
    p_rawfetch() { console.assert(false, "XXX Undefined function Transport.rawfetch"); }
    //noinspection JSUnusedGlobalSymbols
    p_fetch() { console.assert(false, "XXX Undefined function Transport.fetch"); }
    p_rawlist() { console.assert(false, "XXX Undefined function Transport.rawlist"); }
    p_list() { console.assert(false, "XXX Undefined function Transport.list"); }
    //noinspection JSUnusedGlobalSymbols
    p_rawreverse() { console.assert(false, "XXX Undefined function Transport.rawreverse"); }
    //noinspection JSUnusedGlobalSymbols
    p_reverse() { console.assert(false, "XXX Undefined function Transport.reverse"); }
    p_rawstore() { console.assert(false, "XXX Undefined function Transport.rawstore"); }
    p_store() { console.assert(false, "XXX Undefined function Transport.store"); }
    //noinspection JSUnusedLocalSymbols
    p_rawadd(hash, date, signature, signedby, verbose) { console.assert(false, "XXX Undefined function Transport.rawadd"); }

    p_add(hash, date, signature, signedby, obj, verbose) {
        if (obj && !hash) hash = obj._hash;
        console.assert(signedby && signature && hash, "p_add: Meaningless request");
        return this.p_rawadd(hash, date, signature, signedby, verbose);
    }

    static _add_value(hash, date, signature, signedby, verbose) {
        let store = {"hash": hash, "date": date, "signature": signature, "signedby": signedby};
        return CryptoLib.dumps(store);
    }
}
exports = module.exports = Transport;