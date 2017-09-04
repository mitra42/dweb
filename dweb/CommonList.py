# encoding: utf-8

from CryptoLib import CryptoLib, WordHashKey, PrivateKeyException, AuthenticationException, DecryptionFail, SecurityWarning
from KeyPair import KeyPair
import base64
import nacl.signing
import nacl.encoding
from StructuredBlock import StructuredBlock
from SignedBlock import Signatures
from Errors import ForbiddenException, AssertionFail, ToBeImplementedException
from SmartDict import SmartDict
from Dweb import Dweb
#TODO-BACKPORT - review this file

class CommonList(SmartDict):  # TODO move class to own file
    """
    Encapsulates a list of blocks, which includes MutableBlocks and AccessControlLists etc
    Partially copied to dweb.js.

    {
    keypair: KeyPair           Keys for this list
    _publicurl:                Hash that is used for refering to list - i.e. of public version of it.
    _list: [ StructuredBlock* ] Blocks on this list
    _master bool                True if this is the controlling object, has private keys etc

    From SmartDict: _acl, name
    From Transportable: _data, _url

    """

    # Comments on use of superclass methods without overriding here

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.__dict__)

    def __init__(self, master=False, keypair=None, data=None, url=None, verbose=False, keygen=False, mnemonic=None,
                 **options):  # Note url is of data
        """
        Create and initialize a MutableBlock
        Typically called either with args (master, keypair) if creating, or with data or url to load from dWeb
        Adapted to dweb.js.MutableBlock.constructor
        Exceptions: PrivateKeyException if passed public key and master=True
        :param bool master: True if master for list
        :param KeyPair|str keypair: Keypair or export of Key identifying this list
        :param data: Exported data to import
        :param url: Hash to exported data
        :param keychain: Set to class to use for Key (supports RSA or WordHashKey)
        :param options: Set on SmartDict unless specifically handled here
        """
        # if verbose: print "master=%s, keypair=%s, key=%s, url=%s, verbose=%s, options=%s)" % (master, keypair, key, url, verbose, options)
        self._master = master
        super(CommonList, self).__init__(data=data, url=url, verbose=verbose,
                                         **options)  # Initializes __dict__ via _data -> _setdata
        # if mnemonic:
        #    self.keypair = WordHashKey(mnemonic)
        if keypair:
            self.keypair = keypair
        if keygen or mnemonic:
            self.keypair = KeyPair.keygen(verbose=verbose, mnemonic=mnemonic, keytype=KeyPair.KEYTYPESIGN,
                                          **options)  # Note these options are also set on smartdict, so catch explicitly if known.
        if not self._master:
            self._publicurl = url  # Maybe None.
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
        if dd.get(
                "keypair"):  # Based on whether the CommonList is master, rather than if the key is (key could be master, and CL not)
            if master and not dd.get("_acl") and not self._allowunsafestore:
                raise SecurityWarning(
                    message="Probably shouldnt be storing private key on this " + self.__class__.__name__)  # Can set KeyPair._allowunsafestore to allow this when testing
            dd["keypair"] = dd["keypair"].privateexport if master else dd["keypair"].publicexport
        publicurl = dd.get("_publicurl")
        dd = super(CommonList, self).preflight(dd=dd)  # Will edit dd in place since its a dic,
        if master:  # Only store on Master, on !Master will be None and override storing url as _publicurl
            dd[
                "_publicurl"] = publicurl  # May be None, have to do this AFTER the super call as super filters out "_*"  #TODO-REFACTOR_PUBLICHASH
        return dd

    # def _setdata(self, value):
    #    super(CommonList, self)._setdata(value) # Sets __dict__ from values including keypair via setter
    # _data = property(SmartDict._getdata, SmartDict._setdata)

    def fetch(self, verbose=False, fetchbody=True, fetchlist=True, fetchblocks=False, **options):
        """
        Copied to dweb.js.

        :param bool fetchlist: True (default) will fetch the list (slow), otherwise just gets the keys etc
        :param verbose:
        :param options:
        """
        if fetchbody:
            super(CommonList, self).fetch(verbose=verbose,
                                          **options)  # only fetches if _needsfetch=True, Sets keypair etc via _data -> _setdata,
        if fetchlist:
            # This is ugly - self._publicurl needed for MB-master; self._url&!_master for ACl.!master; keypair for VK
            listurl = self._publicurl or ((not self._master) and self._url) or self.keypair._url
            assert listurl, "Must be a url to look on a list"
            self._list = Signatures.fetch(url=listurl, fetchblocks=fetchblocks, verbose=verbose, **options)
        return self  # for chaining

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
        return acl2._url

    def store(self, verbose=False, dontstoremaster=False, **options):
        # - uses SmartDict.store which calls _data -> _getdata which gets the key
        if verbose: print "CL.store"
        if self._master and not self._publicurl:
            self._publicurl = self._storepublic()
        if not (self._master and dontstoremaster):
            super(CommonList, self).store(verbose=verbose, **options)  # Stores privatekey  and sets _url
        return self

    def publicurl(self, command=None, **options):   #TODO-BACKPORT this looks like xurl, not what we want after backport
        return Dweb.transport(self._publicurl).xurl(self, command=command or "list", url=self._publicurl,
                                  **options)  # , contenttype=self.__getattr__("Content-type"))

    def privateurl(self):  #TODO-BACKPORT this looks like xurl, not what we want after backport
        """
        Get a URL that can be used for edits to the resource
        Side effect of storing the key

        :return:
        """
        #TODO-BACKPORT sure will have different way to get transport
        return self.transport().xurl(self, command="update", contenttype=self._current.__getattr__("Content-type"))
        # TODO-AUTHENTICATION - this is particularly vulnerable w/o authentication as stores PrivateKey in unencrypted form

    def signandstore(self, obj, verbose=False, **options):
        """
        Sign and store a StructuredBlock on a list - via the SB's signatures - see add for doing independent of SB

        :param StructuredBlock obj:
        :param verbose:
        :param options:
        :return:
        """
        self.fetch(fetchlist=False)  # Check its fetched
        if not self._master:
            raise ForbiddenException(what="Signing a new entry when not a master list")
        # The obj.store stores signatures as well (e.g. see StructuredBlock.store)
        obj.sign(self, verbose=verbose).store(verbose=verbose, **options)
        return self

    def add(self, obj, verbose=False, **options):
        """
        Add a object, typically MBM or ACL (i.e. not a StructuredBlock) to a List,
        COPIED TO JS 2017-05-24

        :param obj: Object to store on this list or a url string.
        """
        url = obj if isinstance(obj, basestring) else obj._url
        assert url  # Empty string, or None would be an error
        from SignedBlock import Signature
        sig = Signature.sign(self, url, verbose=verbose, **options)
        Dweb.transport(sig.signedby).add(url=url, date=sig.date,
                           signature=sig.signature, signedby=sig.signedby, verbose=verbose, **options)
        return sig  # Typically for adding to local copy of list
        # Caller will probably want to add obj to list , not done here since MB handles differently.

class EncryptionList(CommonList):
    """
    Common class for AccessControlList and KeyChain for things that can handle encryption

    accesskey   Key with which things on this list are encrypted
    From CommonList: keypair, _publicurl, _list, _master, name
    """
    pass