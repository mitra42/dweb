# encoding: utf-8
from datetime import datetime

from misc import ToBeImplementedException
from CryptoLib import CryptoLib # Suite of functions for hashing, signing, encrypting
#from StructuredBlock import StructuredBlock
from SignedBlock import SignedBlock

class MutableBlock(object):
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


    { _key: KeyPair, _current: SignedBlock, _prev: [ SignedBlock* ] }
    Get/Set non-private attributes writes to _current

    """
    #TODO-MUTABLE copy changes back to spec

    def __setattr__(self, name, value):
        if name and name[0] == "_":
            super(MutableBlock, self).__setattr__(name, value)   # Save _current, _key, _prev etc locally
        else:
            self._current.__setattr__(name, value)   # Pass to current

    def __getattr__(self, name):
        if name and name[0] == "_":
            return self.__dict__.get(name, None)    # Get _current, _key, _prev etc locally
        else:
            return self._current.__getattr__(name, None)

    def __repr__(self):
        return "MutableBlock(%s)" % self.__dict__

    def __init__(self, key=None, **options):
        """
        :param key:
        :param options:
        """
        #TODO-MUTABLE allow creation and initialization from a known public key
        if not key:
            key = CryptoLib.keygen()
        self._key = key
        self._current = SignedBlock()
        self._prev = []

    def signandstore(self, verbose=False, **options):
        """
        Sign and Store a version, or entry in MutableBlockMaster
        :return: hash stored under
        """
        self._current.sign(self._key).store(verbose=verbose, **options)

    def fetch(self, verbose=False, **options):
        """
        Still experimental - may split MutableBlock and MutableBlockMaster
        :param verbose:
        :param options:
        :return:
        """
        blocks = SignedBlock.fetch(self._key.publickey(), verbose=verbose, **options)
        #TODO now convert blocks into what we want - not sure what that is
        if verbose: print "MutableBlock.fetch Retrieved",len(blocks)
        return blocks

    #TODO - add metadata to Mutable - and probably others

