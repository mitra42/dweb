# encoding: utf-8
from datetime import datetime
import unittest
import os

from misc import filecontent
from CryptoLib import CryptoLib
from Transport import TransportBlockNotFound
from TransportLocal import TransportLocal
from TransportHTTP import TransportHTTP
from Block import Block
from StructuredBlock import StructuredBlock
from MutableBlock import MutableBlockMaster, MutableBlock


class Testing(unittest.TestCase):
    def setUp(self):
        super(Testing, self).setUp()
        testTransport = TransportHTTP
        self.verbose=False
        self.quickbrownfox =  "The quick brown fox ran over the lazy duck"
        self.dog = "But the clever dog chased the fox"
        self.mydic = { "a": "AAA", "1":100, "B_date": datetime.now()}  # Dic can't contain integer field names
        self.ipandport = ('localhost', 4243)  # Serve it via HTTP on all addresses
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
        multihash = Block(self.quickbrownfox).store(verbose=self.verbose)
        block = Block.block(multihash, verbose=self.verbose)
        assert block._data == self.quickbrownfox, "Should return data stored"

    def test_StructuredBlock(self):
        from StructuredBlock import StructuredBlock
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
        from StructuredBlock import StructuredBlock, StructuredLink
        sblock = StructuredBlock({ "data": self.quickbrownfox})
        assert sblock.size(verbose=self.verbose) == len(self.quickbrownfox), "Should get length"
        assert sblock.content(verbose=self.verbose) == self.quickbrownfox, "Should fetch string"
        multihash = Block(self.dog).store(verbose=self.verbose)
        sblock = StructuredBlock({ "hash": multihash})
        assert sblock.content(verbose=self.verbose) == self.dog, "Should fetch dog string"
        assert sblock.size(verbose=self.verbose) == len(self.dog), "Should get length"
        slinksblock = StructuredBlock({ "links": [
                                            StructuredLink({ "data": self.quickbrownfox}),
                                            StructuredLink({ "hash": multihash}),
                                        ]})
        assert slinksblock.content(verbose=self.verbose) == self.quickbrownfox+self.dog, "Should get concatenation"
        assert slinksblock.size(verbose=self.verbose) == len(self.quickbrownfox)+len(self.dog), "Should get length"
        #TODO add functionality for deleting specific items (via a "deleted" entry), and Clearing a list of all earlier.

    def test_http(self):
        # Run python -m ServerHTTP; before this
        Block.setup(TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        multihash = Block(self.quickbrownfox).store(verbose=self.verbose)
        block = Block.block(multihash, verbose=self.verbose)
        assert block._data == self.quickbrownfox, "Should return data stored"

    def test_file(self):
        Block.setup(TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        content = filecontent(self.exampledir + "index.html")
        sb = StructuredBlock(data=content, **{"Content-type":"text/html"})
        sbhash = sb.store()
        sburl = sb.url(command="file")
        #print "SBURL=",sburl # For debugging with Curl
        resp = Block.transport._sendGetPost(False, "file", ["sb", sbhash])
        assert resp.text == content, "Should return data stored"
        assert resp.headers["Content-type"] == "text/html", "Should get type"
        # Now test a MutableBlock that uses this content
        mbm = MutableBlockMaster(key=filecontent(self.exampledir+"index_html_rsa"), hash=sbhash)
        mbm.signandstore(verbose=self.verbose)
        mb = MutableBlock(key=mbm.publickey())
        mb.fetch()      # Just fetches the signatures
        assert mb.content() == mbm.content(), "Should round-trip HTML content"
        mbcontent2 = Block.transport._sendGetPost(False,"file", [MutableBlock.table, mb.hash]).text
        assert mbcontent2 == mbm.content(), "Should fetch MB content via its URL"
        print "index.html MB =", mb.url(command="file")

    def test_typeoverride(self):    # See if can override the type on a block
        Block.setup(TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        # Store the wrench icon
        content = filecontent(self.exampledir + "WrenchIcon.png")
        wrenchhash = Block(content).store(verbose=self.verbose)
        # And check it got there
        resp = Block.transport._sendGetPost(False, "block", [ Block.table, wrenchhash], params={"contenttype": "image/png"})
        assert resp.headers["Content-type"] == "image/png", "Should get type"
        assert resp.content == content, "Should return data stored"

    def test_badblock(self):
        Block.setup(TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        try:
            resp = Block.transport._sendGetPost(False, "block", [ Block.table, "12345"], params={"contenttype": "image/png"})
        except TransportBlockNotFound as e:
            pass
        else:
            assert False, "Should raise a TransportBlockNotFound error"

    def _storeas(self, filename, keyname, type):
        filepath = self.exampledir + filename
        keypath = self.exampledir + keyname if keyname else None
        content = filecontent(filepath)
        sb = StructuredBlock(data=content, **{"Content-type": type})
        sb.store(verbose=self.verbose)
        if keypath and not os.path.exists(keypath):
            CryptoLib.export(CryptoLib.keygen(), private=True, filename=keypath) # Uncomment to get a key
        #TODO next line fails if dont have a keyname which is ok for now
        mbm = MutableBlockMaster(key=filecontent(keypath), hash=sb.hash).signandstore()
        print filename + ":" + mbm.url(command="file")
        print filename + " editable:" + mbm.privateurl()


    def test_current(self):     #TODO-URLREFACTOR add url function to objects
        # A set of tools building up to usability for web.
        # All the functionality in storeas should have been tested elsewhere.
        self._storeas("dweb.js", "dweb_js_rsa", "application/json")
        self._storeas("index.html", "index_html_rsa", "text/html")
        self._storeas("snippet.html", "snippet_html_rsa", "text/html")

        #TODO ====Storing from web editor====
        #TODO Build save part of lib

        """
        Think storage part is along lines of ...
        Page has hash for key/privkey << for now fixed, later can load resource to work on
        Sends update/mbm/keyhash data
        It fetches key from keyhash, signs mb, and stores
        """



        #TODO How to hold key, how to sign,
        #TODO SAVE WORKING
        #TODO -----
        #TODO think of urls that would be useful e.g. /list/
        #TODO mutable block URL that can upload, retrieve, test retrieval and add to demo page
        #TODO upload some other things e.g. an image
        #TODO Relative URL handler on HTTPServer using same logic as IPFS - look for "/" in request
        #TODO Test relative URL on index page to image
        #TODO Add a Ajax list to sample page that loads raw content
        #TODO Add a Ajax list to sample page that loads structured data
        #TODO Javascript library running in sample web page
        #TODO Javascript library to be able to ....

        #TODO Build a trivial uploader (reqs URL refactor)

    #TODO Think about tools for URL handling to make play nice with web pages
    #TODO open question - store html in such a way that "block" understands, or retrieve as "html"

    #TODO-EDITOR image uploading https://www.tinymce.com/docs/get-started/upload-images/