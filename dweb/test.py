# encoding: utf-8
from datetime import datetime
import unittest
import os
from pathlib2 import Path
from json import loads, dumps
import base64
from Crypto.PublicKey import RSA

from misc import _print
from CryptoLib import CryptoLib, KeyPair
from Transport import TransportBlockNotFound, TransportURLNotFound, TransportFileNotFound
from TransportLocal import TransportLocal
from TransportHTTP import TransportHTTP
from CommonBlock import Transportable
from Block import Block
from StructuredBlock import StructuredBlock
from MutableBlock import CommonList, MutableBlock, AccessControlList, KeyChain
from File import File, Dir
from Dweb import Dweb


class Testing(unittest.TestCase):
    def setUp(self):
        super(Testing, self).setUp()
        testTransport = TransportHTTP  # Can switch between TransportLocal and TransportHTTP to test both
        self.verbose=False
        self.quickbrownfox =  "The quick brown fox ran over the lazy duck"
        self.dog = "But the clever dog chased the fox"
        self.mydic = { "a": "AAA", "1":100, "B_date": datetime.now()}  # Dic can't contain integer field names
        self.ipandport = ('localhost',4243)  # Serve it via HTTP on all addresses
        #self.ipandport = ('192.168.1.156',4243)  # Serve it via HTTP on all addresses
        self.exampledir = "../examples/"    # Where example files placed
        self.mnemonic = "lecture name virus model jealous whisper stone broom harvest april notable lunch" # Random valid mnemonic
        if testTransport == TransportLocal:
            Dweb.settransport(transportclass=TransportLocal, verbose=self.verbose, dir="../cache")
        elif testTransport == TransportHTTP:
            # Run python -m ServerHTTP; before this
            Dweb.settransport(transportclass=TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        else:
            assert False, "Unimplemented test for Transport "+testTransport.__class__.__name__

    def tearDown(self):
        super(Testing, self).tearDown()

    def keyfromfile(self, keyname, private=False):
        """
        Load a key from a file, if file doesnt exist then create it with a new randome key.
        Note that in normal testing, the file will be created when the test is run first, then that key file will end up in git so will be same on all machines.
        """
        keypath = self.exampledir + keyname
        if not os.path.exists(keypath):
            keypair = KeyPair.keygen()
            File._write(filepath=keypath, data=keypair.privateexport if private else keypair.publicexport)
        return File.load(filepath=keypath).content()

    # ======== STANDARD CREATION ROUTINES
    def _acl(self): # See test_keychain for use and canonical testing
        if self.verbose: print "Creating AccessControlList"
        # Create a acl for testing, - full breakout is in test_acl
        accesskey=CryptoLib.randomkey()
        acl = AccessControlList(name="test_acl.acl", master=True, keypair=self.keyfromfile("test_acl1_rsa", private=True),
                                accesskey=base64.urlsafe_b64encode(accesskey), verbose=self.verbose)
        acl._allowunsafestore = True    # Not setting _acl on this
        acl.store(verbose=self.verbose)
        acl._allowunsafestore = False
        if self.verbose: print "Creating AccessControlList hash=", acl._hash
        return acl

    def _sb(self, acl=None):    # See test_structuredblock for canonical testing of this
        if self.verbose: print "Create Structured Block"
        sb = StructuredBlock()
        sb.name = "test _sb"
        sb.data = self.quickbrownfox
        sb._acl = acl
        sb.store(verbose=self.verbose)  # Automatically encrypts based on ACL
        if self.verbose: print "Created Structured Block hash=",sb._hash
        return sb

    # ======== END OF STANDARD CREATION ROUTINES


    def test_Block(self):
        hash = Block(data=self.quickbrownfox).store(verbose=self.verbose)._hash
        block = Block(hash=hash, verbose=self.verbose).fetch(verbose=self.verbose)
        assert block._data == self.quickbrownfox, "Should return data stored"

    def test_StructuredBlock(self):
        # Test Structured block
        sb = StructuredBlock(data=CryptoLib.dumps(self.mydic), verbose=self.verbose)
        assert sb.a == self.mydic['a'], "Testing attribute access"
        multihash = sb.store(verbose=self.verbose)._hash
        sb2 = StructuredBlock(hash=multihash, verbose=self.verbose)
        sb2.fetch(verbose=self.verbose)
        assert sb2.a == self.mydic['a'], "Testing StructuredBlock round-trip"
        assert sb2.B_date == self.mydic["B_date"], "DateTime should survive round trip"

    def test_Signatures(self):
        # Test Signatures
        #self.verbose=True
        signedblock = StructuredBlock(data=self.mydic)
        keypair = KeyPair.keygen()
        # This test should really fail, BUT since keypair has private it passes signature
        #commonlist0 = CommonList(keypair=keypair, master=False)
        #print commonlist0
        #signedblock.sign(commonlist0, verbose=self.verbose) # This should fail, but
        if self.verbose: print "test_Signatures CommonLost"
        CommonList.table = "BOGUS"  # Defeat errors
        commonlist = CommonList(keypair=keypair, keygen=RSA, master=True, name="test_Signatures.commonlist")
        if self.verbose: print "test_Signatures sign"
        commonlist._allowunsafestore = True
        signedblock.sign(commonlist, verbose=self.verbose)
        commonlist._allowunsafestore = False
        if self.verbose: print "test_Signatures verification"
        assert signedblock.verify(verify_atleastone=True, verbose=self.verbose), "Should verify"
        signedblock.a="A++"
        signedblock.dirty()
        assert not signedblock.verify(verify_atleastone=True, verbose=self.verbose), "Should fail"

    def test_MutableBlocks(self):
        #self.verbose=True
        if self.verbose: print "test_MutableBlocks: Create master"
        mblockm = MutableBlock(master=True, keygen=RSA, verbose=self.verbose)      # Create a new block with a new key
        mblockm._current.data = self.quickbrownfox                       # Put some data in it (goes in the StructuredBlock at _current
        mblockm._allowunsafestore = True                        # Avoid dependency on ACL and encryption in this test
        mblockm.signandstore(verbose=self.verbose)              # Sign it - this publishes it
        mblockm._allowunsafestore = False
        testhash0 = mblockm._current._hash                      # Get a pointer to that version
        if self.verbose: print "test_MutableBlocks: Edit it"
        mblockm._current.data = self.dog                        # Put some different content in it
        mblockm._current.dirty()                                # Have to manually "dirty" it since already written
        mblockm._allowunsafestore = True                        # Avoid dependency on ACL and encryption in this test
        mblockm.signandstore(verbose=self.verbose)              # Publish new content
        mblockm.store()
        mblockm._allowunsafestore = False
        testhash = mblockm._current._hash                       # Get a pointer to the new version
        mbmpubhash = mblockm._publichash
        #keyhash = mblockm.keypair.store().publichash           # Get the publickey pointer to the block
        if self.verbose: print "test_MutableBlocks: And check it"
        mblock = MutableBlock(hash=mbmpubhash, verbose=self.verbose)                     # Setup a copy (not Master) via the publickey
        mblock.fetch(verbose=self.verbose)                      # Fetch the content
        assert mblock._current._hash == testhash, "Should match hash stored above"
        assert mblock._list[0].hash == testhash0, "Prev list should hold first stored"

    def test_LongFiles(self):
        from StructuredBlock import StructuredBlock
        sb1 = StructuredBlock({ "data": self.quickbrownfox}) # Note this is data held in the SB, as compared to _data which is data representing the SB
        assert sb1.size(verbose=self.verbose) == len(self.quickbrownfox), "Should get length"
        assert sb1.content(verbose=self.verbose) == self.quickbrownfox, "Should fetch string"
        multihash = Block(data=self.dog).store(verbose=self.verbose)._hash
        sb2 = StructuredBlock({ "hash": multihash})  # Note passing multihash as the hash of the data, not the hash of the SB.
        assert sb2.content(verbose=self.verbose) == self.dog, "Should fetch dog string"
        assert sb2.size(verbose=self.verbose) == len(self.dog), "Should get length"
        slinksblock = StructuredBlock({ "links": [
                                            StructuredBlock({ "data": self.quickbrownfox}),
                                            StructuredBlock({ "hash": multihash}),
                                        ]})
        assert slinksblock.content(verbose=self.verbose) == self.quickbrownfox+self.dog, "Should get concatenation"
        assert slinksblock.size(verbose=self.verbose) == len(self.quickbrownfox)+len(self.dog), "Should get length"

    def test_http(self):
        # Run python -m ServerHTTP; before this
        Dweb.settransport(transportclass=TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        multihash = Block(data=self.quickbrownfox).store(verbose=self.verbose)._hash
        block = Block(hash=multihash, verbose=self.verbose).fetch(verbose=self.verbose)
        assert block._data == self.quickbrownfox, "Should return data stored"

    def test_file(self):
        #self.verbose=True
        Dweb.settransport(transportclass=TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        content = File.load(filepath=self.exampledir + "index.html", verbose=self.verbose).content(verbose=self.verbose)
        sb = StructuredBlock(**{"Content-type":"text/html"})  # ** because cant use args with hyphens\
        sb.data = content
        sb.store()
        sburl = sb.url(command="file", url_output="getpost")
        assert sburl == [False, "file", ["sb", sb._hash]]
        resp = Dweb.transport._sendGetPost(sburl[0], sburl[1], sburl[2], verbose=False)
        assert resp.text == content, "Should return data stored"
        assert resp.headers["Content-type"] == "text/html", "Should get type"
        # Now test a MutableBlock that uses this content
        mbm = MutableBlock(master=True, keypair=self.keyfromfile("index_html_rsa", private=True), contenthash=sb._hash)
        mbm._allowunsafestore = True
        mbm.store().signandstore(verbose=self.verbose)
        mbm._allowunsafestore = False
        if self.verbose: print "store tells us:", mbm.content()
        assert mbm.content()==content, "Should match content stored"
        mb = MutableBlock(hash=mbm._publichash)
        mb.fetch()      # Just fetches the signatures
        assert mb.content() == mbm.content(), "Should round-trip HTML content"
        getpostargs=mb.url(command="file", url_output="getpost")
        mbcontent2 = Dweb.transport._sendGetPost(*getpostargs).text
        assert mbcontent2 == mbm.content(), "Should fetch MB content via its URL"

    def test_typeoverride(self):    # See if can override the type on a block
        Dweb.settransport(transportclass=TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        # Store the wrench icon
        content = File.load(filepath=self.exampledir + "WrenchIcon.png").content()
        wrenchhash = Block(data=content).store(verbose=self.verbose)._hash
        # And check it got there
        resp = Dweb.transport._sendGetPost(False, "rawfetch",  [wrenchhash], params={"contenttype": "image/png"})
        assert resp.headers["Content-type"] == "image/png", "Should get type"
        assert resp.content == content, "Should return data stored"
        resp = Dweb.transport._sendGetPost(False, "file",  ["b", wrenchhash], params={"contenttype": "image/png"})
        assert resp.headers["Content-type"] == "image/png", "Should get type"
        assert resp.content == content, "Should return data stored"

    def test_badblock(self):
        Dweb.settransport(transportclass=TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        try:
            resp = Dweb.transport._sendGetPost(False, "rawfetch", [ "12345"], params={"contenttype": "image/png"})
        except TransportURLNotFound as e:
            pass
        else:
            assert False, "Should raise a TransportURLNotFound error"

    def _storeas(self, filename, keyname, contenttype, **options):
        filepath = self.exampledir + filename
        if os.path.isdir(filepath):
            f = Dir.load(filepath=filepath, upload=True, verbose=self.verbose, option=options)
        else:
            f = File.load(filepath=filepath, contenttype=contenttype, upload=True, verbose=self.verbose, **options)
        if self.verbose: print f
        keypath = self.exampledir + keyname if keyname else None
        if keypath:
            mbm = MutableBlock(master=True, keypair=self.keyfromfile(keyname, private=True), contenthash=f._hash, verbose=self.verbose)
            mbm._allowunsafestore = True    # TODO could encrypt these
            mbm.store(private=True, verbose=self.verbose)
            mbm.signandstore(verbose=self.verbose)
            mbm._allowunsafestore = False
            print filename + " editable:" + mbm.privateurl()    # Side effect of storing
            print filename + ":" + mbm.publicurl(command="file", table="mb")
        else:
            print filename + ":" + f.url(command="file", table="sb")


    def test_uploads(self):
        # A set of tools to upload things so available for testing.
        # All the functionality in storeas should have been tested elsewhere.
        Dweb.settransport(transportclass=TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        b=Block(data=self.dog); b.store(); print self.dog,b.url()
        self._storeas("dweb.js", "dweb_js_rsa", "application/javascript")
        self._storeas("jquery-3.1.1.js", None, "application/javascript")
        self._storeas("index.html", "index_html_rsa", "text/html")
        self._storeas("test.html", "test_html_rsa", "text/html")
        self._storeas("snippet.html", "snippet_html_rsa", "text/html")
        self._storeas("snippet2.html", "snippet_html_rsa", "text/html")
        self._storeas("WrenchIcon.png", None, "image/png")
        self._storeas("DWebArchitecture.png", "DwebArchitecture_png_rsa","image/png")
        self._storeas("../tinymce", "tinymce_rsa", None)
        self._storeas("../docs/_build/html", "docs_build_html_rsa", None)
        self._storeas("objbrowser.html", "objbrowser_html_rsa", "text/html")

    def test_uploadandrelativepaths(self):
        # Test that a directory can be uploaded and then accessed by a relative path
        Dweb.settransport(transportclass=TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        f1sz = File.load("../tinymce/langs/readme.md").size
        # Upload a multi-level directory
        f = Dir.load(filepath="../tinymce", upload=True, verbose=self.verbose,)
        #print f.url()  # url of sb at top of directory
        sb = StructuredBlock(hash=f._hash, verbose=self.verbose).fetch(verbose=self.verbose)
        assert len(sb.links) == 7, "tinymce should have 7 files but has "+str(len(sb.links))
        resp = Dweb.transport._sendGetPost(False, "file", ["sb", f._hash,"langs/readme.md"])
        assert int(resp.headers["Content-Length"]) == f1sz,"Should match length of readme.md"
        # /file/mb/SHA3256B64URL.88S-FYlEN1iF3WuDRdXoR8SyMUG6crR5ehM21IvUuS0=/tinymce.min.js

    def test_crypto(self):
        if self.verbose: print "test_crypto: tests of the crypto library - esp round trips through functions"
        # Try symetric encrypt/decrypt
        aeskey = CryptoLib.randomkey()
        enc = CryptoLib.sym_encrypt(self.quickbrownfox, aeskey)
        dec = CryptoLib.sym_decrypt(enc, aeskey)
        assert dec == self.quickbrownfox
        # Try RSA encrypt/decrypt
        keypair = KeyPair.keygen()
        enc = keypair.encrypt(self.quickbrownfox)
        dec = keypair.decrypt(enc)
        assert dec == self.quickbrownfox

    def test_keychain(self): # TODO rename test_keychain
        """
        This is a supercomplex test, that effectively tests a lot of subsystems including AccessControlLists, KeyChains and encryption in transport
        """
        #self.verbose=True
        if self.verbose: print "KEYCHAIN 0 - create"
        kc = KeyChain(mnemonic=self.mnemonic, verbose=self.verbose, name="test_keychain kc").store(verbose=self.verbose)
        KeyChain.addkeychains(kc)
        if self.verbose: print "KEYCHAIN 1 - add mbm to it"
        mblockm = MutableBlock.new(name="test_keychain mblockm", acl=kc, content=self.quickbrownfox, _allowunsafestore=True, signandstore=True, verbose=self.verbose)
        mbmhash = mblockm._hash
        kc.add(mblockm, verbose=self.verbose)   # Sign and store on KC's list
        if self.verbose: print "KEYCHAIN 2 - add viewerkeypair to it"
        vkpname="test_keychain viewerkeypair"
        viewerkeypair = KeyPair(name=vkpname, key=self.keyfromfile("test_viewer1_rsa", private=True))
        viewerkeypair._acl = kc
        viewerkeypair.store(verbose=self.verbose) # Defaults to store private=False
        kc.add(viewerkeypair, verbose=self.verbose)
        if self.verbose: print "KEYCHAIN 3: Fetching mbm hash=",mbmhash
        mbm2 = MutableBlock(hash=mbmhash, master=True, verbose=self.verbose, name="test_keychain mbm2")
        mbm2.fetch(verbose=self.verbose)
        assert mbm2.name == mblockm.name, "Names should survive round trip"
        if self.verbose: print "KEYCHAIN 4: reconstructing KeyChain and fetch"
        Dweb.keychains = [] # Clear Key Chains
        kcs2 = KeyChain.new(mnemonic=self.mnemonic, verbose=self.verbose, name="test_keychain kc") # Note only fetches if name matches
        if self.verbose: print "KEYCHAIN 5: Check MBM carried ok"
        mbm3 = kcs2.mymutableBlocks()[-1]
        assert mbm3.__class__.__name__ == "MutableBlock", "Should be a mutable block"
        assert mbm3.name == mblockm.name, "Names should survive round trip"
        if self.verbose: print "KEYCHAIN 5: Check can user ViewerKeyPair"
        acl = self._acl()   # Create Access Control List    - dont require encrypting as pretending itssomeone else's
        acl._allowunsafestore = True
        acl.add(viewerpublichash=viewerkeypair._hash, verbose=self.verbose)   # Add us as viewer
        sb = self._sb(acl=acl)   # Encrypted obj
        assert KeyChain.myviewerkeys()[0].name == vkpname, "Should find viewerkeypair stored above"
        if self.verbose: print "KEYCHAIN 6: Check can fetch and decrypt - should use viewerkeypair stored above"
        sb2 = StructuredBlock(hash=sb._hash, verbose=self.verbose).fetch(verbose=self.verbose) # Fetch & decrypt
        assert sb2.data == self.quickbrownfox, "Data should survive round trip"
        if self.verbose: print "KEYCHAIN 7: Check can store content via an MB"
        mblockm = MutableBlock.new(contentacl=acl, _allowunsafestore=True, content=self.quickbrownfox, signandstore=True, verbose=self.verbose)  # Simulate other end
        mb = MutableBlock(name="test_acl mb", hash=mblockm._publichash, verbose=self.verbose)
        assert mb.content(verbose=self.verbose) == self.quickbrownfox, "should round trip through acl"
        if self.verbose: print "test_keychain: done"
        #TODO - named things in keychain
        #TODO - test_keychain with HTML


    def Xtest_current(self):
        # def test_peer(self):
        # Experimental testing of peer
        self.verbose=True
        from TransportDist import TransportDist #TODO-TX move up top to imports when sold
        from TransportDist_Peer import Peer, ServerPeer
        # Use cache as the local machine's - remote will use cache_peer
        Dweb.settransport(transportclass=TransportDist, dir="../cache", verbose=self.verbose)
        qbfhash="SHA3256B64URL.heOtR2QnWEvPuVdxo-_2nPqxCSOUUjTq8GShJv8VUFI="    # Hash of quick brown fox
        cdhash="SHA3256B64URL.50GNWgUQ9GgrVfMvpedEg77ByMRYkUgPRU9P1gWaNF8="    # Hash of the Clever Dog string saved in test_upload
        data = Dweb.transport.rawfetch(hash=qbfhash,verbose=self.verbose)
        assert data == self.quickbrownfox, "Local cache of quick brown fox"+data
        invalidhash="SHA3256B64URL.aaaabbbbccccVfMvpedEg77ByMRYkUgPRU9P1gWaNF8="
        try:
            data = Dweb.transport.rawfetch(hash=invalidhash,verbose=self.verbose)
        except TransportBlockNotFound as e:
            if self.verbose: print e

        # This chunk may end up in a method on TransportDist_Peer
        node = Dweb.transport.node
        ipandport = ServerPeer.defaultipandport
        newpeer = Peer()
        foundpeer = node.peers.find(ipandport=ipandport)
        if not foundpeer:
            peer = Peer(ipandport=ipandport, verbose=self.verbose)    # Dont know nodeid yet
            node.peers.append(peer)
        peer.connect(verbose=self.verbose)
        assert peer.info["type"] == "DistPeerHTTP","Unexpected peer.info"+repr(peer.info)
        # Now we've got a peer so try again, should get bounced off peer server
        try:
            data = Dweb.transport.rawfetch(hash=invalidhash, verbose=self.verbose)
        except TransportBlockNotFound as e:
            if self.verbose: print e
        data = Dweb.transport.rawfetch(hash=cdhash, verbose=self.verbose)
        assert data == self.dog
        print "NEXTSTEP-----"
        print "XXX@362", Dweb.transport.rawstore(data=self.quickbrownfox, verbose=self.verbose)
        print "DONE---"