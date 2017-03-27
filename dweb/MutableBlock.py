# encoding: utf-8

from Block import Block
from CryptoLib import CryptoLib, KeyPair, PrivateKeyException, AuthenticationException, DecryptionFail # Suite of functions for hashing, signing, encrypting
import base64
from StructuredBlock import StructuredBlock
from SignedBlock import SignedBlocks
from misc import ForbiddenException, _print
from CommonBlock import Transportable, SmartDict


class CommonList(SmartDict):
    """
    Encapsulates a list of blocks, which includes MutableBlocks and AccessControlLists etc
    Partially copied to dweb.js.

    {
    keypair: KeyPair           Keys for this list
    _publichash:                Hash that is used for refering to list - i.e. of public version of it.
    _list: [ StructuredBlock* ] Blocks on this list
    _master bool                True if this is the controlling object, has private keys etc

    From SmartDict: _acl,
    From Transportable: _data, _hash

    """
    # Comments on use of superclass methods without overriding here

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.__dict__)

    def __init__(self, master=False, keypair=None, data=None, hash=None, verbose=False, **options):  # Note hash is of data
        #TODO-REFACTOR check all callers to this in this file
        """
        Create and initialize a MutableBlock
        Typically called either with args (master, keypair) if creating, or with data or hash to load from dWeb
        Adapted to dweb.js.MutableBlock.constructor
        Exceptions: PrivateKeyException if passed public key and master=True
        :param bool master: True if master for list
        :param KeyPair|str keypair: Keypair or export of Key identifying this list
        :param data: Exported data to import
        :param hash: Hash to exported data
        :param options: Set on SmartDict unless specifically handled here
        """
        #if verbose: print "master=%s, keypair=%s, key=%s, hash=%s, verbose=%s, options=%s)" % (master, keypair, key, hash, verbose, options)
        self._master = master
        super(CommonList, self).__init__(data=data, hash=hash, verbose=verbose, **options)  # Initializes __dict__ via _data -> _setdata

        if keypair: # Note keypair may also have been set via "data" field in super call
            if not isinstance(keypair, KeyPair): # Its an export
                keypair = KeyPair(key = keypair)  # Convert a string or a RSA key to a keypair
            self.keypair = keypair
        if self._master:
            if self.keypair: # master & keypair
                if not self.keypair._key.has_private:
                    raise PrivateKeyException(keypair.privatehash)
            else:   # master & !keypair
                self.keypair = KeyPair.keygen(**options)   # Note these options are also set on smartdict, so catch explicitly if known.
        else:
            self._publichash = hash # Maybe None.

        self._list = []

    def preflight(self, dd=None):
        if not dd:
            dd = self.__dict__.copy()
        if dd.get("keypair"):
            dd["keypair"] = dd["keypair"].privateexport if dd["_master"] else dd["keypair"].publicexport
        return super(CommonList, self).preflight(dd=dd)

    def _setdata(self, value):
        super(CommonList, self)._setdata(value) # Sets __dict__ from values
        if self.keypair and not isinstance(self.keypair, KeyPair):
            self.keypair = KeyPair(key=self.keypair)
            self._master = self.keypair._key.has_private

    _data = property(SmartDict._getdata, _setdata)

    def fetch(self, verbose=False, fetchlist=True, **options):
        """
        Copied to dweb.js.

        :param bool fetchlist: True (default) will fetch the list (slow), otherwise just gets the keys etc
        :param verbose:
        :param options:
        """
        super(CommonList, self).fetch(verbose=verbose, **options)   # Sets keypair etc via _data -> _setdata
        if fetchlist:
            self._list = SignedBlocks.fetch(hash=self._publichash, verbose=verbose, **options).sorteddeduplicated()
        return self # for chaining

    def store(self, verbose=False, **options):
        # - uses SmartDict.store which calls _data -> _getdata which gets the key
        if verbose: print "ACL.store"
        if self._master and not self._publichash:
            acl2 = self.__class__(master=False, keypair=self.keypair)
            acl2.store(verbose=verbose, **options)
            self._publichash = acl2._hash
        super(CommonList,self).store()   # Stores privatekey  and sets _hash
        return self

    def publicurl(self, command=None, **options):
        return Transportable.transport.url(self, command=command or "list", hash=self._publichash, **options) #, contenttype=self.__getattr__("Content-type"))

    def privateurl(self):
        """
        Get a URL that can be used for edits to the resource
        Side effect of storing the key

        :return:
        """
        return Transportable.transport.url(self, command="update", hash=self.privatehash, contenttype=self._current.__getattr__("Content-type"))
        #TODO-AUTHENTICATION - this is particularly vulnerable w/o authentication as stores PrivateKey in unencrypted form


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
        obj.sign(self).store(verbose=verbose, **options)
        return self


