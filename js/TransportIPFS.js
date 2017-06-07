/*
This Transport layers builds on IPFS and the IPFS-IIIF-Db,

The IPFS-IIIF-DB is more than needed, and should really strip it down, and just use the bits we need,
but its hard to figure out

Lists have listeners,
'started': for when started - then can read list - tested during IPFS start (which slows that down)
'resource inserted': for when something new posted
'mutation': triggered when changed

TODO-IPFS-MULTILIST
For now we use one list, and filter by hash, at some point we'll need lots of lists and its unclear where to split
- at listener; partition or list within that (resources / hits) or have to filter on content

*/



// Library packages other than IPFS
// IPFS components
const IPFS = require('ipfs');
const CID = require('cids');
const IIIFDB = require('ipfs-iiif-db');  //https://github.com/pgte/ipfs-iiif-db

// Utility packages (ours) Aand one-loners
const makepromises = require('./utils/makepromises');
function delay(ms, val) { return new Promise(resolve => {setTimeout(() => { resolve(val); },ms)})}
function consolearr(arr) { return (arr && arr.length >0) ? [arr.length+" items inc:", arr[-1]] : arr}

// Other Dweb modules
const Transport = require('./Transport.js');

//Debugging only



let globaltransport;  //TODO-IPFS move to use from Dweb
let globalannotationList;  //TODO-IPFS move to use from Dweb

let defaultipfsoptions = {
    repo: '/tmp/ipfs' + Math.random(), //TODO-IPFS think through where, esp for browser
    //init: false,
    //start: false,
    config: {
        Addresses: { Swarm: [ '/libp2p-webrtc-star/dns4/star-signal.cloud.ipfs.team/wss' ] },   // For IIIF - same as defaults
        Discovery: { webRTCStar: { Enabled: true } }    // For IIIF - same as defaults
    },
    EXPERIMENTAL: {
        pubsub: true
    }
};

// See https://github.com/pgte/ipfs-iiif-db for options
let iiifoptions = { ipfs: defaultipfsoptions, store: "leveldb", partition: "dweb" }; //TODO-IIIF try making parition a variable and connecting to multiple

const annotationlistexample = { //TODO-IPFS update this to better example
    "@id": "foobar",    // Only required field is @id
    "hash": "A1B2C3D4E5",
    "date": "20170104T1234",
    "signature": "123456ABC",
    "signedby": "123456ABC"
};

class TransportIPFS extends Transport {

    constructor(ipfsoptions, verbose, options) {
        super(options);
        this.ipfs = undefined;  // Not yet defined
        this.ipfsoptions = ipfsoptions; // Dictionary of options, currently unused
        this.options = options;

    }

    // This chunk starts up IPFS (old version w/o IIIF)
    static ipfsstart(ipfsoptions, verbose) {
        //let ipfs = new IPFS(ipfsoptions); // Without CRDT (for lists)
        const res = IIIFDB(iiifoptions); //Note this doesn't start either IPFS or annotationlist
        const ipfs = res.ipfs;
        let annotationList;
        return new Promise((resolve, reject) => {
            ipfs.version()
                .then((version) => console.log("Version=", version))
                //TODO-IPFS - have to disable init and start for CRDT/lists as it starts itself - will be a problem for TODO-IPFS-MULTILIST
                //.then((unused) => ipfs.init({emptyRepo: true, bits: 2048}))
                //.then((version) => console.log("initialized"))
                //.then((unused) => ipfs.start())
                .then((unused) => console.log("IPFS node",ipfs.isOnline() ? "and online" : "but offline"))    //TODO throw error if not online
                .then(() => {
                    annotationList = res.annotationList(annotationlistexample);    //TODO-IPFS move this to the list command - means splitting stuff under it that calls bootstrap
                    globalannotationList = annotationList;  //TODO-IPFS remove need for global
                    annotationList.on('started', (event) => {
                        if (verbose) { console.log("annotationList started, list at start = ", ...consolearr(annotationList.getResources())); }
                        resolve(ipfs)   // Cant resolve till annotation list online
                    });
                })
                //.then(() => resolve(ipfs))  // Whatever happens above, want to return ipfs to caller
                .catch((err) => {
                    console.log("UNCAUGHT ERROR in ipfsstart", err);
                    reject(err)
                })
        })
    }


