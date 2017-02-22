# encoding: utf-8
from datetime import datetime

from StructuredBlock import StructuredBlock

class MutableBlock(StructuredBlock):
    """
    Encapsulates a block that can change
    """
    """
    store(:any:`MutableReferenceMaster`, :any:`MutableListEntry`) -> :any:`Multihash`
    mutableoject(:any:`MutableReference`) -> :any:`MutableBlock`
    MutableBlockMaster: `MutableReferenceMaster` `MutableListEntry`*
    MutableListEntry: `SignedDatedBlock` | `SignedChainedObject`
    MutableReference: `PublicKey` `MutableOptions`
    MutableReferenceMaster: `KeyPair` `MutableOptions`
    MutableBlock: `MutableListEntry`*
    MutableOptions: "options": "LAST" | "ALL"  [ int ]
    SignedChainedObject: `ChainedObject` `Signature` `PublicKey`
    ChainedObject: `DatedBlock` `Chain`
    Chain:  "previous": `Multihash`
    # Note could do a class DatedBlock as subclass of StructuredBlock
    """
    def store(self, verbose=False, **options):
        """
        Store a Mutable Object
        :return: hash stored under
        """
        # Date, Sign, <DONE> Store the block, get the hash, save hash in db
        # Maybe date on outside of sig

        #TODO update spec to show signaturedate instead of date
