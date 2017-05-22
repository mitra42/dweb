const Dweb = require('./Dweb.js');
const StructuredBlock = require('./StructuredBlock.js');
const MutableBlock = require('./MutableBlock.js');
const KeyChain = require('./KeyChain.js');
const sodium = require("libsodium-wrappers");
//const sodium = require("/Users/mitra/git/mitra_libsodium.js/dist/modules/libsodium-wrappers.js");
//Uncomment to debug, check urlsafe occurs: console.log("XXX@keypair:2",sodium)

const jsdom = require("jsdom");
const { JSDOM } = jsdom;
htmlfake = '<!DOCTYPE html><ul><li id="myList.0">Failed to load sb via StructuredBlock</li><li id="myList.1">Failed to load mb via MutableBlock</li><li id="myList.2">Failed to load sb via dwebfile</li><li id="myList.3">Failed to load mb via dwebfile</li></ul>'
const dom = new JSDOM(htmlfake);
//console.log("XXX@8",dom.window.document.getElementById("myList.0").textContent); // Before loading = "Failed to load sb via StructuredBlock"
document = dom.window.document;   // Note in JS can't see "document" like can in python

const mbhash = "BLAKE2.dfMoOqTdXvqKhoZo7HPvD5raBXfgH7chXsN2PElizs8=";  // Hash reported out at tinymce.html
const mb2hash = "BLAKE2.nBWNoMyOJdhm-wrx0URYo7Utw3jG8J3boEBUcXvATVU="; // Hash reported for docs/_build/html
const sbhash="BLAKE2.spTuo7yuSJEQyYy3rUFV2G0SCDxhkZEHhQQttozxWtQ="; // This is teh hash field from any line of list/..mbhash..

function previouslyworking() {        // This was previously working in examples
    let verbose=false;
    console.log("StructuredBlock=======");
    let sb = new StructuredBlock(sbhash);
    let el = document.getElementById("myList.0");
    //console.log("el=",el);
    sb.async_load(true,
        function(msg) { sb.async_path(["langs","readme.md"], verbose,  [ "async_elem", el, verbose, null, null ], null); },
        null);
    //To debug, uncomment the el.textContent line in Transportable.async_elem
    console.log("MutableBlock=======");
    <!-- also works with /file/mb/.....=/langs/readme.md -->
    let mb = new MutableBlock(mbhash, null, false, null, false, null, null, null, verbose, null);
    mb.async_loadandfetchlist(verbose,
        function(msg) { mb.async_path(["langs","readme.md"], verbose, ["async_elem", "myList.1", verbose, null, null], null); },
        null);
    console.log("Now test path using dwebfile and sb =======");
    verbose=false;
    Dweb.async_dwebfile("sb", sbhash, "langs/readme.md", ["async_elem", "myList.2", verbose, null, null], null);
    console.log("Now test path using dwebfile and mb =======");
    Dweb.async_dwebfile("mb", mbhash, "langs/readme.md", ["async_elem", "myList.3", verbose, null, null], null);
    console.log("XXX@31 end testing");
}

function cryptotest() { //TODO-CRYPTO Still working on this
    // First test some of the lower level functionality - create key etc
    let verbose = false; // Set to true below while testing
    let qbf="The quick brown fox ran over the lazy duck";
    let key = sodium.randombytes_buf(sodium.crypto_shorthash_KEYBYTES);
    let shash_u64 = sodium.crypto_shorthash('test', key, 'urlsafebase64'); // urlsafebase64 is support added by mitra
    key = null;
    let hash_hex = sodium.crypto_generichash(32, qbf, key, 'hex'); // Try this with null as the key
    let hash_64 = sodium.crypto_generichash(32, qbf, key, 'base64'); // Try this with null as the key
    let hash_u64 = sodium.crypto_generichash(32, qbf, key, 'urlsafebase64'); // Try this with null as the key
    if (verbose) { console.log("hash_hex = ",shash_u64, hash_hex, hash_64, hash_u64); }
    if (hash_u64 !== "YOanaCqfg3UsKoqlNmVG7SFwLgDyB3aToEmLCH-vOzs=") { console.log("ERR Bad blake2 hash"); }
    let signingkey = sodium.crypto_sign_keypair();
    if (verbose) { console.log(signingkey); }
    let seedstr = "01234567890123456789012345678901";
    let seed = sodium.from_string(seedstr);
    let boxkey = sodium.crypto_box_seed_keypair(seed);
    //FAILS - No round trip yet: if (verbose) { console.log("XXX@57 to_string=",sodium.to_string(boxkey.privateKey)); }

    // Set mnemonic to value that generates seed "01234567890123456789012345678901"
    let mnemonic = "coral maze mimic half fat breeze thought champion couple muscle snack heavy gloom orchard tooth alert cram often ask hockey inform broken school cotton"; // 32 byte
    // Test sequence extracted from test.py
    let kc = KeyChain.async_new(mnemonic, false, "test_keychain kc", verbose, null, null);

    console.log("STARTING UNTESTED");
    //verbose = true;
    let mblockm = MutableBlock.async_new(kc, null, "test_keychain mblockm", true, qbf, true, verbose, null, null); //acl, contentacl, name, _allowunsafestore, content, signandstore, verbose, options
    console.log("END TESTING");
    //mbmhash = mblockm._hash
    //kc.add(mblockm, verbose=self.verbose)   # Sign and store on KC's list
}

//previouslyworking();
cryptotest();
