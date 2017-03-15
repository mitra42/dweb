# encoding: utf-8
from datetime import datetime

from misc import ToBeImplementedException, ForbiddenException
from CryptoLib import CryptoLib, KeyPair # Suite of functions for hashing, signing, encrypting
from Block import Block
from SignedBlock import SignedBlock, SignedBlocks

class CommonList(object):
    """
    Encapsulates a list of blocks, which includes MutableBlocks and AccessControlLists etc
    Partially copied to dweb.js.

    { _keypair: KeyPair, _list: [ StructredBlock* ] }

    """
    transportcommand="block"

    @property
    def _hash(self):
        """
        Return private or public hash for this list, depending on master.  Side effect of storing if reqd. #TODO-AUTHENTICATION check not storing inadvertantly

        :return:
        """
        if self.master:
            return self._keypair.privatehash
        else:
            return self._keypair.publichash

    def __getattr__(self, name):
        """
        Set local attribute, note redefined by MutableBlock

        :param name:
        """
        return self.__dict__.get(name, None)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.__dict__)

    def __init__(self, master=False, keypair=None, key=None, hash=None, verbose=False, **options):  # Note hash is of data
        """
        Create and initialize a MutableBlock
        Adapted to dweb.js.MutableBlock.constructor

        :param KeyPair keypair: Keypair identifying this list
        :param options: # Can indicate how to initialize content
        """
        #print "master=%s, keypair=%s, key=%s, hash=%s, verbose=%s, options=%s)" % (master, keypair, key, hash, verbose, options)
        self._master = master
        if key or hash:
            keypair = KeyPair(key=key, hash=hash)   # Should only be one of them

        if keypair:
            self._keypair = keypair
        else:
            self._keypair = KeyPair.keygen(**options)
        self._list = []

    def fetch(self, verbose=False, **options):
        """
        Copied to dweb.js.

        :param verbose:
        :param options:
        """
        self._list = SignedBlocks.fetch(hash=self._keypair.publichash, verbose=verbose, **options).sorteddeduplicated()

    def url(self, **options):
        return Block.transport.url(self, **options)

    #TODO - add metadata to Mutable - and probably others

    def publicurl(self, command=None, table=None):
        return Block.transport.url(self, command=command or "list", table=table or self.table, hash=self._keypair.publichash) #, contenttype=self.__getattr__("Content-type"))

    def privateurl(self):
        """
        Get a URL that can be used for edits to the resource
        Side effect of storing the key

        :return:
        """
        return Block.transport.url(self, command="update", table=self.table, hash=self.privatehash, contenttype=self.__getattr__("Content-type"))
        #TODO-AUTHENTICATION - this is particularly vulnerable w/o authentication as stores PrivateKey in unencrypted form

    def store(self, private=False, verbose=False):
        """
        Store a list, so can be retrieved by its hash.
        Saves the key, can be subclassed to save other meta-data.

        :param private: True if should store the private key version    #TODO-AUTHENTICATION currently insecure as stores Private key unencrypted
        :return:
        """
        self._keypair.store(private=private, verbose=verbose)    # Store key so can be accessed by hash
        return self # For chaining

    def signandstore(self, obj, verbose=False, **options):
        """
        Sign and store a SignedBlock on a list

        :param SignedBlock obj:
        :param verbose:
        :param options:
        :return:
        """
        if not self._master:
            raise ForbiddenException("Signing a new entry when not a master list")
        obj.sign(self._keypair).store(verbose=verbose, **options)
        return self


class MutableBlock(CommonList):
    """
    Encapsulates a block that can change.
    Get/Set non-private attributes writes to the SignedBlock at _current.

    { _keypair: KeyPair, _current: SignedBlock, _list: [ SignedBlock* ] }
    """

    def __init__(self, master=False, keypair=None, key=None, hash=None, contenthash=None, verbose=False, **options):
        """
        Create and initialize a MutableBlock
        Adapted to dweb.js.MutableBlock.constructor

        :param key:
        :param hash: of key
        :param contenthash: hash of initial content (only currently applicable to master)
        :param options: # Can indicate how to initialize content
        """
        # This next line for "hash" is odd, side effect of hash being for content with MB.master and for key with MB.!master
        super(MutableBlock, self).__init__(master=master, keypair=keypair, key=key, hash=hash, verbose=verbose, **options)
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
            super(MutableBlock, self).__setattr__(name, value)   # Save _current, _keypair, _list etc locally # Looks at CommonList
        else:
            self._current.__setattr__(name, value)   # Pass to current

    def signandstore(self, verbose=False, **options):
        """
        Sign and Store a version, or entry in MutableBlock master
        Exceptions: SignedBlockEmptyException if neither hash nor structuredblock defined, ForbiddenException if !master

        :return: self to allow chaining of functions
        """
        return super(MutableBlock, self).signandstore(self._current, verbose=verbose, **options) # ERR SignedBlockEmptyException, ForbiddenException


class AccessControlList(CommonList):
    """
    An AccessControlList is a list for each control domain, with the entries being who has access.

    To create a list, it just requires a key pair, like any other List

    See Authentication.rst

    :param CommonList:
    :return:
    """
    table = "acl"

    def __init__(self, master=False, keypair=None, key=None, hash=None, verbose=False, **options):
        """
        Create and initialize a MutableBlock
        Adapted to dweb.js.MutableBlock.constructor

        :param key:
        :param hash: of key (alternative to key)
        :param master: True if its the master of the list, False, if its just a copy.
        :param options: # Can indicate how to initialize content
        """
        super(AccessControlList, self).__init__(master=master, keypair=keypair, key=key, hash=hash, verbose=verbose, **options)

    def item(info, verbose=False, **options):
        """

        :param info:    Dict, JSON, or StructuredBlock # Note SignedBlock also supports hash & signatures but not used here
        :param verbose:
        :return:
        """
        return SignedBlock(structuredblock=fields, verbose=verbose, **options)

    def add(self, viewerpublichash, verbose=False, **options):
        """
        Add a new ACL entry
        Needs publickey of viewer
        #TODO - maybe use a second key for the viewing, while the privatekey of this list controls editing the list.

        :param self:
        :return:
        """
        if not self._master:
            raise ForbiddenException("Cant add viewers to ACL copy")
        print "XXX@221 hash=",viewerpublichash
        viewerpublickeypair = KeyPair(hash=viewerpublichash)
        aclinfo = {
            "token": viewerpublickeypair.encrypt(self._keypair.privateexport),  #TODO returns binary which is a problem !
            "viewer": viewerpublichash,
            #TODO - recommended to use Crypto.Cipher.PKCS1_OAEP instead
        }
        sb = SignedBlock(structuredblock=aclinfo)
        print "XXX@228", sb
        self.signandstore(sb, verbose, **options)
