# encoding: utf-8
from datetime import datetime

from misc import ToBeImplementedException
from CryptoLib import CryptoLib # Suite of functions for hashing, signing, encrypting
from Block import Block
from SignedBlock import SignedBlock, SignedBlocks

class CommonList(object):
    """
    Encapsulates a list of blocks, which includes MutableBlocks and AccessControlLists etc
    Partially copied to dweb.js.

    { _key: KeyPair, _hashpublickey, _list: [ StructredBlock* ] }

    """
    transportcommand="block"

    @property
    def _hash(self):
        if not self._hashpublickey:
            # Note this uses MutableBlock.table because could be called under MBM but that table is for PrivateKeys
            self._hashpublickey = Block(data=CryptoLib.export(self._key, private=False)).store(table="mb")
        if self._key.has_private and not self._hashprivatekey:
            self._hashprivatekey = Block(data=CryptoLib.export(self._key, private=True)).store(table=self.table)
        return (self._hashprivatekey if self._master else self._hashpublickey)

    def __getattr__(self, name):
        """
        Set local attribute, note redefined by MutableBlock

        :param name:
        """
        return self.__dict__.get(name, None)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.__dict__)

    def __init__(self, master=False, key=None, hash=None, verbose=False, **options):  # Note hash is of data

        """
        Create and initialize a MutableBlock
        Adapted to dweb.js.MutableBlock.constructor

        :param key:
        :param hash: optional hash of data to initialize with NOT hash of the key.
        :param options: # Can indicate how to initialize content
        """
        self._master = master
        if master:
            self._hashpublickey = None
            self._hashprivatekey = hash
        else:
            self._hashpublickey = hash        # Could be None
            self._hashprivatekey = None        # Could be None
        if key:
            if isinstance(key, basestring):
            # Its an exported key string, import it (note could be public or private)
                key = CryptoLib.importpublic(key)  # Works on public or private
                self._key = key
        else:
            self._key = None
            if not hash:    # Dont generate key if have a hash
                self._key = CryptoLib.keygen()
        self._list = []


    def fetch(self, verbose=False, **options):
        """
        Copied to dweb.js.

        :param verbose:
        :param options:
        """
        if not self._hash and not self._hashpublickey:
            self._hashpublickey = CryptoLib.Curlhash(CryptoLib.export(self._key.publickey()), verbose=verbose, **options)
        self._list = SignedBlocks.fetch(hash=self._hashpublickey, verbose=verbose, **options).sorteddeduplicated()

    def url(self, **options):
        return Block.transport.url(self, **options)

    #TODO - add metadata to Mutable - and probably others

    #def __setattr__(self, name, value):
    #    super(ListMaster, self).__setattr__(name, value)   # Save _current, _key, _list etc locally

    def publickey(self, exportable=True):
        """
        :param exportable: if True export a string, otherwise a publickey (typically a RSAobj
        :return: key that can be used to fetch this block elsewhere
        """
        return CryptoLib.export(self._key) if exportable else self._key.publickey()

    def publicurl(self, command=None, table=None):
        self._hash
        return Block.transport.url(self, command=command or "list", table=table or self.table, hash=self._hashpublickey) #, contenttype=self.__getattr__("Content-type"))

    def privateurl(self):
        """
        Get a URL that can be used for edits to the resource
        Side effect of storing the key

        :return:
        """
        #TODO - catch attempt to do this when _master=False - invalid
        self._hashprivatekey = Block(data=CryptoLib.export(self._key, private=True)).store(table=self.table)
        self._hash # Side effect of generating hashes
        return Block.transport.url(self, command="update", table=self.table, hash=self._hashprivatekey, contenttype=self.__getattr__("Content-type"))
        #TODO-AUTHENTICATION - this is particularly vulnerable w/o authentication as stores PrivateKey in unencrypted form

class MutableBlock(CommonList):
    """
    Encapsulates a block that can change.
    Get/Set non-private attributes writes to the SignedBlock at _current.

    { _key: KeyPair, _current: SignedBlock, _list: [ SignedBlock* ] }
    """

    def __init__(self, master=False, key=None, hash=None, contenthash=None, verbose=False, **options):  # Note hash is of data
        """
        Create and initialize a MutableBlock
        Adapted to dweb.js.MutableBlock.constructor

        :param key:
        :param hash: of key
        :param contenthash: hash of initial content (only currently applicable to master)
        :param options: # Can indicate how to initialize content
        """
        # This next line for "hash" is odd, side effect of hash being for content with MB.master and for key with MB.!master
        super(MutableBlock, self).__init__(master=master, key=key, hash=hash, verbose=verbose, **options)
        self._current = SignedBlock(hash=contenthash, verbose=verbose, **options) if master else None # Create a place to hold content, pass hash to load content
        self.__dict__["table"] = "mbm" if master else "mb"  #TODO should probably refactor table->_table but lots of cases

    def __getattr__(self, name):
        if name and name[0] == "_":
            return self.__dict__.get(name, None)    # Get _current, _key, _list etc locally
        else:
            return self._current.__getattr__(name)

    def fetch(self, verbose=False, **options):
        """
        Copied to dweb.js.

        :param verbose:
        :param options:
        """
        super(MutableBlock, self).fetch(verbose=verbose, **options)
        self._current = self._list[-1]

    def content(self, **options):
        return self._current.content(**options)

    def publicurl(self, command=None, table=None):
        return super(MutableBlock, self).publicurl(command=command, table=table or MutableBlock.table)

    def __setattr__(self, name, value):
        #TODO should probably fail if !master
        if name and name[0] == "_":
            super(MutableBlock, self).__setattr__(name, value)   # Save _current, _key, _list etc locally # Looks at CommonList
        else:
            self._current.__setattr__(name, value)   # Pass to current

    def signandstore(self, verbose=False, **options):
        """
        Sign and Store a version, or entry in MutableBlock master
        Exceptions: SignedBlockEmptyException if neither hash nor structuredblock defined

        :return: self
        """
        #TODO should fail if !master
        self._current.sign(self._key).store(verbose=verbose, **options) # Note this is storing all the sigs, not the content of _current
        # ERR SignedBlockEmptyException
        return self # Allow chaining functions e.g. MutableBlock(...).signandstore().xyz()


def AccessControlList(CommonList):
    table = "acl"

    def __init__(self, key=None, hash=None, **options):
        """
        Create and initialize a MutableBlock
        Adapted to dweb.js.MutableBlock.constructor

        :param key:
        :param hash: of key
        :param options: # Can indicate how to initialize content
        """
        super(AccessControlList, self).__init__(key, hash, **options)

def AccessControlListMaster(Commonlist):
    table = "aclm"