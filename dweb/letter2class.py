"""
This is a seperate file, loaded last, to avoid circular dependencies.
"""

from Block import Block
from StructuredBlock import StructuredBlock
from MutableBlock import MutableBlock
from KeyPair import KeyPair
from AccessControlList import AccessControlList
from KeyChain import KeyChain
from SmartDict import SmartDict
from Signature import Signature

LetterToClass = {
    Block.table:            Block,
    StructuredBlock.table:  StructuredBlock,
    MutableBlock.table:     MutableBlock,
    KeyPair.table:          KeyPair,
    AccessControlList.table: AccessControlList,
    KeyChain.table:          KeyChain,
    SmartDict.table:        SmartDict,
    Signature.table:        Signature
}
