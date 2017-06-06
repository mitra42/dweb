
// IPFS components
const IPFS = require('ipfs');
const CID = require('cids');
const IIIFDB = require('ipfs-iiif-db')


// Utility packages (ours)
const makepromises = require('./utils/makepromises')

// Other Dweb modules
const Transport = require('./Transport.js');

//Debugging only


var globaltransport;  //TODO-IPFS move to use from Dweb
var globalannotationList;  //TODO-IPFS move to use from Dweb

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

let iiifoptions = { ipfs: defaultipfsoptions, store: "leveldb", partition: "iiif" }   //*Use "leveldb" for node and indexeddb (not sure how to represent)

const annotationlistexample = { //TODO-IPFS match to structure of list additios
    "@id": "foobar",    // Only required field is @id
}

class TransportIPFS extends Transport {

    constructor(ipfsoptions, verbose, options) {
        super(options);
        this.ipfs = undefined;  // Not yet defined
        this.ipfsoptions = ipfsoptions; // Dictionary of options, currently unused
        this.options = options;

    }

    // This chunk starts up IPFS (old version w/o IIIF)
    static ipfsstart(ipfsoptions) {
        //let ipfs = new IPFS(ipfsoptions); // Without CRDT (for lists)
        const res = IIIFDB(iiifoptions); //Note this doesn't start either IPFS or annotationlist
        const ipfs = res.ipfs;
        let annotationList;
        /*
        const annotationList = res.annotationList(annotationlistexample)    //TODO-IPFS move this to the list command - means splitting stuff under it that calls bootstrap
        globalannotationList = annotationList;  // TODO-IPFS remove need for global
        annotationList.on('started', (event) => {
            console.log('-------XXX-------- annotationList started', event);
            let gr = annotationList.getResources();
            console.log("GR at start = ", gr);
        })
        */
        return new Promise((resolve, reject) => {
            ipfs.version()
                .then((version) => console.log("Version=", version))
                //TODO-IPFS - may have to disable init and start for CRDT/lists
                //.then((unused) => ipfs.init({emptyRepo: true, bits: 2048}))
                //.then((version) => console.log("initialized"))
                //.then((unused) => ipfs.start())
                .then((unused) => console.log("IPFS node",ipfs.isOnline() ? "and online" : "but offline"))    //TODO throw error if not online
                .then(() => {
                    annotationList = res.annotationList(annotationlistexample);    //TODO-IPFS move this to the list command - means splitting stuff under it that calls bootstrap
                    annotationList.on('started', (event) => {
                        console.log('-------XXX-------- annotationList started', event);
                        let gr = annotationList.getResources();
                        console.log("GR at start = ", gr);
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
        let cid = (hash instanceof CID) ? hash : TransportIPFS.link2cid(hash)
        return this.promisified.ipfs.block.get(cid)
            .then((result)=> result.data.toString())
    }
    async_rawfetch(self, hash, verbose, success, error) {   //TODO-IPFS OBSOLETE this
        this.p_rawfetch(hash, verbose).then((data)=>success(data)).catch((err) => error(err))
        if (verbose) console.log("async_rawfetch continuining")
    }


     p_rawlist(hash, verbose) { //TODO-IPFS move initialization of annotation list here
     // obj being loaded
     // Locate and return a block, based on its multihash
     // Call chain is mb.load > CL.fetchlist > THttp.rawlist > Thttp.load > CL|MB.fetchlist.success > callers.success
        console.assert(hash, "TransportHTTP.async_rawlist: requires hash");
        globalannotationList.on('started', (event) => {
            console.log('annotationList started', event);
            gr = annotationList.getResources();
            console.log("GR at start = ", gr);
        })
     }

     //TODO-IPFS review from here down

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
        let buf = (data instanceof Buffer) ? data : new Buffer(data)
        return this.promisified.ipfs.block.put(buf).then((block) => TransportIPFS.cid2link(block.cid));
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
                let verbose = true;
                let hashqbf;
                let hashrold
                let qbf = "The quick brown fox"
                let rold = "Ran over the lazy dog"
                let transport
                TransportIPFS.setup()
                .then((t) => { console.log("setup returned and transport set");
                    transport = t;
                    globaltransport = transport;    //TODO-IPFS remove need for globaltransport and globalannotationList
                })

                //.then(() => { transport.p_rawlist("UNDEFINED", verbose); console.log("XXX@200p_rawlist returned")})
                .then(() => transport.p_rawstore(qbf, verbose))
                .then((hash) => {
                    console.log("rawstore returned", hash);
                    let newcid = TransportIPFS.link2cid(hash);
                    let newhash = TransportIPFS.cid2link(newcid);
                    console.assert(hash === newhash, "Should round trip");
                    hashqbf = hash;
                })
                .then(()=>transport.async_rawstore(null, rold, verbose,
                    function(hash) { console.log("async_rawstore got",hash); hashrold=hash; }, null
                ))
                // Note above returns immediately and runs async, we don't wait for it before below
                .then(()=> transport.p_rawfetch(hashqbf, verbose))
                .then((data) => {
                    console.log("rawfetch returned", data);
                    console.assert(data = qbf, "Should fetch block stored above");
                })

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

/* TODO-IPFS need this

annotationList.on('started', (event) => {
    //console.log('started', event)
    gr = annotationList.getResources();
    console.log("GR at start = ", gr);
    //console.log('annotation list now is:', annotationList.toJSON())
})
*/

/*
 annotationList.on('mutation', (event) => {
 console.log('new mutation', event)
 gr = annotationList.getResources();
 console.log("GR = ", gr);
 //console.log('annotation list now is:', annotationList.toJSON())
 })
 */

/* TODO-IPFS need this
annotationList.on('resource inserted', (event) => {
    //console.log('resource inserted', event)
    console.log("Added= ", event.value);
})
*/

/* TODO-IPFS need this in test
alnow = annotationList.getResources();
console.log("AL.resource=",alnow);

resource1 = {
    "@id": "foobar123",
    "content": "This is a test, this is only a test"
}
resource2 = {
    "@id": "foobar123",
    "content": "And this is another test"
}
annotationList.pushResource(resource1);
console.log("ANNOTATION LIST NOW:", annotationList.toJSON());

alnow = annotationList.getResources();
console.log("AL.resource=",alnow);


function delay(ms, val) { return new Promise(resolve => {setTimeout(() => { resolve(val); },ms)})}

console.log("example2_iifs_crdt.js queueing");

delay(2000,resource2).then((x) => annotationList.pushResource(resource2))
delay(2000,"Delayed 200").then((x) => console.log(x))

console.log("example2_iifs_crdt.js finishing");
*/
