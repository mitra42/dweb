const TransportHTTPBase = require('./TransportHTTPBase.js');

defaulthttpoptions = {
    ipandport: [ 'localhost',4243]
};

class TransportHTTP extends TransportHTTPBase {

    constructor(ipandport, verbose, options) {
        super(ipandport, options);
        this.options = options; // Dictionary of options, currently unused
    }


    static p_setup(httpoptions, verbose, options) {
        let combinedhttpoptions = Object.assign(defaulthttpoptions, httpoptions);
        return new Promise((resolve, reject) => {
            try {
                let t = new TransportHTTP(combinedhttpoptions.ipandport, verbose, options);
                resolve(t);
            } catch (err) {
                console.log("Exception thrown in TransportHTTP.p_setup");
                reject(err);
            }
        })
    }

    static setup(ipandport, options) {
        let verbose = false;    //TODO check if should be in args
        return new TransportHTTP(ipandport, verbose, options);
    }
    p_rawfetch(hash, verbose) {
        // Locate and return a block, based on its multihash
        return this.p_load("rawfetch", hash, verbose);
    }
    p_rawlist(hash, verbose) {
        // obj being loaded
        // Locate and return a block, based on its multihash
        // Call chain is mb.load > CL.p_fetchlist > THttp.rawlist > Thttp.load > CL|MB.p_fetchlist.success > callers.success
        console.assert(hash, "TransportHTTP.p_rawlist: requires hash");
        return this.p_load("rawlist", hash, verbose);
    }
    rawreverse() { console.assert(false, "XXX Undefined function TransportHTTP.rawreverse"); }

    p_rawstore(data, verbose) {
        //PY: res = self._sendGetPost(True, "rawstore", headers={"Content-Type": "application/octet-stream"}, urlargs=[], data=data, verbose=verbose)
        console.assert(data, "TransportHttp.p_rawstore: requires data");
        return this.p_post("rawstore", null, "application/octet-stream", data, verbose) // Returns immediately with a promise
    }

    p_rawadd(hash, date, signature, signedby, verbose) {
        //verbose=true;
        console.assert(hash && signature && signedby, "p_rawadd args",hash,signature,signedby);
        if (verbose) console.log("rawadd", hash, date, signature, signedby);
        let value = TransportHTTP._add_value( hash, date, signature, signedby, verbose)+ "\n";
        return this.p_post("rawadd", null, "application/json", value, verbose); // Returns immediately
    }

    async_update(self, hash, type, data, verbose, success, error) { console.trace(); console.assert(false, "OBSOLETE"); //TODO-IPFS obsolete with p_*
        this.async_post("update", hash, type, data, verbose, success, error);
    }

    static test() {
        return new Promise((resolve, reject)=> resolve(this));  // I think this should be a noop - fetched already
    }
}
exports = module.exports = TransportHTTP;

