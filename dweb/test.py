# encoding: utf-8
from datetime import datetime
import unittest
import os
from pathlib2 import Path
from json import loads, dumps

from misc import _print
from CryptoLib import CryptoLib
from Transport import TransportBlockNotFound, TransportURLNotFound
from TransportLocal import TransportLocal
from TransportHTTP import TransportHTTP
from Block import Block
from StructuredBlock import StructuredBlock
from MutableBlock import MutableBlockMaster, MutableBlock
from File import File, Dir


class Testing(unittest.TestCase):
    def setUp(self):
        super(Testing, self).setUp()
        testTransport = TransportHTTP  # Can switch between TransportLocal and TransportHTTP to test both
        self.verbose=False
        self.quickbrownfox =  "The quick brown fox ran over the lazy duck"
        self.dog = "But the clever dog chased the fox"
        self.mydic = { "a": "AAA", "1":100, "B_date": datetime.now()}  # Dic can't contain integer field names
        #self.ipandport = ('localhost', 4243)  # Serve it via HTTP on all addresses
        self.ipandport = ('192.168.1.156', 4243)  # Serve it via HTTP on all addresses
        self.exampledir = "../examples/"    # Where example files placed
        if testTransport == TransportLocal:
            Block.setup(TransportLocal, verbose=self.verbose, dir="../cache")
        elif testTransport == TransportHTTP:
            # Run python -m ServerHTTP; before this
            Block.setup(TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        else:
            assert False, "Unimplemented test for Transport "+testTransport.__class__.__name__

    def tearDown(self):
        super(Testing, self).tearDown()

    def test_Block(self):
        multihash = Block(data=self.quickbrownfox).store(verbose=self.verbose)
        block = Block.block(multihash, verbose=self.verbose)
        assert block._data == self.quickbrownfox, "Should return data stored"

    def test_StructuredBlock(self):
        # Test Structured block
        sblock = StructuredBlock(dict=self.mydic)
        assert sblock.a == self.mydic['a'], "Testing attribute access"
        multihash = sblock.store(verbose=self.verbose)
        sblock2 = StructuredBlock.sblock(multihash, verbose=self.verbose)
        assert sblock2.a == self.mydic['a'], "Testing StructuredBlock round-trip"
        assert sblock2.B_date == self.mydic["B_date"], "DateTime should survive round trip"

    def test_Signatures(self):
        from SignedBlock import SignedBlock
        # Test Signatures
        signedblock = SignedBlock(structuredblock=self.mydic)
        key = CryptoLib.keygen()
        signedblock.sign(key, verbose=self.verbose)
        assert signedblock.verify(verify_atleastone=True), "Should verify"
        signedblock.a="A++"
        assert not signedblock.verify(verify_atleastone=True, verbose=self.verbose), "Should fail"

    def test_MutableBlocks(self):
        from MutableBlock import MutableBlockMaster, MutableBlock
        # Mutable Blocks
        mblockm = MutableBlockMaster(verbose=self.verbose)      # Create a new block with a new key
        mblockm.data = self.quickbrownfox                       # Put some data in it (goes in the SignedBlock
        mblockm.signandstore(verbose=self.verbose)              # Sign it - this publishes it
        testhash0 = mblockm._current._hash                      # Get a pointer to that version
        # Editing
        mblockm.data = self.dog                                 # Put some different content in it
        mblockm.signandstore(verbose=self.verbose)              # Publish new content
        testhash = mblockm._current._hash                       # Get a pointer to the new version
        publickey = mblockm.publickey()                         # Get the publickey pointer to the block
        # And check it
        mblock = MutableBlock(key=publickey)                    # Setup a copy (not Master) via the publickey
        mblock.fetch(verbose=self.verbose)                      # Fetch the content
        assert mblock._current._hash == testhash, "Should match hash stored above"
        assert mblock._prev[0]._hash == testhash0, "Prev list should hold first stored"

    def test_LongFiles(self):
        from StructuredBlock import StructuredBlock
        sblock = StructuredBlock({ "data": self.quickbrownfox}) # Note this is data held in the SB, as compared to _data which is data representing the SB
        assert sblock.size(verbose=self.verbose) == len(self.quickbrownfox), "Should get length"
        assert sblock.content(verbose=self.verbose) == self.quickbrownfox, "Should fetch string"
        multihash = Block(data=self.dog).store(verbose=self.verbose)
        sblock = StructuredBlock({ "hash": multihash})
        assert sblock.content(verbose=self.verbose) == self.dog, "Should fetch dog string"
        assert sblock.size(verbose=self.verbose) == len(self.dog), "Should get length"
        slinksblock = StructuredBlock({ "links": [
                                            StructuredBlock({ "data": self.quickbrownfox}),
                                            StructuredBlock({ "hash": multihash}),
                                        ]})
        assert slinksblock.content(verbose=self.verbose) == self.quickbrownfox+self.dog, "Should get concatenation"
        assert slinksblock.size(verbose=self.verbose) == len(self.quickbrownfox)+len(self.dog), "Should get length"

    def test_http(self):
        # Run python -m ServerHTTP; before this
        Block.setup(TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        multihash = Block(data=self.quickbrownfox).store(verbose=self.verbose)
        block = Block.block(multihash, verbose=self.verbose)
        assert block._data == self.quickbrownfox, "Should return data stored"

    def test_file(self):
        Block.setup(TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        content = File.load(filepath=self.exampledir + "index.html").content()
        sb = StructuredBlock(data=content, **{"Content-type":"text/html"})
        sbhash = sb.store()
        sburl = sb.url(command="file")
        #print "SBURL=",sburl # For debugging with Curl
        resp = Block.transport._sendGetPost(False, "file", ["sb", sbhash])
        assert resp.text == content, "Should return data stored"
        assert resp.headers["Content-type"] == "text/html", "Should get type"
        # Now test a MutableBlock that uses this content
        mbm = MutableBlockMaster(key=File.load(filepath=self.exampledir+"index_html_rsa").content(), hash=sbhash)
        mbm.signandstore(verbose=self.verbose)
        mb = MutableBlock(key=mbm.publickey())
        mb.fetch()      # Just fetches the signatures
        assert mb.content() == mbm.content(), "Should round-trip HTML content"
        mbcontent2 = Block.transport._sendGetPost(False,"file", [MutableBlock.table, mb._hash]).text
        assert mbcontent2 == mbm.content(), "Should fetch MB content via its URL"

    def test_typeoverride(self):    # See if can override the type on a block
        Block.setup(TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        # Store the wrench icon
        content = File.load(filepath=self.exampledir + "WrenchIcon.png").content()
        wrenchhash = Block(data=content).store(verbose=self.verbose)
        # And check it got there
        resp = Block.transport._sendGetPost(False, "block", [ Block.table, wrenchhash], params={"contenttype": "image/png"})
        assert resp.headers["Content-type"] == "image/png", "Should get type"
        assert resp.content == content, "Should return data stored"

    def test_badblock(self):
        Block.setup(TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        try:
            resp = Block.transport._sendGetPost(False, "block", [ Block.table, "12345"], params={"contenttype": "image/png"})
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
        keypath = self.exampledir + keyname if keyname else None
        if keypath:
            if not os.path.exists(keypath):
                CryptoLib.export(CryptoLib.keygen(), private=True, filename=keypath) # Uncomment to get a key
                #TODO next line fails if dont have a keyname which is ok for now
            mbm = MutableBlockMaster(key=File.load(filepath=keypath).content(), hash=f._hash, verbose=self.verbose).signandstore(verbose=self.verbose)
            print filename + " editable:" + mbm.privateurl()    # Side effect of storing
            print filename + ":" + mbm.publicurl(command="file", table="mb")
        else:
            print filename + ":" + f.url(command="file")


    def test_uploads(self):
        # A set of tools to upload things so available for testing.
        # All the functionality in storeas should have been tested elsewhere.
        Block.setup(TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
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

    def test_uploadandrelativepaths(self):
        # Test that a directory can be uploaded and then accessed by a relative path
        Block.setup(TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        f1sz = File.load("../tinymce/langs/readme.md").size
        # Upload a multi-level directory
        f = Dir.load(filepath="../tinymce", upload=True, verbose=self.verbose,)
        #print f.url()  # url of sb at top of directory
        sb = StructuredBlock.sblock(table=f.table, hash=f._hash, verbose=self.verbose)
        assert len(sb.links) == 8, "tinymce has 8 files"
        resp = Block.transport._sendGetPost(False, "file", [f.table, f._hash,"langs/readme.md"])
        assert int(resp.headers["Content-Length"]) == f1sz,"Should match length of readme.md"
        # http://localhost:4243/file/mb/SHA3256B64URL.88S-FYlEN1iF3WuDRdXoR8SyMUG6crR5ehM21IvUuS0=/tinymce.min.js

    def test_current(self):
        pass
