# encoding: utf-8
from datetime import datetime
import unittest

from CryptoLib import CryptoLib
from TransportLocal import TransportLocal
from TransportHTTP import TransportHTTP
from Block import Block


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
        mblockm = MutableBlockMaster(verbose=self.verbose)
        mblockm.data = self.quickbrownfox
        mblockm.signandstore(verbose=self.verbose)
        testhash0 = mblockm._current._hash
        mblockm.data = self.dog
        mblockm.signandstore(verbose=self.verbose)
        testhash = mblockm._current._hash
        publickey = mblockm.publickey()
        mblock = MutableBlock(key=publickey)
        mblock.fetch(verbose=self.verbose)
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

    def test_current(self):
        # A set of tools building up to usability for web.
        Block.setup(TransportHTTP, verbose=self.verbose, ipandport=self.ipandport )
        filename = self.exampledir + "index.html"
        file = open(filename, "r")
        content = file.read()
        file.close()
        multihash = Block(content).store(verbose=self.verbose)
        #print "http://localhost:4243/block?hash="+multihash # For debugging with Curl
        block = Block.block(multihash, verbose=self.verbose)
        assert block._data == content, "Should return data stored"
        text = Block.transport._sendGet("block", params={"hash": multihash}).text
        assert text == content, "Should return data stored"
        from StructuredBlock import StructuredBlock
        sb = StructuredBlock(data=content, **{"Content-type":"text/html"})
        multihash = sb.store()
        #print "http://localhost:4243/file?hash="+multihash # For debugging with Curl
        resp = Block.transport._sendGet("file", params={"hash": multihash})
        assert resp.text == content, "Should return data stored"
        assert resp.headers["Content-type"] == "text/html", "Should get type"
        #TODO allow for URL like file/multihash
        #TODO allow for URLs containing html or json or gif
        #TODO Create URL; open in browser;
        #TODO switch from block?hash= to block/hash and file/hash

        #TODO handle unrecognized hashes in calls like file
        #TODO Add a public key for the index page, then mutable block then URL that can retrieve mutable, upload, retrieve, test retrieval
        #TODO upload some other things e.g. an image
        #TODO Relative URL handler on HTTPServer using same logic as IPFS - look for "/" in request
        #TODO Test relative URL on index page to image
        #TODO Add a Ajax list to sample page that loads raw content
        #TODO Add a Ajax list to sample page that loads structured data
        #TODO Javascript library running in sample web page
        #TODO Javascript library to be able to ....

    #TODO Think about tools for URL handling to make play nice with web pages
    #TODO open question - store html in such a way that "block" understands, or retrieve as "html"
