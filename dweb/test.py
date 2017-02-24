# encoding: utf-8
from datetime import datetime
import unittest

from CryptoLib import CryptoLib
from TransportLocal import TransportLocal
from Block import Block


class Testing(unittest.TestCase):
    def setUp(self):
        super(Testing, self).setUp()
        self.verbose=False
        self.quickbrownfox =  "The quick brown fox ran over the lazy duck"
        self.dog = "But the clever dog chased the fox"
        self.mydic = { "a": "AAA", "1":100, "B_date": datetime.now()}  # Dic can't contain integer field names
        Block.setup(TransportLocal, verbose=self.verbose, dir="../cache")

    def tearDown(self):
        super(Testing, self).tearDown()

    def test_Block(self):
        multihash = Block(self.quickbrownfox).store(verbose=self.verbose)
        block = Block.block(multihash, verbose=self.verbose)
        assert block._data == self.quickbrownfox, "Should return data stored"

    def test_StructuredBlock(self):
        from StructuredBlock import StructuredBlock
        # Test Structured block
        sblock = StructuredBlock(self.mydic)
        assert sblock.a == self.mydic['a'], "Testing attribute access"
        multihash = sblock.store(verbose=self.verbose)
        sblock2 = StructuredBlock.block(multihash, verbose=self.verbose)
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
        self.verbose=True
        #TODO add functionality for deleting specific items (via a "deleted" entry), and Clearing a list of all earlier.