    static setup(ipfsoptions, verbose, options) {
        let combinedipfsoptions = Object.assign(defaultipfsoptions, ipfsoptions);
        let t = new TransportIPFS(combinedipfsoptions, verbose, options);
        return new Promise((resolve, reject) => {
            TransportIPFS.ipfsstart(combinedipfsoptions, verbose)
            .then((ipfs) => {
                t.ipfs = ipfs;
                t.promisified = {ipfs:{}};
                makepromises(t.ipfs, t.promisified.ipfs, [ { block: ["put", "get"] }]); // Has to be after t.ipfs defined
                resolve(t);
            })
            .catch((err) => {
                console.log("Uncaught error in TransportIPFS.setup", err);
                reject(err);
            })
        })
    }

    // Everything else - unless documented here - should be opaque to the actual structure of a CID
    // or a Link. This code may change as its not clear (from IPFS docs) if this is the right mapping.
    static cid2link(cid) {
        //console.log("XXX@72:",cid.multihash[0],cid.multihash[1],cid.multihash[2]);
        return "/ipfs/"+cid.toBaseEncodedString()
    }  //TODO-IPFS this might not be right, (TODO-IPFS-Q)

    static link2cid(link) {
        let arr = link.split('/');
        console.assert(arr.length===3 && arr[1]==="ipfs");
        return new CID(arr[2])
    }

    p_rawfetch(hash, verbose) {
        console.assert(hash, "TransportIPFS.p_rawfetch: requires hash");
        let cid = (hash instanceof CID) ? hash : TransportIPFS.link2cid(hash);
        return this.promisified.ipfs.block.get(cid)
            .then((result)=> result.data.toString())
    }
    async_rawfetch(self, hash, verbose, success, error) {   //TODO-IPFS OBSOLETE this
        this.p_rawfetch(hash, verbose).then((data)=>success(data)).catch((err) => error(err));
        if (verbose) console.log("async_rawfetch continuining")
    }


    p_rawlist(hash, verbose) { //TODO-IPFS move initialization of annotation list here
        // obj being loaded
        // Locate and return a list, based on its multihash
        // Call chain is mb.load > CL.fetchlist > THttp.rawlist > Thttp.load > CL|MB.fetchlist.success > callers.success
        // This is coded as a p_rawlist (i.e. returning a Promise, even though it returns immediately, that is so that
        // it can be recoded for an architecture where we need to wait for the list.
        // notify is NOT part of the Python interface, needs implementing there.
        console.assert(hash, "TransportHTTP.async_rawlist: requires hash");
        return new Promise((resolve, reject) => {
            let res = globalannotationList.getResources()
                .filter((obj) => (obj.signedby === hash))
            if (verbose) console.log("p_rawlist found",...consolearr(res));
            resolve(res);
        })
    }
    listmonitor(hash, callback, verbose) {
        // Typically called immediately after a p_rawlist to get notification of future items
        //TODO-IPFS-MULTILIST will want to make more efficient.
        globalannotationList.on('resource inserted', (event) => {
            let obj = event.value;
            if (verbose) console.log('resource inserted', obj)
            //obj["signature"] = obj["@id"];
            //delete obj["@id"];
            //console.log('resource after transform', obj);
            if (callback && (obj.signedby === hash)) callback(obj);
        })
    }

    async_rawlist(self, hash, verbose, success, error) {
        //TODO-IPFS OBSOLETE this
        this.p_rawlist(hash, verbose).then((res)=>success(res)).catch((err)=>error(err));
    }

    rawreverse() { console.assert(false, "XXX Undefined function TransportHTTP.rawreverse"); }

