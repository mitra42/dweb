# encoding: utf-8

from Block import Block
from CryptoLib import CryptoLib, KeyPair, WordHashKey, PrivateKeyException, AuthenticationException, DecryptionFail, SecurityWarning
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

    From SmartDict: _acl, name
    From Transportable: _data, _hash

    """
    # Comments on use of superclass methods without overriding here

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.__dict__)

    def __init__(self, master=False, keypair=None, data=None, hash=None, verbose=False, keygen=False, mnemonic=None, **options):  # Note hash is of data
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
        if mnemonic:
            self.keypair = WordHashKey(mnemonic)
        if keypair:
            self.keypair = keypair
        if keygen:
                self.keypair = KeyPair.keygen(**options)   # Note these options are also set on smartdict, so catch explicitly if known.
        if not self._master:
            self._publichash = hash # Maybe None.

        self._list = []

    @property
    def keypair(self):
        return self.__dict__.get("keypair")

    @keypair.setter
    def keypair(self, value):
        if value and not isinstance(value, KeyPair):
            value = KeyPair(key=value)
        self.__dict__["keypair"] = value
        self._master = value and value._key.has_private()


    def preflight(self, dd=None):
        if not dd:
            dd = self.__dict__.copy()
        if dd.get("keypair"):   # Based on whether the CommonList is master, rather than if the key is (key could be master, and CL not)
            if dd["_master"] and not dd.get("_acl") and not self._allowunsafestore:
                raise SecurityWarning(message="Probably shouldnt be storing private key on this "+self.__class__.__name__)  # Can set KeyPair._allowunsafestore to allow this when testing
            dd["keypair"] = dd["keypair"].privateexport if dd["_master"] else dd["keypair"].publicexport
        return super(CommonList, self).preflight(dd=dd)

    #def _setdata(self, value):
    #    super(CommonList, self)._setdata(value) # Sets __dict__ from values including keypair via setter
    #_data = property(SmartDict._getdata, SmartDict._setdata)

    def fetch(self, verbose=False, fetchBody=True, fetchlist=True, fetchblocks=False, **options):
        """
        Copied to dweb.js.

        :param bool fetchlist: True (default) will fetch the list (slow), otherwise just gets the keys etc
        :param verbose:
        :param options:
        """
        if fetchBody:
            super(CommonList, self).fetch(verbose=verbose, **options)   # only fetches if _needsfetch=True, Sets keypair etc via _data -> _setdata,
        if fetchlist:
            self._list = SignedBlocks.fetch(hash=self._publichash or self.keypair._hash, fetchblocks=fetchblocks, verbose=verbose, **options).sorteddeduplicated()
        return self # for chaining

    def _storepublic(self, verbose=False, **options):
        acl2 = self.__class__(keypair=self.keypair, name=self.name)
        acl2._master = False
        acl2.store(verbose=verbose, **options)
        return acl2._hash

    def store(self, verbose=False, dontstoremaster=False, **options):
        # - uses SmartDict.store which calls _data -> _getdata which gets the key
        if verbose: print "CL.store"
        if self._master and not self._publichash:
            self._publichash = self._storepublic()
        if not (self._master and dontstoremaster):
            super(CommonList,self).store(verbose=verbose, **options)   # Stores privatekey  and sets _hash
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
        Sign and store a StructuredBlock on a list - via the SB's signatures - see add for doing independent of SB

        :param StructuredBlock obj:
        :param verbose:
        :param options:
        :return:
        """
        self.fetch(fetchlist=False) # Check its fetched
        if not self._master:
            raise ForbiddenException(what="Signing a new entry when not a master list")
        # The obj.store stores signatures as well (e.g. see StructuredBlock.store)
        obj.sign(self).store(verbose=verbose, **options)
        return self

    def add(self, obj, verbose=False, **options):
        """
        Add a object, typically MBM or ACL (i.e. not a StructuredBlock) to a List,
        """
        hash = obj if isinstance(obj, basestring) else obj._hash
        from SignedBlock import Signature
        sig = Signature.sign(self, hash, verbose=verbose, **options)
        self.transport.add(hash=hash, date=sig.date,
                   signature=sig.signature, signedby=sig.signedby, verbose=verbose, **options)
        # Caller will probably want to add obj to list , not done here since MB handles differently.


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
    table = "mb"

    def __init__(self, master=False, keypair=None, data=None, hash=None, contenthash=None, contentacl=None, verbose=False, **options):
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
        super(MutableBlock, self).fetch(verbose=verbose, fetchblocks=False, **options)  # Dont fetch old versions
        if len(self._list):
            curr = self._list[-1]
            self._current = curr and curr.fetch() # Fetch current content
        return self # For chaining

    def content(self, verbose=False, **options):
        self.fetch()    # defaults fetchlist=True, fetchblocks=False
        self._current = self._current.fetch()   # To fetch just the current block (the assignment is because will change class)
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

