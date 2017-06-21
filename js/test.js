const Dweb = require('./Dweb.js');
//TODO Move all these into Dweb.StructuredBlock etc
const MutableBlock = require('./MutableBlock.js');
const KeyChain = require('./KeyChain.js');
const KeyPair = require('./KeyPair.js');
const sodium = require("libsodium-wrappers");
//const sodium = require("/Users/mitra/git/mitra_libsodium.js/dist/modules/libsodium-wrappers.js");
//Uncomment to debug, check urlsafe occurs: console.log("XXX@keypair:2",sodium)

const jsdom = require("jsdom");
const { JSDOM } = jsdom;
htmlfake = '<!DOCTYPE html><ul><li id="myList.0">Failed to load sb via StructuredBlock</li><li id="myList.1">Failed to load mb via MutableBlock</li><li id="myList.2">Failed to load sb via dwebfile</li><li id="myList.3">Failed to load mb via dwebfile</li></ul>';
const dom = new JSDOM(htmlfake);
//console.log("XXX@8",dom.window.document.getElementById("myList.0").textContent); // Before loading = "Failed to load sb via StructuredBlock"
document = dom.window.document;   // Note in JS can't see "document" like can in python

const mbhash = "BLAKE2.dfMoOqTdXvqKhoZo7HPvD5raBXfgH7chXsN2PElizs8=";  // Hash reported out at tinymce.html
const mb2hash = "BLAKE2.nBWNoMyOJdhm-wrx0URYo7Utw3jG8J3boEBUcXvATVU="; // Hash reported for docs/_build/html
const sbhash="BLAKE2.spTuo7yuSJEQyYy3rUFV2G0SCDxhkZEHhQQttozxWtQ="; // This is teh hash field from any line of list/..mbhash..

