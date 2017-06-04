
// IPFS components
const IPFS = require('ipfs');
const CID = require('cids');

// Utility packages (ours)
const makepromises = require('./utils/makepromises')

// Other Dweb modules
const Transport = require('./Transport.js');

//Debugging only


let defaultipfsoptions = {
    repo: '/tmp/ipfs' + Math.random(), //TODO-IPFS think through where, esp for browser
    init: false,
    start: false,
    EXPERIMENTAL: {
        pubsub: true
    }
};

class TransportIPFS extends Transport {

    constructor(ipfsoptions, verbose, options) {
        super(options);
        this.ipfs = undefined;  // Not yet defined
        this.ipfsoptions = ipfsoptions; // Dictionary of options, currently unused
        this.options = options;

    }


    // This chunk starts up IPFS
    static ipfsstart(ipfsoptions) {
        let ipfs = new IPFS(ipfsoptions);
        return new Promise((resolve, reject) => {
            ipfs.version()
                .then((version) => console.log("Version=", version))
                .then((unused) => ipfs.init({emptyRepo: true, bits: 2048}))
                .then((unused) => ipfs.start())
                .then((unused) => {
                    if (ipfs.isOnline()) console.log('IPFS node is now ready and online');
                    resolve(ipfs);
                })    //TODO throw error if not online
                .catch((err) => {
                    console.log("UNCAUGHT ERROR in ipfsstart", err);
                    reject(err)
                })
        })
    }


    static setup(ipfsoptions, options) {
        let verbose = false;    //TODO check if should be in args
        let combinedipfsoptions = Object.assign(defaultipfsoptions, ipfsoptions);
        let t = new TransportIPFS(combinedipfsoptions, verbose, options);
        return new Promise((resolve, reject) => {
            TransportIPFS.ipfsstart(combinedipfsoptions)
            .then((ipfs) => {
                t.ipfs = ipfs;
                t.promisified = {ipfs:{}}
                makepromises(t.ipfs, t.promisified.ipfs, [ { block: ["put", "get"] }]); // Has to be after t.ipfs defined
                resolve(t);
            })
            .catch((err) => {
                console.log("Uncaught error in TransportIPFS.setup", err);
                reject(err);
            })
        })
    }

    static cid2link(cid) {
        //console.log("XXX@72:",cid.multihash[0],cid.multihash[1],cid.multihash[2]);
        return "/ipfs/"+cid.toBaseEncodedString()
    }  //TODO-IPFS this might not be right, (TODO-IPFS-Q)
    static link2cid(link) {
        let arr = link.split('/');
        console.assert(arr.length===3 && arr[1]==="ipfs");
        return new CID(arr[2])
    }
    async_rawfetch(self, hash, verbose, success, error) {
        // Locate and return a block, based on its multihash
        this.async_load("rawfetch", hash, verbose, success, error);
    }

//TODO-IPFS review from here down


/*
    // This chunk tests block storage
    function blocktest(message) {
    let blobtxt = 'a serialized object'
    const blob = new Buffer(blobtxt);
    let cid;    // Holds id of block stored
    return new Promise((resolve, reject) => {
        console.log("MESSAGE=",message)
        promisified.ipfs.block.put(blob)
            .then((block) => {
                //console.log(block);
                let cid = block.cid;
                //console.log("CID=",cid);
                return cid;
            })
            .then((cid) => promisified.ipfs.block.get(cid))
            .then((result) => {
                //console.log(result);
                let data = result.data.toString();
                console.log("Block Data=", data);
                resolve(data);
            })
            //.then((data) => console.assert(data === blobtxt, "Should round trip ok"))
            .catch((err) => {
                console.log("UNCAUGHT ERROR IN BLOCKTEST", err)
                reject(err)
            })
    })
    }
    */
    /*
    async_rawlist(self, hash, verbose, success, error) {
        // obj being loaded
        // Locate and return a block, based on its multihash
        // Call chain is mb.load > CL.fetchlist > THttp.rawlist > Thttp.load > CL|MB.fetchlist.success > callers.success
        console.assert(hash, "TransportHTTP.async_rawlist: requires hash");
        this.async_load("rawlist", hash, verbose, success, error);
    }
    rawreverse() { console.assert(false, "XXX Undefined function TransportHTTP.rawreverse"); }
*/
    p_rawstore(data, verbose) { // Note async_rawstore took extra "self" parameter but unued and unclear that any of
        //PY-HTTP: res = self._sendGetPost(True, "rawstore", headers={"Content-Type": "application/octet-stream"}, urlargs=[], data=data, verbose=verbose)
        console.assert(data, "TransportIPFS.p_rawstore: requires data");
        let buf;
        if (! (data instanceof Buffer)) {
            buf = new Buffer(data)
        } else {
            buf = data;
        }
        return new Promise((resolve, reject) =>
            this.promisified.ipfs.block.put(buf)
                .then((block) => { // Debugging of CID - can eliminate this clause
                    if (verbose) console.log("p_rawstore>",TransportIPFS.cid2link(block.cid));
                    //console.log("XXX@pstore data=",block.data)
                    return (TransportIPFS.cid2link(block.cid));
                })
                .then((hash) => resolve(hash))
                .catch((err) => reject(err))
        )
    }
    async_rawstore(self, data, verbose, success, error) {   //TODO-IPFS OBSOLETE this
        this.p_rawstore(data, verbose).then((hash)=>success(hash)).catch((err) => error(err))
        if (verbose) console.log("async_rawstore continuining")
    }

    /*
    async_rawadd(self, hash, date, signature, signedby, verbose, success, error) {
        verbose=true;
        console.assert(hash && signature && signedby, "async_rawadd args",hash,signature,signedby);
        if (verbose) console.log("rawadd", hash, date, signature, signedby);
        let value = TransportHTTP._add_value( hash, date, signature, signedby, verbose)+ "\n";
        //async_post(self, command, hash, type, data, verbose, success, error)
        this.async_post("rawadd", null, "application/json", value, verbose, success, error); // Returns immediately
    }

    async_update(self, hash, type, data, verbose, success, error) {
        this.async_post("update", hash, type, data, verbose, success, error);
    }
    */


    static test() {
        try {
                let transport;
                let verbose = true;
                TransportIPFS.setup()
                .then((t) => { console.log("setup returned");
                    transport = t; })
                .then(() => transport.p_rawstore("The quick brown fox", verbose))
                .then((hash) => {
                    console.log("rawstore returned", hash);
                    let newcid = TransportIPFS.link2cid(hash);
                    let newhash = TransportIPFS.cid2link(newcid);
                    console.assert(hash === newhash, "Should round trip");
                })
                .then(()=>transport.async_rawstore(null, "Ran over the lazy dog", verbose,
                    function(hash) { console.log("async_rawstore got",hash)}, null
                ))
                .catch((err) => {
                    console.log("test ERR=", err);
                    throw(err)
                });
        } catch (err) {
            console.log("Exception thrown in TransportIPFS.test", err)
        }
    }

}
exports = module.exports = TransportIPFS;