    p_rawstore(data, verbose) { // Note async_rawstore took extra "self" parameter but unued and unclear that any of
        //PY-HTTP: res = self._sendGetPost(True, "rawstore", headers={"Content-Type": "application/octet-stream"}, urlargs=[], data=data, verbose=verbose)
        console.assert(data, "TransportIPFS.p_rawstore: requires data");
        let buf = (data instanceof Buffer) ? data : new Buffer(data);
        return this.promisified.ipfs.block.put(buf).then((block) => TransportIPFS.cid2link(block.cid));
    }
    async_rawstore(self, data, verbose, success, error) {   //TODO-IPFS OBSOLETE this
        this.p_rawstore(data, verbose).then((hash)=>success(hash)).catch((err) => error(err));
        if (verbose) console.log("async_rawstore continuining")
    }

    rawadd(hash, date, signature, signedby, verbose) {
        console.assert(hash && signature && signedby, "p_rawadd args",hash,signature,signedby);
        if (verbose) console.log("p_rawadd", hash, date, signature, signedby);
        let value = {"@id": signature, "hash": hash, "date": date, "signature": signature, "signedby": signedby};
        globalannotationList.pushResource(value);   //TODO-IPFS remove need for globalannotationList
    }
    p_rawadd(hash, date, signature, signedby, verbose) {
        return new Promise((resolve, reject)=> { try {
            this.rawadd(hash, date, signature, signedby, verbose);
            resolve(undefined);
        } catch(err) {
            reject(err);
        } })
    }
    async_rawadd(self, hash, date, signature, signedby, verbose, success, error) {
        try {
            this.rawadd(hash, date, signature, signedby, verbose);
        } catch (err) {
            console.log("async_rawadd failed", err);
            if (error) error(err);
        }
    }

    /*
    async_update(self, hash, type, data, verbose, success, error) {
        this.async_post("update", hash, type, data, verbose, success, error);
    }
    */


    static test() {
        try {
                let verbose = true;
                let hashqbf;
                let hashrold;
                let qbf = "The quick brown fox";
                let rold = "Ran over the lazy dog";
                let transport;
                let testhash = "1114";
                let listlen;    // Holds length of list run intermediate
                TransportIPFS.setup({}, verbose, {})
                .then((t) => { if (verbose) console.log("setup returned and transport set - including annoationList");
                    transport = t;
                    globaltransport = transport;    //TODO-IPFS remove need for globaltransport and globalannotationList
                })

                //.then(() => { transport.p_rawlist("UNDEFINED", verbose); console.log("XXX@200p_rawlist returned")})
                .then(() => transport.p_rawstore(qbf, verbose))
                .then((hash) => {
                    if (verbose) console.log("rawstore returned", hash);
                    let newcid = TransportIPFS.link2cid(hash);
                    let newhash = TransportIPFS.cid2link(newcid);
                    console.assert(hash === newhash, "Should round trip");
                    hashqbf = hash;
                })
                .then(()=>transport.async_rawstore(null, rold, verbose,
                    function(hash) { if (verbose) console.log("async_rawstore got",hash); hashrold=hash; }, null
                ))
                // Note above returns immediately and runs async, we don't wait for it before below
                .then(()=> transport.p_rawfetch(hashqbf, verbose))
                .then((data) => console.assert(data === qbf, "Should fetch block stored above"))
                .then(() => transport.p_rawlist(testhash, verbose))
                .then((res) => { listlen=res.length; if (verbose) console.log("rawlist returned ",...consolearr(res))})
                .then(() => transport.listmonitor(testhash, (obj)=> console.log("Monitored",obj), verbose))
                .then((res) => transport.p_rawadd("123", "TODAY", "Joe Smith", testhash, verbose))
                .then(() => { if (verbose) console.log("p_rawadd returned ")})
                .then(() => transport.p_rawlist(testhash, verbose))
                .then((res) => {if (verbose) console.log("rawlist returned ",...consolearr(res))}) // Note not showing return
                .then(() => delay(2000))
                .then(() => transport.p_rawlist(testhash, verbose))
                .then((res) => console.assert(res.length = listlen+1, "Should have added one item"))
                .then(() => console.log("delaying 10 secs"))
                .then(() => delay(10000))
                .then(() => console.log("TransportIPFS test complete"))
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
