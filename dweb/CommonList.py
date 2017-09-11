# encoding: utf-8

from KeyPair import KeyPair
import base64
import nacl.signing
import nacl.encoding
from StructuredBlock import StructuredBlock
from Signature import Signature
from Errors import ForbiddenException, SecurityWarning, CodingException
from SmartDict import SmartDict
from Dweb import Dweb

class CommonList(SmartDict):
    """
    CommonList is a superclass for anything that manages a storable list of other urls
    e.g. MutableBlock, KeyChain, AccessControlList

    Fields:
    keypair         Holds a KeyPair used to sign items
    _list           Holds an array of signatures of items put on the list
    _master         True if this is a master list, i.e. can add things
    _publicurl     Holds the url of publicly available version of the list.
    _allowunsafestore True if should override protection against storing unencrypted private keys (usually only during testing)
    dontstoremaster True if should not store master key
    """
    table = "cl"

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.__dict__)

    def __init__(self, data=None, master=None, key=None, verbose=False, **options):
        """
        Create a new instance of CommonList

        :param url: url of list to fetch from Dweb
        :param data: json string or dict to load fields from
        :param master: boolean, true if should create a master list with private key etc
        :param key: A KeyPair, or a dict of options for creating a key: valid = mnemonic, seed, keygen:true
            keygen: boolean, true means it should generate a key
            mnemonic: BIP39 string to use as a mnemonic to generate the key - TODO not implemented (in JS) yet
            seed: Seed to key generation algorithm
        :param options: dict that overrides any fields of data
        """
        super(CommonList, self).__init__(data=data, verbose=verbose, **options)  # Initializes __dict__ via _data -> _setdata
        if key:
            self._setkeypair(key, verbose)
        #Note this must be AFTER _setkeypair since that sets based on keypair found and _storepublic for example wants to force !master
        if master is None:
            self._master = self.keypair.has_private()
        else:
            self._master = master
        if (not self._master) and (not self._publicurl):
            #We aren't master, so publicurl is same as url - note URL will only have been set if constructor called from SmartDict.fetch
            self._publicurl = self._url

    def _setdata(self, value):
        super(CommonList, self)._setdata(value)
        if not self._list:
            self._list = [] # Clear list (not undefined field) if setting data

    @classmethod
    def keytype(self):
        """
        Return the type of key to use from Dweb.KeyPair.KEYTYPE* constants
        By default its KEYTYPESIGN, but KeyChain subclasses

        :return: constant
        """
        return KeyPair.KEYTYPESIGN

    def __setattr__(self, name, value):
        """
        Set a field of the object, this provides the equivalent of Python setters and getters.
        Call chain is ...  or constructor > _setdata > _setproperties > __setattr__
        Subclasses SmartDict

        Default passes "keypair" to _setkeypair
        :param name: string - name of attribute to set
        :param value: anything but usually string from retrieving - what to set name to.
        """
        verbose = False
        if (name == "keypair"):
            self._setkeypair(value, verbose)
        else:
            super(CommonList, self).__setattr__(name, value)

    def _setkeypair(self, value, verbose=False):
        """
        Set the keypair attribute, converts value into KeyPair if not already
        Call chain is ...  or constructor > _setdata > _setproperties > __setattr__ > _setkeypair
        Sets _master if value has a private key (note that is overridden in the constructor)

        :param value: KeyPair, or Dict like _key field of KeyPair
        """
        if value and not (isinstance(value, KeyPair)):
            value = KeyPair({ "key": value }, verbose) # Note ignoring keytype for now
        super(CommonList, self).__setattr__("keypair", value)
        self._master = value and value.has_private()

    def preflight(self, dd):
        """
        Prepare a dictionary of data for storage,
        Subclasses SmartDict to:
            convert the keypair for export and check not unintentionally exporting a unencrypted public key
            ensure that _publicurl is stored (by default it would be removed)
        and subclassed by AccessControlList

        :param dd: dict of attributes of this, possibly changed by superclass
        :return: dict of attributes ready for storage.
        """
        if dd.get("keypair"):
            if dd.get("_master") and not dd.get("_acl") and not self._allowunsafestore:
                raise SecurityWarning(message="Probably shouldnt be storing private key"+repr(dd))
            dd["keypair"] = dd["keypair"].privateexport() if dd["_master"] else dd["keypair"].publicexport()
        # Note same code for publicurl in CommonList & KeyPair
        publicurl = dd.get("_publicurl") # Save before preflight
        master = dd.get("_master")
        dd = super(CommonList, self).preflight(dd=dd)  #Edits dd in place
        if master: # Only store on Master, on !Master will be None and override storing url as _publicurl
            dd["_publicurl"] = publicurl  # May be None, have to do this AFTER the super call as super filters out "_*"
        return dd

    def fetchlist(self, verbose=False):
        """
        Load the list from the Dweb,
        Use list_then_elements instead if wish to load the individual items in the list
        """
        if not self._publicurl:
            self._storepublic(verbose)
        lines = self.transport().rawlist(self._publicurl, verbose)
        # lines should be an array
        if verbose: print("CommonList:fetchlist.success", self._url, "len=", lines.length);
        self._list = [Signature(l, verbose) for l in lines]   #Turn each line into a Signature

    def list_then_elements(self, verbose=False):
        """
        Utility function to simplify nested functions, fetches body, list and each element in the list.

        :resolves: list of objects signed and added to the list
        """
        self.fetchlist(verbose)
        # Return is [result of fetchdata] which is [new objs] (suitable for storing in keys etc)
        return [ sig.fetchdata(verbose)
            for sig in Signature.filterduplicates(self._list) ] #Dont load multiple copies of items on list (might need to be an option?)

    def _storepublic(self, verbose=False):
        """
        Store a public version of the object, just stores name field and public key
        Typically subclassed to save specific fields
        Note that this returns immediately after setting url, so caller may not need to wait for success
        """
        #CL(data, master, key, verbose, options)
        cl = self.__class__(data=None, master=False, key=self.keypair, verbose=verbose, name=self.name);
        cl.store(verbose)    # sets _url
        self._publicurl = cl._url

    def store(self, verbose=False):
        """
            Store on Dweb, if _master will ensure that stores a public version as well, and saves in _publicurl
            Will store master unless dontstoremaster is set.
        """
        if self._master and not self._publicurl:
            self._storepublic(verbose) # Stores asynchronously, but _publicurl set immediately
        if not (self._master and self.dontstoremaster):
            super(CommonList, self).store(verbose);    # Transportable.store(verbose)


    #publicurl() { console.assert(false, "XXX Undefined function CommonList.publicurl"); }   // For access via web
    #privateurl() { console.assert(false, "XXX Undefined function CommonList.privateurl"); }   // For access via web

    def append(self, obj, verbose=False): # Allow JS style push or Python style append
        return self.push(obj, verbose)

    def push(self, obj, verbose=False):
        """
         Equivalent to Array.push but returns a promise because asynchronous
         Sign and store a object on a list, stores both locally on _list and sends to Dweb

         :param obj: Should be subclass of SmartDict, (Block is not supported), can be URL of such an obj
         :returns: sig created in process - for adding to lists etc.
         :throws:   ForbiddenException if not master;
        """
        if not obj:
            raise CodingException(message="CL.push obj should never be non-empty")
        self.store(verbose)    # Make sure stored
        if not isinstance(obj, basestring):
            obj.store(verbose)
        if not (self._master and self.keypair):
            raise ForbiddenException(message="Signing a new entry when not a master list")
        url = obj if isinstance(obj, basestring) else obj._url
        sig = self.sign(url, verbose)
        self._list.append(sig);     # Keep copy locally on _list
        self.add(sig, verbose)      # Add to list in dweb
        return sig

    def sign(self, url, verbose=False):
        """
        Utility function to create a signature - used by push and in KeyChain.push
        :param url:    URL of object to sign
        :returns:       Signature
        """
        if not url: raise CodingException(message="Empty url is a coding error")
        if not self._master: raise ForbiddenException(message="Must be master to sign something")
        sig = Signature.sign(self, url, verbose); # returns a new Signature
        assert sig.signature, "Must be a signature"
        return sig

    def add(self, sig, verbose=False):
        """
        Add a signature to the Dweb for this list

        :param sig: Signature
        :resolves:  undefined
        """
        if not sig: raise CodingException(message="CommonList.add is meaningless without a sig")
        return self.transport().rawadd(sig.url, sig.date, sig.signature, sig.signedby, verbose)

    def verify(self, sig, verbose=False):
        return self.keypair.verify(signable=sig.signable(), urlb64sig=sig.signature)


    """
    # Will only work if transport can do callbacks. HTTP can't Local can't and IPFS not implemented
    listmonitor(self, callback, verbose) {  #TODO-BACKPORT support callbacks
        self.transport().listmonitor(self._publicurl,
             (obj) => {
                if verbose: print("CL.listmonitor",self._publicurl,"Added",obj)
                sig = Signature(obj, verbose)
                if not othersig.signature in [ sig.signature for sig in self._list ]: #Check not duplicate (esp of locally pushed one
                    self._list.append(sig)
                callback(sig);
             }
        )
    """


