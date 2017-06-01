/*
    This is an attempt to get something - anything - working on the CRDT/IIIF/Y space
    so that can then start pulling it apart to an example that is NOT dependent on IIIF

    After trying to copy the example fro ipfs-iiif-db failed (calls indexdb even when running node) trying to
    follow the login in the documentation at in https://github.com/pgte/ipfs-iiif-db

*/

const DB = require('ipfs-iiif-db')
console.log("example2_iifs_crdt.js starting")


function repoPath () {
    // TODO: shouldnt need a new repo on every instance
    return '/tmp/ipfs-y/' + Math.random()
}

const ipfsOptions = {
    repo: repoPath(),
    config: {
        Addresses: {
            Swarm: [
                '/libp2p-webrtc-star/dns4/star-signal.cloud.ipfs.team/wss'
            ]
        },
        Discovery: {
            webRTCStar: {
                Enabled: true
            }
        }
    },
    EXPERIMENTAL: {
        pubsub: true
    }
}
options = { ipfs: ipfsOptions, store: "leveldb", partion: "iiif" }
const db = DB(options);

// Get an anotations object
//TODO see how much of this originalAnnotationList is required
originalAnnotationListExample = {
    "@context": "http://iiif.io/api/search/0/context.json",
        "@id": "https://wellcomelibrary.org/annoservices/search/b18035723?q=gene",
        "@type": "sc:AnnotationList",
        "within": {
        "@type": "sc:Layer",
            "total": 80
    },
    "startIndex": 0
}
OALSimple = {
    "@id": "foobar"
}
const annotationList = db.annotationList(originalAnnotationListExample)



annotationList.on('started', (event) => {
    //console.log('started', event)
    gr = annotationList.getResources();
    console.log("GR at start = ", gr);
    //console.log('annotation list now is:', annotationList.toJSON())
})

/*
annotationList.on('mutation', (event) => {
    console.log('new mutation', event)
    gr = annotationList.getResources();
    console.log("GR = ", gr);
    //console.log('annotation list now is:', annotationList.toJSON())
})
*/

annotationList.on('resource inserted', (event) => {
    //console.log('resource inserted', event)
    console.log("Added= ", event.value);
})


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

