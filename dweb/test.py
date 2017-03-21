# encoding: utf-8
from datetime import datetime
import unittest
import os
from pathlib2 import Path
from json import loads, dumps

from misc import _print
from CryptoLib import CryptoLib, KeyPair
from Transport import TransportBlockNotFound, TransportURLNotFound
from TransportLocal import TransportLocal
from TransportHTTP import TransportHTTP
from CommonBlock import Transportable
from Block import Block
from StructuredBlock import StructuredBlock
from MutableBlock import MutableBlock, AccessControlList #TODO-AUTHENTICATION move to own file
from File import File, Dir


class Testing(unittest.TestCase):
    def setUp(self):
        super(Testing, self).setUp()
        testTransport = TransportHTTP  # Can switch between TransportLocal and TransportHTTP to test both
        self.verbose=False
        self.quickbrownfox =  "The quick brown fox ran over the lazy duck"
        self.dog = "But the clever dog chased the fox"
        self.mydic = { "a": "AAA", "1":100, "B_date": datetime.now()}  # Dic can't contain integer field names
        self.ipandport = ('localhost', 4243)  # Serve it via HTTP on all addresses
        #self.ipandport = ('192.168.1.156', 4243)  # Serve it via HTTP on all addresses
        self.exampledir = "../examples/"    # Where example files placed
        if testTransport == TransportLocal:
            Transportable.setup(TransportLocal, verbose=self.verbose, dir="../cache")
        elif testTransport == TransportHTTP:
            # Run python -m ServerHTTP; before this
            Transportable.setup(TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
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
        signedblock = StructuredBlock(data=self.mydic)
        keypair = KeyPair.keygen()
        signedblock.sign(keypair, verbose=self.verbose)
        assert signedblock.verify(verify_atleastone=True), "Should verify"
        signedblock.a="A++"
        assert not signedblock.verify(verify_atleastone=True, verbose=self.verbose), "Should fail"

    def test_MutableBlocks(self):
        # Mutable Blocks
        mblockm = MutableBlock(master=True, verbose=self.verbose)      # Create a new block with a new key
        mblockm.data = self.quickbrownfox                       # Put some data in it (goes in the StructuredBlock at _current
        mblockm.signandstore(verbose=self.verbose)              # Sign it - this publishes it
        testhash0 = mblockm._current._hash                      # Get a pointer to that version
        # Editing
        mblockm.data = self.dog                                 # Put some different content in it
        mblockm.signandstore(verbose=self.verbose)              # Publish new content
        testhash = mblockm._current._hash                       # Get a pointer to the new version
        keyhash = mblockm._keypair.store().publichash           # Get the publickey pointer to the block
        # And check it
        mblock = MutableBlock(hash=keyhash)                     # Setup a copy (not Master) via the publickey
        mblock.fetch(verbose=self.verbose)                      # Fetch the content
        assert mblock._current._hash == testhash, "Should match hash stored above"
        assert mblock._list[0]._hash == testhash0, "Prev list should hold first stored"

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
        Block.setup(TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        multihash = Block(data=self.quickbrownfox).store(verbose=self.verbose)._hash
        block = Block(hash=multihash, verbose=self.verbose).fetch(verbose=self.verbose)
        assert block._data == self.quickbrownfox, "Should return data stored"

    def test_file(self):
        Transportable.setup(TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        content = File.load(filepath=self.exampledir + "index.html", verbose=self.verbose).content(verbose=self.verbose)
        sb = StructuredBlock(**{"Content-type":"text/html"})  # ** because cant use args with hyphens\
        sb.data = content
        sb.store()
        sburl = sb.url(command="file", url_output="getpost")
        assert sburl == [False, "file", ["sb", sb._hash]]
        resp = Transportable.transport._sendGetPost(sburl[0], sburl[1], sburl[2], verbose=False)
        assert resp.text == content, "Should return data stored"
        assert resp.headers["Content-type"] == "text/html", "Should get type"
        # Now test a MutableBlock that uses this content
        mbm = MutableBlock(master=True, data=self.keyfromfile("index_html_rsa", private=True), contenthash=sb._hash)
        mbm.store().signandstore(verbose=self.verbose)
        if self.verbose: print "store tells us:", mbm.content()
        assert mbm.content()==content, "Should match content stored"
        mb = MutableBlock(hash=mbm._keypair.publichash)
        mb.fetch()      # Just fetches the signatures
        assert mb.content() == mbm.content(), "Should round-trip HTML content"
        mbcontent2 = Transportable.transport._sendGetPost(False,"file", ["mb", mb._hash]).text
        assert mbcontent2 == mbm.content(), "Should fetch MB content via its URL"

    def test_typeoverride(self):    # See if can override the type on a block
        Transportable.setup(TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        # Store the wrench icon
        content = File.load(filepath=self.exampledir + "WrenchIcon.png").content()
        wrenchhash = Block(data=content).store(verbose=self.verbose)._hash
        # And check it got there
        resp = Transportable.transport._sendGetPost(False, "rawfetch",  [wrenchhash], params={"contenttype": "image/png"})
        assert resp.headers["Content-type"] == "image/png", "Should get type"
        assert resp.content == content, "Should return data stored"
        resp = Transportable.transport._sendGetPost(False, "file",  ["b", wrenchhash], params={"contenttype": "image/png"})
        assert resp.headers["Content-type"] == "image/png", "Should get type"
        assert resp.content == content, "Should return data stored"

    def test_badblock(self):
        Block.setup(TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        try:
            resp = Transportable.transport._sendGetPost(False, "rawfetch", [ "12345"], params={"contenttype": "image/png"})
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
            mbm = MutableBlock(master=True, data=self.keyfromfile(keyname, private=True), contenthash=f._hash, verbose=self.verbose)
            mbm.store(private=True, verbose=self.verbose)
            mbm.signandstore(verbose=self.verbose)
            print filename + " editable:" + mbm.privateurl()    # Side effect of storing
            print filename + ":" + mbm.publicurl(command="file", table="mb")
        else:
            print filename + ":" + f.url(command="file", table="sb")


    def test_uploads(self):
        # A set of tools to upload things so available for testing.
        # All the functionality in storeas should have been tested elsewhere.
        Transportable.setup(TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
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

    def test_uploadandrelativepaths(self):
        # Test that a directory can be uploaded and then accessed by a relative path
        Transportable.setup(TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        f1sz = File.load("../tinymce/langs/readme.md").size
        # Upload a multi-level directory
        f = Dir.load(filepath="../tinymce", upload=True, verbose=self.verbose,)
        #print f.url()  # url of sb at top of directory
        sb = StructuredBlock(hash=f._hash, verbose=self.verbose).fetch(verbose=self.verbose)
        assert len(sb.links) == 8, "tinymce has 8 files"
        resp = Transportable.transport._sendGetPost(False, "file", ["sb", f._hash,"langs/readme.md"])
        assert int(resp.headers["Content-Length"]) == f1sz,"Should match length of readme.md"
        # /file/mb/SHA3256B64URL.88S-FYlEN1iF3WuDRdXoR8SyMUG6crR5ehM21IvUuS0=/tinymce.min.js

    def Xtest_current(self):
        self.verbose=True
        print "XXXUploading index.html"
        self._storeas("index.html", "index_html_rsa", "text/html")

    def Xtest_acl(self):    # For testing ACL
        self.verbose = True

        acl = AccessControlList(master=True, key=self.keyfromfile("test_acl1_rsa", private=True), verbose=self.verbose)
        acl.store(verbose=self.verbose) # Store public key
        #TODO Why storing new each time
        viewerkeypair = KeyPair(key=self.keyfromfile("test_viewer1_rsa")).store()

        viewerkeypair.encrypt(acl._keypair.privateexport)



        #acl.add(viewerkeypair.publichash)
        print "XXX@Done"
