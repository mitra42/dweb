# encoding: utf-8
from datetime import datetime

from CryptoLib import CryptoLib
from TransportLocal import TransportLocal
from Block import Block
from StructuredBlock import StructuredBlock
from SignedBlock import SignedBlock
from MutableBlock import MutableBlock

def test():
    # Test Block
    verbose=False
    Block.setup(TransportLocal, verbose=verbose, dir="../cache")
    mydata="The quick brown fox ran over the lazy duck"
    multihash = Block(mydata).store(verbose=verbose)
    block = Block.block(multihash, verbose=verbose)
    assert block._data == mydata, "Should return data stored"

    # Test Structured block
    mydic = { "a": "AAA", "1":100}  # Dic can't contain integer field names
    mydic["B_date"] = datetime.now()     # Make sure can write date and time and survives round trip
    sblock = StructuredBlock(mydic)
    assert sblock.a == mydic['a'], "Testing attribute access"
    multihash = sblock.store(verbose=verbose)
    sblock = StructuredBlock.block(multihash, verbose=verbose)
    assert sblock.a == mydic['a'], "Testing StructuredBlock round-trip"
    assert sblock.B_date == mydic["B_date"], "DateTime should survive round trip"

    # Test Signatures
    signedblock = SignedBlock(structuredblock=sblock)
    key = CryptoLib.keygen()
    signedblock.sign(key, verbose=verbose)
    assert signedblock.verify(verify_atleastone=True), "Should verify"
    signedblock.a="A++"
    assert not signedblock.verify(verify_atleastone=True, verbose=verbose), "Should fail"

    # Mutable Blocks
    mblock = MutableBlock(verbose=verbose)
    mblock.data = mydata
    mblock.signandstore(verbose=verbose)
    mblock.data = "But the clever dog chased the fox"
    mblock.signandstore(verbose=verbose)
    verbose = True
    mblock.fetch(verbose=verbose)

    #TODO Split mutable objects class
