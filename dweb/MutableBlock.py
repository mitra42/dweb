# encoding: utf-8
from datetime import datetime

from misc import ToBeImplementedException
from CryptoLib import CryptoLib # Suite of functions for hashing, signing, encrypting
from Block import Block
from SignedBlock import SignedBlock, SignedBlocks

class MutableBlock(object):
    """
    Encapsulates a block that can change, or a list of blocks.

    Get/Set non-private attributes writes to the SignedBlock at _current

    { _key: KeyPair, _current: SignedBlock, _prev: [ SignedBlock* ] }

    """
    table="mb"
    transportcommand="block"

    @property
    def hash(self):
        return self._hash or (self._key and CryptoLib.urlhash(CryptoLib.exportpublic(self._key.publickey()))) or None

    def __getattr__(self, name):
        if name and name[0] == "_":
            return self.__dict__.get(name, None)    # Get _current, _key, _prev etc locally
        else:
            return self._current.__getattr__(name, None)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.__dict__)

    def __init__(self, key=None, hash=None, **options):
        """
        Create and initialize a MutableBlockMaster

        :param key:
        :param options: # Can indicate how to initialize content
        """
        #TODO-MUTABLE allow creation and initialization from a known public key
        self._hash = hash        # Could be None
        if key:
            if isinstance(key, basestring):
            # Its an exported key string, import it (note could be public or private)
                key = CryptoLib.importpublic(key)  # Works on public or private
                self._key = key
        else:
            self._key = None
            if not hash:    # Dont generate key if have a hash
                self._key = CryptoLib.keygen()
        self._current = None
        self._prev = []

    def fetch(self, verbose=False, **options):
        """
        Still experimental - may split MutableBlock and MutableBlockMaster

        :param verbose:
        :param options:
        """
        if self._key:
            signedblocks = SignedBlocks.fetch(publickey=self._key.publickey(), verbose=verbose, **options)
        else:
            signedblocks = SignedBlocks.fetch(hash=self.hash, verbose=verbose, **options)
        curr, prev = signedblocks.latestandsorteddeduplicatedrest()
        self._current = curr
        self._prev = prev

    def content(self, **options):
        return self._current.content(**options)

    def url(self, **options):
        return Block.transport.url(self, **options)

    #TODO - add metadata to Mutable - and probably others

class MutableBlockMaster(MutableBlock):
    """
    Class for publishing contains a list of older versions, or of previous blog postings.
    Get/Set non-private attributes writes to _current

    { _key: KeyPair, _current: SignedBlock, _prev: [ SignedBlock* ] }

    """
    # TODO-MUTABLE add variants for publishing & reading Lists (e.g. Blogs) or  Single Items,

    def __init__(self, key=None, **options):
        super(MutableBlockMaster,self).__init__()
        self._current = SignedBlock(**options)  # Create a place to hold content, options could load content

    def __setattr__(self, name, value):
        if name and name[0] == "_":
            super(MutableBlockMaster, self).__setattr__(name, value)   # Save _current, _key, _prev etc locally
        else:
            self._current.__setattr__(name, value)   # Pass to current

    def signandstore(self, verbose=False, **options):
        """
        Sign and Store a version, or entry in MutableBlockMaster

        :return: hash stored under
        """
        self._current.sign(self._key).store(verbose=verbose, **options) # Note this is storing all the sigs, not the content of _current

    def publickey(self, exportable=True):
        """
        :param exportable: if True export a string, otherwise a publickey (typically a RSAobj
        :return: key that can be used to fetch this block elsewhere
        """
        return CryptoLib.exportpublic(self._key) if exportable else self._key.publickey()
