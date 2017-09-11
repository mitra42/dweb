from KeyPair import KeyPair
import nacl.signing
import nacl.encoding
from Errors import ToBeImplementedException, EncryptionException, CodingException
from Dweb import Dweb, consolearr
from CommonList import CommonList
from json import dumps

class KeyChain(CommonList):  # TODO move to own file
    """
    KeyChain extends CommonList to store a users keys, MutableBlocks and AccessControlLists

    Fields:
    _keys:  Array of keys (the signed objects on the list)
    """
    table = "kc"

    def __init__(self, data=None, master=False, key=None, verbose=False):
        self._keys = [] # Before super as may be overritten by data (unlikely since starts with '_'
        super(KeyChain, self).__init__(data=data, master=master, key=key, verbose=verbose)

    @classmethod
    def new(cls, data=None, key=None, verbose=False):
        """
        Create a new KeyChain object based on a new or existing key.
        Store and add to the Dweb.keychains, list any elements already on the KeyChain (relevant for existing keys)
        data, key:  See CommonList for parameters
        returns:    KeyChain created
        """
        kc = cls(data=data, master=True, key=key, verbose=verbose)
        kc.store(verbose)
        KeyChain.addkeychains(kc)
        kc.list_then_elements(verbose)
        return kc

    def keytype(self):
        return KeyPair.KEYTYPESIGNANDENCRYPT

    def list_then_elements(self, verbose=False):
        """
        Subclasses CommonList to store elements in a _keys array.

        returns:    Array of KeyPair
        """
        self._keys = super(KeyChain,self).list_then_elements(verbose)
        if (verbose): print "KC.list_then_elements Got keys", consolearr(self._keys)
        return self._keys


    def encrypt(self, res, b64=False):
        """
        Encrypt an object (usually represented by the json string). Pair of .decrypt()

        :param res: The material to encrypt, usually JSON but could probably also be opaque bytes
        :param b64: True if result wanted in urlsafebase64 (usually)
        :return:    Data encrypted by Public Key of this KeyChain.
        """
        return self.keypair.encrypt(res, b64=b64, signer=self)

    def decrypt(self, data, verbose=False):
        """
        Decrypt data with this KeyChain - pair of .encrypt()
        Chain is SD.fetch > SD.decryptdata > ACL|KC.decrypt, then SD.setdata

        :param data: String from json, b64 encoded
        :return: decrypted text as string
        :throws: :throws: EncryptionException if no encrypt.privateKey, CodingError if !data
        """
        if not self.keypair._key["encrypt"]:
            raise EncryptionException(message="No decryption key in"+dumps(self.keypair._key))
        return self.keypair.decrypt(data, self, "text") #data, signer, outputformat - Throws EnryptionException if no encrypt.privateKey, CodingError if !data

    def accesskey(self):
        raise CodingException(message="KeyChain doesnt have an accesskey")

    @classmethod
    def addkeychains(cls, keychains):
        """
        Add keys I can use for viewing to Dweb.keychains where it will be iterated over during decryption.

        :param keychains:   keychain or Array of keychains
        """
        if isinstance(keychains, (list, tuple)):
            Dweb.keychains += keychains
        else:
            Dweb.keychains.append(keychains)

    def _storepublic(self, verbose=False):
        """
        Subclasses CommonList._storepublic
        Store a publicly viewable version of KeyChain - note the keys should be encrypted
        Note - does not return a promise, the store is happening in the background
        Sets this_publicurl to the URL of this stored version.
        """
        if (verbose): print "KeyChain._storepublic"
        kc = KeyChain({name: self.name}, false, self.keypair, verbose)
        kc.store(verbose)
        self._publicurl = kc._url

    def store(self, verbose=False):
        """
        Subclasses CommonList.store
        Unlike other store this ONLY stores the public version, and sets the _publicurl, on the assumption that the private key of a KeyChain should never be stored.
        Private/master version should never be stored since the KeyChain is itself the encryption root.
        """
        self.dontstoremaster = true    #Make sure store only stores public version
        return super(KeyChain, self).store(verbose)   #Stores public version and sets _publicurl


    @staticmethod
    def keychains_find(dict, verbose):
        """
        Locate a needed KeyChain on Dweb.keychains by some filter.

        :param dict:    dictionary to check against the keychain (see CommonList.match() for interpretation
        :return:        AccessControlList or KeyChain or None
        """
        kcs = [kc for kc in Dweb.keychains if kc.match(dict)]  # Empty string if
        return kcs[0] if kcs else None

    @staticmethod
    def mykeys(clstarget):
        """
        Utility function to find any keys in any of Dweb.keychains for the target class.

        clstarget:  Class to search Dweb.keychains for, KeyPair, or something with a KeyPair e.g. subclass of CommonList(ACL, MB)
        returns:    (possibly empty) array of KeyPair or CommonList
        """
        #Dweb.keychains is an array of arrays so have to flatten the result - super obscure python but works and fast
        return [key for kc in Dweb.keychains for key in kc._keys if isinstance(key, clstarget)]