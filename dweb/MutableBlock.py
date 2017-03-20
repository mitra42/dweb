# encoding: utf-8

from Block import Block
from CryptoLib import KeyPair, PrivateKeyException # Suite of functions for hashing, signing, encrypting
from SignedBlock import SignedBlock, SignedBlocks
from misc import ForbiddenException, _print
from CommonBlock import Transportable


class CommonList(Transportable):
    """
    Encapsulates a list of blocks, which includes MutableBlocks and AccessControlLists etc
    Partially copied to dweb.js.

    { _keypair: KeyPair, _list: [ StructredBlock* ] }

    """

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

    def __init__(self, master=False, keypair=None, data=None, hash=None, verbose=False, **options):  # Note hash is of data
        """
        Create and initialize a MutableBlock
        Adapted to dweb.js.MutableBlock.constructor
        Exceptions: PrivateKeyException if passed public key and master=True

        :param KeyPair keypair: Keypair identifying this list
        :param options: # Can indicate how to initialize content

        """
        #print "master=%s, keypair=%s, key=%s, hash=%s, verbose=%s, options=%s)" % (master, keypair, key, hash, verbose, options)
        self._master = master
        if data or hash:
            keypair = KeyPair(data=data, hash=hash, master=master)   # Should only be one of them

        if master and keypair and not keypair._key.has_private:
            raise PrivateKeyException(keypair.privatehash)

        if keypair:
            self._keypair = keypair
        else:
            self._keypair = KeyPair.keygen(**options)
        #TODO this should fail if ketpair doesnt have a master
        self._list = []

    def fetch(self, verbose=False, **options):
        """
        Copied to dweb.js.

        :param verbose:
        :param options:
        """
        self._list = SignedBlocks.fetch(hash=self._keypair.publichash, verbose=verbose, **options).sorteddeduplicated()

    def url(self, **options):
        #Note depends on subclass defining _table. And retrieval depends on that _table being in ServerHTTP.LetterToClass
        return Transportable.transport.url(self, **options)

    #TODO - add metadata to Mutable - and probably others

    def publicurl(self, command=None, **options):
        return Transportable.transport.url(self, command=command or "list", hash=self._keypair.publichash, **options) #, contenttype=self.__getattr__("Content-type"))

    def privateurl(self):
        """
        Get a URL that can be used for edits to the resource
        Side effect of storing the key

        :return:
        """
        return Transportable.transport.url(self, command="update", hash=self._keypair.privatehash, contenttype=self.__getattr__("Content-type"))
        #TODO-AUTHENTICATION - this is particularly vulnerable w/o authentication as stores PrivateKey in unencrypted form

    def store(self, private=False, verbose=False, **options):
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
            raise ForbiddenException(what="Signing a new entry when not a master list")
        obj.sign(self._keypair).store(verbose=verbose, **options)
        return self


class MutableBlock(CommonList):
    """
    Encapsulates a block that can change.
    Get/Set non-private attributes writes to the SignedBlock at _current.

    { _keypair: KeyPair, _current: SignedBlock, _list: [ SignedBlock* ] }
    """
    _table = "mb"

    def __init__(self, master=False, keypair=None, data=None, hash=None, contenthash=None, verbose=False, **options):
        """
        Create and initialize a MutableBlock
        Adapted to dweb.js.MutableBlock.constructor
        Exceptions: PrivateKeyException if passed public key and master=True


        :param data: Public or Private key text as exported by "PEM"
        :param hash: of key
        :param contenthash: hash of initial content (only currently applicable to master)
        :param options: # Can indicate how to initialize content
        """
        # This next line for "hash" is odd, side effect of hash being for content with MB.master and for key with MB.!master
        if verbose: print "MutableBlock( keypair=",keypair, "data=",data, "hash=", hash, "options=", options,")"
        super(MutableBlock, self).__init__(master=master, keypair=keypair, data=data, hash=hash, verbose=verbose, **options)
        # Exception PrivateKeyException if passed public key and master=True
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

        :return: self for chaining
        """
        if verbose: print "MutableBlock.fetch pubkey=",self._keypair.publichash
        super(MutableBlock, self).fetch(verbose=verbose, **options)
        self._current = self._list[-1]
        return self # For chaining

    def content(self, verbose=False, **options):
        self.fetch()
        return self._current.content(verbose=verbose, **options)

    def file(self, verbose=False, **options):
        if verbose: print "MutableBlock.file", self
        self.fetch(verbose=verbose, **options)    #TODO look at log for test_file, does too many fetches and lists
        if not self._current:
            raise AssertionFail(message="Looking for a file on an unloaded MB")
        return self._current.file(verbose=verbose, **options)

    def __setattr__(self, name, value):
        #TODO should probably fail if !master
        if name and name[0] == "_":
            super(MutableBlock, self).__setattr__(name, value)   # Save _current, _keypair, _list etc locally # Looks at CommonList
        else:
            self._current.__setattr__(name, value)   # Pass to current (a SignedBlock)

    def signandstore(self, verbose=False, **options):
        """
        Sign and Store a version, or entry in MutableBlock master
        Exceptions: SignedBlockEmptyException if neither hash nor structuredblock defined, ForbiddenException if !master

        :return: self to allow chaining of functions
        """
        return super(MutableBlock, self).signandstore(self._current, verbose=verbose, **options) # ERR SignedBlockEmptyException, ForbiddenException

    def path(self, urlargs, verbose=False, **optionsignored):
        print "XXX@191",self
        return self._current.path(urlargs, verbose)  # Pass to _current, (a SignedBlock)  and walk its path

class AccessControlList(CommonList):
    """
    An AccessControlList is a list for each control domain, with the entries being who has access.

    To create a list, it just requires a key pair, like any other List

    See Authentication.rst

    :param CommonList:
    :return:
    """

    def __init__(self, master=False, keypair=None, key=None, hash=None, verbose=False, **options):
        """
        Create and initialize a MutableBlock
        Adapted to dweb.js.MutableBlock.constructor

        :param key:
        :param hash: of key (alternative to key)
        :param master: True if its the master of the list, False, if its just a copy.
        :param options: # Can indicate how to initialize content
        """
        super(AccessControlList, self).__init__(master=master, keypair=keypair, data=data, hash=hash, verbose=verbose, **options)

    def item(info, verbose=False, **options):
        """

        :param info:    Dict, JSON, or StructuredBlock # Note SignedBlock also supports hash & signatures but not used here
        :param verbose:
        :return:
        """
        return SignedBlock(structuredblock=info, verbose=verbose, **options)

    def add(self, viewerpublichash, verbose=False, **options):
        """
        Add a new ACL entry
        Needs publickey of viewer
        #TODO - maybe use a second key for the viewing, while the privatekey of this list controls editing the list.

        :param self:
        :return:
        """
        if not self._master:
            raise ForbiddenException(what="Cant add viewers to ACL copy")
        viewerpublickeypair = KeyPair(hash=viewerpublichash)
        aclinfo = {
            "token": viewerpublickeypair.encrypt(self._keypair.privateexport),  #TODO returns binary which is a problem !
            "viewer": viewerpublichash,
            #TODO - recommended to use Crypto.Cipher.PKCS1_OAEP instead
        }
        sb = SignedBlock(structuredblock=aclinfo)
        self.signandstore(sb, verbose, **options)
