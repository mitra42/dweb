const TransportHTTPBase = require('./TransportHTTPBase.js');
//TODO-IPFS rewrite as promises

class TransportHTTP extends TransportHTTPBase {

    constructor(ipandport, verbose, options) {
        super(ipandport, options);
        this.options = options; // Dictionary of options, currently unused
    }

    static setup(ipandport, options) {
        let verbose = false;    //TODO check if should be in args
        return new TransportHTTP(ipandport, verbose, options);
    }
    async_rawfetch(self, hash, verbose, success, error) { console.trace(); console.assert(false, "OBSOLETE"); //TODO-IPFS obsolete with p_*   //TODO merge with transport.list
        // Locate and return a block, based on its multihash
        this.async_load("rawfetch", hash, verbose, success, error);
    }
    async_rawlist(self, hash, verbose, success, error) {  console.trace(); console.assert(false, "OBSOLETE"); //TODO-IPFS obsolete with p_*
        // obj being loaded
        // Locate and return a block, based on its multihash
        // Call chain is mb.load > CL.fetchlist > THttp.rawlist > Thttp.load > CL|MB.fetchlist.success > callers.success
        console.assert(hash, "TransportHTTP.async_rawlist: requires hash");
        this.async_load("rawlist", hash, verbose, success, error);
    }
    rawreverse() { console.assert(false, "XXX Undefined function TransportHTTP.rawreverse"); }

    async_rawstore(self, data, verbose, success, error) { console.trace(); console.assert(false, "OBSOLETE"); //TODO-IPFS obsolete with p_*
        //PY: res = self._sendGetPost(True, "rawstore", headers={"Content-Type": "application/octet-stream"}, urlargs=[], data=data, verbose=verbose)
        console.assert(data, "TransportHttp.async_rawstore: requires data");
        this.async_post("rawstore", null, "application/octet-stream", data, verbose, success, error) // Returns immediately
    }

    async_rawadd(self, hash, date, signature, signedby, verbose, success, error) { console.trace(); console.assert(false, "OBSOLETE"); //TODO-IPFS obsolete with p_*
        verbose=true;
        console.assert(hash && signature && signedby, "async_rawadd args",hash,signature,signedby);
        if (verbose) console.log("rawadd", hash, date, signature, signedby);
        let value = TransportHTTP._add_value( hash, date, signature, signedby, verbose)+ "\n";
        //async_post(self, command, hash, type, data, verbose, success, error)
        this.async_post("rawadd", null, "application/json", value, verbose, success, error); // Returns immediately
    }

    async_update(self, hash, type, data, verbose, success, error) { console.trace(); console.assert(false, "OBSOLETE"); //TODO-IPFS obsolete with p_*
        this.async_post("update", hash, type, data, verbose, success, error);
    }
}
exports = module.exports = TransportHTTP;