"""
#OBS - not used in JS, so returning as using array - maybe copied when implement MutableBlock & StructuredBlock
class Signatures(list):
    #A list of Signature (note on Javascript this is just a list, and earliest is  static methods on the Signature class)

    def earliest(self):
        #:return: earliest date of a list of signatures
        return min(sig.date for sig in self)

    def verify(self, url=None):
        #:param url: url to check (None to check url in sigs)
        #:return: True if all signatures verify
        return all(s.verify(url=url) for s in self)

    @classmethod
    def fetch(cls, url=None, verbose=False, fetchblocks=False, **options):
        "-""
        Find all the related Signatures.
        Exception: TransportURLNotFound if empty or bad URL

        :param url:
        :param verbose:
        :param options:
        :return: SignedBlocks which is a list of StructuredBlock
        "-""
        #key = KeyPair.export(publickey) if publickey is not None else None,
        assert url is not None
        if verbose: print "SignedBlocks.fetch looking for url=",url,"fetchblocks=", fetchblocks
        try:
            lines = Dweb.transport(url).rawlist(url=url, verbose=verbose, **options)
        except (TransportURLNotFound, TransportFileNotFound) as e:
            return Signatures([])    # Its ok to fail as list may be empty
        else:
            if verbose: print "Signatures.fetch found ",len(lines) if lines else None
            results = {}
            sigs = Signatures(Signature(s) for s in lines )
            if fetchblocks:
                raise ToBeImplementedException(name="fetchblocks for Signatures")    # Note havent defined a way to store the block on the sig
            return Signatures([ s for s in sigs if KeyPair.verify(s) ])

    def blocks(self, fetchblocks=True, verbose=False):
        results = {}
        for s in self:
            url = s.url
            if not results.get(url, None):

                if fetchblocks:
                    results[url] = UnknownBlock(url=url).fetch()  # We don't know its a SB, UnknownBlock.fetch() will convert
                else:
                    results[url] = UnknownBlock(url=url)  # We don't know its a SB
            if not results[url]._signatures:
                results[url]._signatures = Signatures([])
            results[url]._signatures.append(s)
        return [ results[url] for url in results]

    def latest(self):
        dated = self._dated()
        latest = max(key for key in dated)      # Find date of SB with latest first sig
        return dated[latest]

"""