class MutableBlock(CommonList):
    """
    Encapsulates a block that can change.
    Get/Set non-private attributes writes to the StructuredBlock at _current.

    {   _current: StructuredBlock       Most recently published item
        _list: [ StructuredBlock* ] }   List of all published item (think of as previous versions)
        contentacl                      ACL, or its hash to use for content (note the MB itself is encrypted with via its own _acl field)
        From CommonList: _publichash, _master bool, keypair
        From SmartDict: _acl,
        From Transportable: _data, _hash
    """
    _table = "mb"

    def __init__(self, master=False, keypair=None, data=None, hash=None, contenthash=None, contentacl=None, verbose=False, **options):
        #TODO-REFACTOR check all callers to this in test()
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
        self.contentacl = contentacl    # Hash of content when publishing - calls contentacl.setter which retrieves it , only has meaning if master - triggers setter on content
        self._current = StructuredBlock(hash=contenthash, verbose=verbose) if master else None # Create a place to hold content, pass hash to load content
        #OBS - table is always mb: self.__dict__["table"] = "mbm" if master else "mb"

    @property
    def contentacl(self):
        return self.__dict__.get("contentacl", None)

    @contentacl.setter
    def contentacl(self, value):
        """
        Set the contentacl used to control whether content encrypted or not

        :param value: hash, AccessControlList or None
        """
        if value:
            if not isinstance(value, AccessControlList):
                value = AccessControlList(value)
        self.__dict__["contentacl"] = value

    def fetch(self, verbose=False, **options):
        """
        Copied to dweb.js.

        :return: self for chaining
        """
        if verbose: print "MutableBlock.fetch pubkey=",self._hash
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

    def signandstore(self, verbose=False, **options):
        """
        Sign and Store a version, or entry in MutableBlock master
        Exceptions: SignedBlockEmptyException if neither hash nor structuredblock defined, ForbiddenException if !master

        :return: self to allow chaining of functions
        """
        if (not self._current._acl) and self.contentacl:
            self._current._acl = self.contentacl    # Make sure SB encrypted when stored
            self._current.dirty()   # Make sure stored again if stored unencrypted. - _hash will be used by signandstore
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

    def __init__(self, master=False, keypair=None, data=None, hash=None, accesskey=None, verbose=False, **options):
        #TODO-REFACTOR check all callers to this in test()
        """
        Create and initialize a AccessControlList
        Adapted to dweb.js.MutableBlock.constructor

        :param KeyPair keypair: Public and Optionally private key
        :param hash: of key (alternative to key)
        :param master: True if its the master of the list, False, if its just a copy.
        :param accesskey: Key to use for access - typically random
        :param options: Set on smart dict unless specifically handled
        """
        super(AccessControlList, self).__init__(master=master, keypair=keypair, data=data, hash=hash, accesskey=accesskey, verbose=verbose, **options)

    def add(self, viewerpublichash=None, verbose=False, **options):
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
            # Need to go B64->binary->encrypt->B64
            "token": viewerpublickeypair.encrypt(base64.urlsafe_b64decode(self.accesskey), b64=True),
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