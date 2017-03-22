# encoding: utf-8

from Block import Block
from CryptoLib import CryptoLib, KeyPair, PrivateKeyException, AuthenticationException, DecryptionFail # Suite of functions for hashing, signing, encrypting
import base64
from StructuredBlock import StructuredBlock
from SignedBlock import SignedBlocks
from misc import ForbiddenException, _print
from CommonBlock import Transportable


class CommonList(Transportable):
    """
    Encapsulates a list of blocks, which includes MutableBlocks and AccessControlLists etc
    Partially copied to dweb.js.

    { _keypair: KeyPair, _list: [ StructuredBlock* ] }

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
        self._list = []

    def fetch(self, verbose=False, **options):
        """
        Copied to dweb.js.

        :param verbose:
        :param options:
        """
        self._list = SignedBlocks.fetch(hash=self._keypair.publichash, verbose=verbose, **options).sorteddeduplicated()


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
        Sign and store a StructuredBlock on a list

        :param StructuredBlock obj:
        :param verbose:
        :param options:
        :return:
        """
        if not self._master:
            raise ForbiddenException(what="Signing a new entry when not a master list")
        # The obj.store stores signatures as well (e.g. see StructuredBlock.store)
        obj.sign(self._keypair).store(verbose=verbose, **options)
        return self


class MutableBlock(CommonList):
    """
    Encapsulates a block that can change.
    Get/Set non-private attributes writes to the StructuredBlock at _current.

    { _keypair: KeyPair, _current: StructuredBlock, _list: [ StructuredBlock* ] }
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
        self._current = StructuredBlock(hash=contenthash, verbose=verbose, **options) if master else None # Create a place to hold content, pass hash to load content
        #OBS - table is always mb: self.__dict__["table"] = "mbm" if master else "mb"

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
        if self._current:
            self._current.fetch()   # Fetch current content
        return self # For chaining

    def content(self, verbose=False, **options):
        self.fetch()
        return self._current.content(verbose=verbose, **options)

    def file(self, verbose=False, **options):
        if verbose: print "MutableBlock.file", self
        self.fetch(verbose=verbose, **options)    #TODO-EFFICIENCY look at log for test_file, does too many fetches and lists
        if not self._current:
            raise AssertionFail(message="Looking for a file on an unloaded MB")
        return self._current.file(verbose=verbose, **options)

    def __setattr__(self, name, value):
        #TODO should probably fail if !master
        if name and name[0] == "_":
            super(MutableBlock, self).__setattr__(name, value)   # Save _current, _keypair, _list etc locally # Looks at CommonList
        else:
            #TODO-REFACTOR - check if used
            self._current.__setattr__(name, value)   # Pass to current (a StructuredBlock)

    def signandstore(self, verbose=False, **options):
        """
        Sign and Store a version, or entry in MutableBlock master
        Exceptions: SignedBlockEmptyException if neither hash nor structuredblock defined, ForbiddenException if !master

        :return: self to allow chaining of functions
        """
        return super(MutableBlock, self).signandstore(self._current, verbose=verbose, **options) # ERR SignedBlockEmptyException, ForbiddenException

    def path(self, urlargs, verbose=False, **optionsignored):
        return self._current.path(urlargs, verbose)  # Pass to _current, (a StructuredBlock)  and walk its path

class AccessControlList(CommonList):
    """
    An AccessControlList is a list for each control domain, with the entries being who has access.

    To create a list, it just requires a key pair, like any other List

    See Authentication.rst

    :param CommonList:
    :return:
    """
    myviewerkeys = []       # Set with keys we can use

    def __init__(self, master=False, keypair=None, data=None, hash=None, verbose=False, **options):
        """
        Create and initialize a AccessControlList
        Adapted to dweb.js.MutableBlock.constructor

        :param KeyPair keypair: Public and Optionally private key
        :param hash: of key (alternative to key)
        :param master: True if its the master of the list, False, if its just a copy.
        :param options: # Can indicate how to initialize content
        """
        super(AccessControlList, self).__init__(master=master, keypair=keypair, data=data, hash=hash, verbose=verbose, **options)

    def add(self, accesskey=None, viewerpublichash=None, verbose=False, **options):
        """
        Add a new ACL entry
        Needs publickey of viewer

        :param self:
        :return:
        """
        if not self._master:
            raise ForbiddenException(what="Cant add viewers to ACL copy")
        viewerpublickeypair = KeyPair(hash=viewerpublichash)
        aclinfo = {
            "token": viewerpublickeypair.encrypt(accesskey, b64=True),
            "viewer": viewerpublichash,
        }
        sb = StructuredBlock(data=aclinfo)
        self.signandstore(sb, verbose, **options)

    def tokens(self, viewerkeypair=None, verbose=False, decrypt=True, **options):
        """
        Find the entries for a specific viewer
        There might be more than one if either the accesskey changed or the person was added multiple times.
        Entries are StructuredBlocks with token being the decryptable token we want

        :param viewerkeypair:  KeyPair of viewer
        :param verbose:
        :param options:
        :return:
        """
        self.fetch(verbose=verbose)
        viewerpublichash = viewerkeypair.publichash
        toks = [ a.token for a in self._list if a.fetch().viewer == viewerpublichash]
        if decrypt:
            toks = [ viewerkeypair.decrypt(str(a), b64=True) for a in toks ]
        return toks

    def decrypt(self, data, viewerkeypair=None, verbose=False):
        vks = viewerkeypair or AccessControlList.myviewerkeys
        if not isinstance(vks, (list, tuple, set)):
            vks = [ vks ]
        for vk in vks:
            for symkey in self.tokens(viewerkeypair = vk, decrypt=True):
                try:
                    r = CryptoLib.sym_decrypt(data, symkey, b64=True) #Exception DecryptionFail
                    return r    # Dont continue to process when find one
                except DecryptionFail as e:  # DecryptionFail but keep going
                    pass    # Ignore if cant decode maybe other keys will work
        raise AuthenticationException(message="ACL.decrypt: No valid keys found")

    @classmethod
    def addviewer(cls, keypair=None):
        """
        Add keys I can view under to ACL

        :param keypair:
        :return:
        """
        if isinstance(keypair, (list, tuple, set)):
            cls.myviewerkeys += keypair
        else:
            cls.myviewerkeys.append(keypair)