class EncryptionList(CommonList):
    """
    Common class for AccessControlList and KeyChain for things that can handle encryption

    accesskey   Key with which things on this list are encrypted
    From CommonList: keypair, _publichash, _list, _master, name
    """
    pass

class AccessControlList(EncryptionList):
    """
    An AccessControlList is a list for each control domain, with the entries being who has access.

    To create a list, it just requires a key pair, like any other List

    See Authentication.rst
    From EncryptionList: accesskey   Key with which things on this list are encrypted
    From CommonList: keypair, _publichash, _list, _master, name

    """
    table = "acl"

    def add(self, viewerpublichash=None, verbose=False, **options):
        """
        Add a new ACL entry
        Needs publickey of viewer

        :param self:
        :return:
        """
        if verbose: print "AccessControlList.add viewerpublichash=",viewerpublichash
        if not self._master:
            raise ForbiddenException(what="Cant add viewers to ACL copy")
        viewerpublickeypair = KeyPair(hash=viewerpublichash).fetch(verbose=verbose)
        aclinfo = {
            # Need to go B64->binary->encrypt->B64
            "token": viewerpublickeypair.encrypt(base64.urlsafe_b64decode(self.accesskey), b64=True),
            "viewer": viewerpublichash,
        }
        sb = StructuredBlock(data=aclinfo)
        self.signandstore(sb, verbose, **options)
        return self # For chaining

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
        if verbose: print "AccessControlList.tokens decrypt=",decrypt
        self.fetch(verbose=verbose, fetchblocks=True)
        viewerhash = viewerkeypair._hash
        toks = [ a.token for a in self._list if a.fetch().viewer == viewerhash]
        if decrypt:
            toks = [ viewerkeypair.decrypt(str(a), b64=True) for a in toks ]
        return toks

    def decrypt(self, data, viewerkeypair=None, verbose=False):
        """

        :param data: string from json - b64 encrypted
        :param viewerkeypair:
        :param verbose:
        :return:
        """
        #vks = viewerkeypair or AccessControlList.myviewerkeys
        vks = viewerkeypair or KeyChain.myviewerkeys()
        if not isinstance(vks, (list, tuple, set)):
            vks = [ vks ]
        for vk in vks:
            for symkey in self.tokens(viewerkeypair = vk, decrypt=True, verbose=verbose):
                try:
                    r = CryptoLib.sym_decrypt(data, symkey, b64=True) #Exception DecryptionFail
                    return r    # Dont continue to process when find one
                except DecryptionFail as e:  # DecryptionFail but keep going
                    pass    # Ignore if cant decode maybe other keys will work
        raise AuthenticationException(message="ACL.decrypt: No valid keys found")

class KeyChain(EncryptionList):
    """
    A class to hold a list of encrypted Private keys. Control of Privatekey of this gives access to all of the items pointed at.

    From EncryptionList accesskey       Behaves like that of the ACL
    From CommonList: keypair, _publichash, _list, _master, name
    From SmartDict:     _acl            For encrypting the KeyChain itself
    """
    mykeychains = []       # Set with keys we can use
    table = "kc"


    def add(self, obj, verbose=False, **options):
        super(KeyChain, self).add(obj, verbose=verbose, **options)
        self._list.append(obj)

    def decrypt(self, data, verbose=False):
        """

        :param data: String from json, b64 encoded
        :param verbose:
        :return:
        """
        symkey = base64.urlsafe_b64decode(self.accesskey)
        r = CryptoLib.sym_decrypt(data, symkey, b64=True)  # Exception DecryptionFail (would be bad)
        return r

    @classmethod
    def addkeychains(cls, *keychains):
        """
        Add keys I can view under to ACL

        :param keychains:   Array of keychains
        :return:
        """
        cls.mykeychains += keychains

    @classmethod
    def find(cls, publichash, verbose=False, **options):
        kcs = [ kc for kc in cls.mykeychains if kc._publichash == publichash ]
        if verbose and kcs: print "KeyChain.find successful"
        return kcs[0] if kcs else None

    @property
    def accesskey(self):
        return base64.urlsafe_b64encode(self.keypair._key._private)

    def store(self, verbose=False, **options ):
        return super(KeyChain, self).store(verbose=verbose, dontstoremaster=True, **options)  # Stores privatekey  and sets _hash

    def fetch(self, verbose=False, **options):
        return super(KeyChain, self).fetch(fetchBody=False, verbose=verbose, **options)  # Dont fetch body, it wasn't stored

    @classmethod
    def myviewerkeys(cls):
        """
        Find any Viewer Keys on the KeyChains

        :return:
        """
        # Super obscure double loop, but works and fast
        return [ k for kc in cls.mykeychains for k in kc._list if isinstance(k,KeyPair) ]


