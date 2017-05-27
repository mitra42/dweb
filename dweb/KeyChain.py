from CryptoLib import CryptoLib, KeyPair, WordHashKey
import nacl.signing
import nacl.encoding
from misc import ToBeImplementedException
from Dweb import Dweb
from CommonList import EncryptionList

class KeyChain(EncryptionList):  # TODO move to own file
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
        if verbose: print "KeyChain.new mnemonic=", mnemonic, "keygen=", keygen
        # master=False, keypair=None, data=None, hash=None, verbose=False, keygen=False, mnemonic=None, **options):  # Note hash is of data
        kc = cls(mnemonic=mnemonic, keygen=keygen, verbose=verbose, name=name)  # Note only fetches if name matches
        kc.store(verbose=verbose)  # Set the _publichash
        KeyChain.addkeychains(kc)
        kc.fetch(verbose=verbose, fetchlist=True, fetchblocks=False)  # Was fetching blocks, but now done by "keys"
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
        COPIED TO JS 2017-05-24

        :param obj: 
        :param verbose: 
        :param options: 
        :return: 
        """
        sig = super(KeyChain, self).add(obj, verbose=verbose, **options)  # Adds to dWeb list
        self._list.append(sig)

    def encrypt(self, res, b64=False):
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
    def accesskey(
            self):  # TODO-WORDHASHKEY any use of this in KeyChain should probably just use the PrivateKey to encrypt rather than symkey
        key = self.keypair._key
        if isinstance(key, WordHashKey):  # Needs own case as privateexport is blocked
            return CryptoLib.b64enc(self.keypair._key._private)
        elif isinstance(key, nacl.signing.SigningKey):
            return self.keypair._key.encode(nacl.encoding.URLSafeBase64Encoder)
        else:
            raise ToBeImplementedException(name="accesskey for " + key.__class__.__name__)

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
        kcs = [kc for kc in Dweb.keychains if kc._publichash == publichash]
        if verbose and kcs: print "KeyChain.find successful"
        return kcs[0] if kcs else None

    def store(self, verbose=False, **options):
        return super(KeyChain, self).store(verbose=verbose, dontstoremaster=True,
                                           **options)  # Stores public version and sets _publichash

    def fetch(self, verbose=False, **options):
        return super(KeyChain, self).fetch(fetchbody=False, verbose=verbose,
                                           **options)  # Dont fetch body, it wasn't stored, but get list

    @classmethod
    def _findbyclass(cls, clstarget):
        # Super obscure double loop, but works and fast
        return [k for kc in Dweb.keychains for k in kc.keys if isinstance(k, clstarget)]

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