function previouslyworking() {   console.trace(); console.assert(false, "OBSOLETE"); //TODO-IPFS obsolete with p_*      // This was previously working in examples
    let verbose=false;
    console.log("StructuredBlock=======");
    let sb = new Dweb.StructuredBlock(sbhash);
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
    Dweb.async_dwebfile("sb", sbhash, "langs/readme.md", ["p_elem", "myList.2", verbose, null], null);
    console.log("Now test path using dwebfile and mb =======");
    Dweb.async_dwebfile("mb", mbhash, "langs/readme.md", ["p_elem", "myList.3", verbose, null], null);
    console.log("END testing previouslyworking()");
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
    if (verbose) { console.log("test: SigningKey=", signingkey); }
    let seedstr = "01234567890123456789012345678901";
    let seed = sodium.from_string(seedstr);
    let boxkey = sodium.crypto_box_seed_keypair(seed);
    //FAILS - No round trip yet: if (verbose) { console.log("XXX@57 to_string=",sodium.to_string(boxkey.privateKey)); }

    // Set mnemonic to value that generates seed "01234567890123456789012345678901"
    let mnemonic = "coral maze mimic half fat breeze thought champion couple muscle snack heavy gloom orchard tooth alert cram often ask hockey inform broken school cotton"; // 32 byte
    // Test sequence extracted from test.py
     if (verbose) { console.log("KEYCHAIN 0 - create"); }
    let kc = KeyChain.async_new(mnemonic, false, "test_keychain kc", verbose, null, null);
    if (verbose) { console.log("KEYCHAIN 1 - add MB to KC"); }
    //verbose = true;
    let mblockm = MutableBlock.async_new(kc, null, "test_keychain mblockm", true, qbf, true, verbose, null, null); //acl, contentacl, name, _allowunsafestore, content, signandstore, verbose, options
    let mbmhash = mblockm._hash;
    kc.async_add(mblockm, verbose, null, null);   //Sign and store on KC's list (returns immediately with Sig)
    if (verbose) { console.log("KEYCHAIN 2 - add viewerkeypair to it"); }
    let vkpname="test_keychain viewerkeypair";
    //let keypair = KeyPair.keygen(Dweb.KEYPAIRKEYTYPEENCRYPT);    // TODO type getting moved to Dweb.KeyPair.KEYTYPE.ENCRYPT
    //let keypairexport = true ? keypair.privateexport() : keypair.publicexport()
    //console.log("keypairexport=",keypairexport);
    let keypairexport = "NACL SEED:w71YvVCR7Kk_lrgU2J1aGL4JMMAHnoUtyeHbqkIi2Bk="; // So same result each time
    //key = "NACL PRIVATE:c7dm7hjSK6VN-J8g3qhqpVgGCKeiUxCLh-4vezLrZEU=" // "test_viewer1_nacl.nacl"   private master
    let viewerkeypair = new KeyPair(null, {"name": vkpname, "key": keypairexport}, verbose);
    viewerkeypair._acl = kc;
    viewerkeypair.async_store(verbose); // Defaults to store private=True (which we want)
    kc.async_add(viewerkeypair, verbose, null, null);
    if (verbose) console.log("KEYCHAIN 3: Fetching mbm hash=",mbmhash);
    //MB(hash, data, master, keypair, keygen, mnemonic, contenthash, contentacl, verbose, options)
    let mbm2 = new MutableBlock(mbmhash, null, true, null, false, null, null, null, verbose, null);
    mbm2.async_load(verbose, function(msg) {
        console.assert(mbm2.name === mblockm.name, "Names should survive round trip"); }, null);
    if (verbose) console.log("KEYCHAIN 4: reconstructing KeyChain and fetch");
    Dweb.keychains = []; // Clear Key Chains
    //async_new(mnemonic, keygen, name, verbose, success, error)
    let kcs2 = KeyChain.async_new(mnemonic, null, "test_keychain kc", verbose,
        function(msg) { // Note success is run AFTER all keys have been loaded
            let mm = KeyChain.mymutableBlocks();
            if (!mm.length) {
                console.assert(mm.length, "Should find mblockm");
            }
            console.log("XXX@99",mm);
            let mbm3 = mm[mm.length - 1];
            console.assert(mbm3 instanceof MutableBlock, "Should be a mutable block", mbm3);
            console.assert(mbm3.name === mblockm.name, "Names should survive round trip");
        },
        null); // Note only fetches if name matches
    /*
    if (verbose) console.log("KEYCHAIN 5: Check can user ViewerKeyPair");
    //acl = self._makeacl()   # Create Access Control List    - dont require encrypting as pretending itssomeone else's
    // This is _makeacl() in test.py
    if (verbose) console.log("Creating AccessControlList");
    //Create a acl for testing, - full breakout is in test_keychain
    let accesskey=CryptoLibrandomkey();
    //hash, data, master, keypair, keygen, mnemonic, verbose, options
    let key = self.keyfromfile("test_acl1"+self.keytail, private=True, keytype=KeyPair.KEYTYPESIGN)
    let accesskey=CryptoLib.b64enc(accesskey);
    let acl = AccessControlList(null, {"name":"test_acl.acl", "accesskey": accesskey }, true, key, false, null, verbose, null);
    acl._allowunsafestore = True    // Not setting _acl on this
    acl.store(verbose, null, null)
    acl._allowunsafestore = False
    if (verbose) console.log("Created AccessControlList hash=", acl._hash);

     acl._allowunsafestore = True
     acl.add(viewerpublichash=viewerkeypair._hash, verbose=self.verbose)   # Add us as viewer
     sb = self._makesb(acl=acl)   # Encrypted obj
     assert KeyChain.myviewerkeys()[0].name == vkpname, "Should find viewerkeypair stored above"
     if (verbose) console.log("KEYCHAIN 6: Check can fetch and decrypt - should use viewerkeypair stored above"
     sb2 = Dweb.StructuredBlock(hash=sb._hash, verbose=self.verbose).fetch(verbose=self.verbose) # Fetch & decrypt
     assert sb2.data == self.quickbrownfox, "Data should survive round trip"
     if (verbose) console.log("KEYCHAIN 7: Check can store content via an MB"
     mblockm = MutableBlock.new(contentacl=acl, name="mblockm", _allowunsafestore=True, content=self.quickbrownfox, signandstore=True, verbose=self.verbose)  # Simulate other end
     mb = MutableBlock(name="test_acl mb", hash=mblockm._publichash, verbose=self.verbose)
     assert mb.content(verbose=self.verbose) == self.quickbrownfox, "should round trip through acl"
     if self.verbose: print "test_keychain: done"
     #TODO - named things in keychain
     #TODO - test_keychain with HTML
     */
    console.log("END TESTING");


}

//previouslyworking();
cryptotest();
