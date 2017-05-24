# encoding: utf-8

from CryptoLib import CryptoLib, KeyPair, WordHashKey, PrivateKeyException, AuthenticationException, DecryptionFail, SecurityWarning
import base64
import nacl.signing
import nacl.encoding
from StructuredBlock import StructuredBlock
from SignedBlock import Signatures
from misc import ForbiddenException, _print, AssertionFail, ToBeImplementedException
from CommonBlock import SmartDict
from Dweb import Dweb


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
        :param keychain: Set to class to use for Key (supports RSA or WordHashKey)
        :param options: Set on SmartDict unless specifically handled here
        """
        #if verbose: print "master=%s, keypair=%s, key=%s, hash=%s, verbose=%s, options=%s)" % (master, keypair, key, hash, verbose, options)
        self._master = master
        super(CommonList, self).__init__(data=data, hash=hash, verbose=verbose, **options)  # Initializes __dict__ via _data -> _setdata
        #if mnemonic:
        #    self.keypair = WordHashKey(mnemonic)
        if keypair:
            self.keypair = keypair
        if keygen or mnemonic:
                self.keypair = KeyPair.keygen(verbose=verbose, mnemonic=mnemonic, keytype=KeyPair.KEYTYPESIGN, **options)   # Note these options are also set on smartdict, so catch explicitly if known.
        if not self._master:
            self._publichash = hash # Maybe None.
        self._list = Signatures([])

    @property
    def keypair(self):
        return self.__dict__.get("keypair")

    @keypair.setter
    def keypair(self, value):
        if value and not isinstance(value, KeyPair):
            value = KeyPair(key=value)
        self.__dict__["keypair"] = value
        self._master = value and value.has_private()


    def preflight(self, dd):
        master = dd["_master"]  # Use master from dd if modified
        if dd.get("keypair"):   # Based on whether the CommonList is master, rather than if the key is (key could be master, and CL not)
            if master and not dd.get("_acl") and not self._allowunsafestore:
                raise SecurityWarning(message="Probably shouldnt be storing private key on this "+self.__class__.__name__)  # Can set KeyPair._allowunsafestore to allow this when testing
            dd["keypair"] = dd["keypair"].privateexport if master else dd["keypair"].publicexport
        publichash = dd.get("_publichash")
        dd = super(CommonList, self).preflight(dd=dd)  # Will edit dd in place since its a dic,
        if master:  # Only store on Master, on !Master will be None and override storing hash as _publichash
            dd["_publichash"] = publichash   # May be None, have to do this AFTER the super call as super filters out "_*"  #TODO-REFACTOR_PUBLICHASH
        return dd


    #def _setdata(self, value):
    #    super(CommonList, self)._setdata(value) # Sets __dict__ from values including keypair via setter
    #_data = property(SmartDict._getdata, SmartDict._setdata)

    def fetch(self, verbose=False, fetchbody=True, fetchlist=True, fetchblocks=False, **options):
        """
        Copied to dweb.js.

        :param bool fetchlist: True (default) will fetch the list (slow), otherwise just gets the keys etc
        :param verbose:
        :param options:
        """
        if fetchbody:
            super(CommonList, self).fetch(verbose=verbose, **options)   # only fetches if _needsfetch=True, Sets keypair etc via _data -> _setdata,
        if fetchlist:
            # This is ugly - self._publichash needed for MB-master; self._hash&!_master for ACl.!master; keypair for VK
            listhash = self._publichash or ((not self._master) and self._hash) or self.keypair._hash
            assert listhash,"Must be a hash to look on a list"
            self._list = Signatures.fetch(hash=listhash, fetchblocks=fetchblocks, verbose=verbose, **options)
        return self # for chaining

    def _storepublic(self, verbose=False, **options):
        """
        Store a publicly visible version of this list. 
        
        :param verbose: 
        :param options: 
        :return: 
        """
        acl2 = self.__class__(keypair=self.keypair, name=self.name)
        acl2._master = False
        acl2.store(verbose=verbose, **options)  # Note will call preflight with _master = False
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
        return Dweb.transport.url(self, command=command or "list", hash=self._publichash, **options) #, contenttype=self.__getattr__("Content-type"))

    def privateurl(self):
        """
        Get a URL that can be used for edits to the resource
        Side effect of storing the key

        :return:
        """
        return Dweb.transport.url(self, command="update", contenttype=self._current.__getattr__("Content-type"))
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
        obj.sign(self, verbose=verbose).store(verbose=verbose, **options)
        return self

    def add(self, obj, verbose=False, **options):
        """
        Add a object, typically MBM or ACL (i.e. not a StructuredBlock) to a List,

        :param obj: Object to store on this list or a hash string.
        """
        hash = obj if isinstance(obj, basestring) else obj._hash
        assert hash # Empty string, or None would be an error
        from SignedBlock import Signature
        sig = Signature.sign(self, hash, verbose=verbose, **options)
        Dweb.transport.add(hash=hash, date=sig.date,
                   signature=sig.signature, signedby=sig.signedby, verbose=verbose, **options)
        return sig  # Typically for adding to local copy of list
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

    def __init__(self, master=False, keypair=None, data=None, hash=None, contenthash=None, contentacl=None, keygen=False, verbose=False, **options):
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
        if verbose: print "MutableBlock( keypair=",keypair, "data=",data, "hash=", hash, "keygen=", keygen, "options=", options,")"
        super(MutableBlock, self).__init__(master=master, keypair=keypair, data=data, hash=hash, keygen=keygen, verbose=verbose, **options)
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
            sig = self._list[-1] # Note this is the last of the list, if lists can get disordered then may need to sort
            self._current = sig and sig.block() # Fetch current content
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


    @classmethod
    def new(cls, acl=None, contentacl=None, name=None, _allowunsafestore=False, content=None, signandstore=False, verbose=False, **options):
        """
        Utility function to allow creation of MB in one step

        :param acl:             Set to an AccessControlList or KeyChain if storing encrypted (normal)
        :param contentacl:      Set to enryption for content
        :param name:            Name of block (optional)
        :param _allowunsafestore: Set to True if not setting acl, otherwise wont allow storage
        :param content:         Initial data for content
        :param verbose:
        :param signandstore:    Set to True if want to sign and store content, can do later
        :param options:
        :return:
        """
        # See test_mutableblock for canonical testing of this
        if verbose: print "MutableBlock.new: Creating MutableBlock", name
        mblockm = cls(name=name, master=True, keygen=True, contentacl=contentacl, verbose=verbose)  # Create a new block with a new key
        mblockm._acl = acl              # Secure it
        mblockm._current.data = content  # Preload with data in _current.data
        if _allowunsafestore:
            mblockm._allowunsafestore = True
            mblockm.keypair._allowunsafestore = True
        mblockm.store()
        if signandstore and content:
            mblockm.signandstore(verbose=verbose)  # Sign it - this publishes it
        if verbose: print "Created MutableBlock hash=", mblockm._hash
        return mblockm


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

    def preflight(self, dd):   #TODO-REFACTOR all preflight to have dd defined by caller (store)
        if (not self._master) and isinstance(self.keypair._key, nacl.signing.SigningKey):
            dd["naclpublic"] = dd.get("naclpublic") or dd["keypair"].naclpublicexport()   # Store naclpublic for verification
        # Super has to come after above as overrights keypair, also cant put in CommonList as MB's dont have a naclpublic and are only used for signing, not encryption
        return super(AccessControlList, self).preflight(dd)

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
            "token": viewerpublickeypair.encrypt(CryptoLib.b64dec(self.accesskey), b64=True, signer=self),
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
        self.fetch(verbose=verbose, fetchblocks=False)
        viewerhash = viewerkeypair._hash
        toks = [ a.block().token for a in self._list if a.block().viewer == viewerhash ]
        if decrypt:
            toks = [ viewerkeypair.decrypt(str(a), b64=True, signer=self) for a in toks ]
        return toks

    def encrypt (self, res, b64=False):
        """
        Encrypt an object (usually represented by the json string). Pair of .decrypt()

        :param res: The material to encrypt, usually JSON but could probably also be opaque bytes
        :param b64: 
        :return: 
        """
        return CryptoLib.sym_encrypt(res, CryptoLib.b64dec(self.accesskey), b64=b64)

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

class KeyChain(EncryptionList): //TODO move to own file
    """
    A class to hold a list of encrypted Private keys. Control of Privatekey of this gives access to all of the items pointed at.

    From EncryptionList accesskey       Behaves like that of the ACL
    From CommonList: keypair, _publichash, _list, _master, name
    From SmartDict:     _acl            For encrypting the KeyChain itself
    """
    table = "kc"

    @classmethod
    def new(cls, mnemonic=None, keygen=False, name="My KeyChain", verbose=False):
        """
        Utility function grouping the most common things done with a new key
        Creates the key, stores if reqd, fetches anything already on it

        :param mnemonic:    Words to translate into keypair
        :param bool keygen: If True generate a key
        """
        if verbose: print "KeyChain.new mnemonic=",mnemonic,"keygen=",keygen
        # master=False, keypair=None, data=None, hash=None, verbose=False, keygen=False, mnemonic=None, **options):  # Note hash is of data
        kc = cls(mnemonic=mnemonic, keygen=keygen, verbose=verbose, name=name)  # Note only fetches if name matches
        kc.store(verbose=verbose)   # Set the _publichash
        KeyChain.addkeychains(kc)
        kc.fetch(verbose=verbose, fetchlist=True, fetchblocks=False)    # Was fetching blocks, but now done by "keys"
        if verbose: print "Created keychain for:", kc.keypair.mnemonic
        if verbose and not mnemonic: print "Record these words if you want to access again"
        return kc

    @property
    def keys(self):
        if not self._keys:
            self._keys = self._list.blocks()
        return self._keys

    def add(self, obj, verbose=False, **options):
        """
        Add a obj (usually a MutableBlock or a ViewerKey) to the keychain. by signing with this key.  
        Item should usually itself be encrypted (by setting its _acl field)
        
        :param obj: 
        :param verbose: 
        :param options: 
        :return: 
        """
        sig = super(KeyChain, self).add(obj, verbose=verbose, **options)  # Adds to dWeb list
        self._list.append(sig)

    def encrypt (self, res, b64=False):
        """
        Encrypt an object (usually represented by the json string). Pair of .decrypt()

        :param res: The material to encrypt, usually JSON but could probably also be opaque bytes
        :param b64: 
        :return: 
        """
        key = self.keypair._key
        if isinstance(key, WordHashKey):
            return CryptoLib.sym_encrypt(res, CryptoLib.b64dec(self.accesskey), b64=b64)
        elif isinstance(key, nacl.signing.SigningKey):
            return self.keypair.encrypt(res, b64=b64, signer=self)
        else:
            raise ToBeImplementedException(name="Keypair.encrypt for " + key.__class__.__name__)

    def decrypt(self, data, verbose=False):
        """

        :param data: String from json, b64 encoded
        :param verbose:
        :return:
        """
        key = self.keypair._key
        if isinstance(key, WordHashKey):
            symkey = CryptoLib.b64dec(self.accesskey)
            return CryptoLib.sym_decrypt(data, symkey, b64=True)  # Exception DecryptionFail (would be bad)
        elif isinstance(key, nacl.signing.SigningKey):
            return self.keypair.decrypt(data, b64=True, signer=self)
        else:
            raise ToBeImplementedException(name="Keypair.decrypt for " + key.__class__.__name__)

    @property
    def accesskey(self):    #TODO-WORDHASHKEY any use of this in KeyChain should probably just use the PrivateKey to encrypt rather than symkey
        key = self.keypair._key
        if isinstance(key, WordHashKey):    # Needs own case as privateexport is blocked
            return CryptoLib.b64enc(self.keypair._key._private)
        elif isinstance(key, nacl.signing.SigningKey):
            return self.keypair._key.encode(nacl.encoding.URLSafeBase64Encoder)
        else:
            raise ToBeImplementedException(name="accesskey for "+key.__class__.__name__)


    @classmethod
    def addkeychains(cls, *keychains):
        """
        Add keys I can view under to ACL (note *keychains means even with single argument keychains is an array)

        :param keychains:   Array of keychains
        :return:
        """
        Dweb.keychains += keychains

    @classmethod
    def find(cls, publichash, verbose=False, **options):
        kcs = [ kc for kc in Dweb.keychains if kc._publichash == publichash ]
        if verbose and kcs: print "KeyChain.find successful"
        return kcs[0] if kcs else None

    def store(self, verbose=False, **options ):
        return super(KeyChain, self).store(verbose=verbose, dontstoremaster=True, **options)  # Stores public version and sets _publichash

    def fetch(self, verbose=False, **options):
        return super(KeyChain, self).fetch(fetchbody=False, verbose=verbose, **options)  # Dont fetch body, it wasn't stored, but get list

    @classmethod
    def _findbyclass(cls, clstarget):
        # Super obscure double loop, but works and fast
        return [ k for kc in Dweb.keychains for k in kc.keys if isinstance(k,clstarget) ]

    @classmethod
    def myviewerkeys(cls):
        """
        Find any Viewer Keys on the KeyChains

        :return:
        """
        return cls._findbyclass(KeyPair)

    @classmethod
    def mymutableBlocks(cls):
        """
        Find any Mutable Blocks Keys on the KeyChains

        :return:
        """
        return cls._findbyclass(MutableBlock)
