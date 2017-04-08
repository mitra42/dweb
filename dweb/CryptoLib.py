# encoding: utf-8

from json import dumps, loads
import base64
import hashlib
from datetime import datetime
from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
import os
from mnemonic import Mnemonic

from misc import MyBaseException, ToBeImplementedException
import sha3 # To add to hashlib
from multihash import encode, SHA1,SHA2_256, SHA2_512, SHA3
from CommonBlock import Transportable, SmartDict
from Dweb import Dweb

class PrivateKeyException(MyBaseException):
    """
    Raised when some code has not been implemented yet
    """
    httperror = 500
    msg = "Operation requires Private Key, but only Public available."

class AuthenticationException(MyBaseException):
    """
    Raised when some code has not been implemented yet
    """
    httperror = 500 #TODO-AUTHENTICATON - which code
    msg = "Authentication Exception: {message}"

class DecryptionFail(MyBaseException):
    """
    Raised if decrypytion failed - this could be cos its the wrong (e.g. old) key
    """
    msg = "Decryption fail"

class SecurityWarning(MyBaseException):
    msg = "Security warning: {message}"

class CryptoLib(object):
    """
    Encapsulate all the Crypto functions in one place so can revise independently of rest of dweb

    # See http://stackoverflow.com/questions/28426102/python-crypto-rsa-public-private-key-with-large-file
    # See http://pycryptodome.readthedocs.io/en/latest/src/examples.html for example using AES+RSA
    """

    @staticmethod
    #def Curlhash(data, hashscheme="SHA3256B64URL", **options):
    def Curlhash(data, hashscheme="SHA3256B64URL", **options):

        """
        Obsolete version pre multihash

        :param data: Any length and combination of bytes
        :return: URL and Filename safe string   hashname.b64encoding
        """
        if hashscheme == "SHA1B64URL":
            return "SHA1B64URL." + base64.urlsafe_b64encode(hashlib.sha1(data).digest())
        elif hashscheme == "SHA3256B64URL":
            return "SHA3256B64URL." + base64.urlsafe_b64encode(hashlib.sha3_256(data).digest())
        elif hashscheme == "SHA3512B64URL":
            return "SHA3512B64URL." + base64.urlsafe_b64encode(hashlib.sha3_512(data).digest())
        else:
            raise ToBeImplementedException(name="CryptoLib.Curlhash for hashscheme="+hashscheme)

    @staticmethod
    def Multihash_Curlhash(data, hashscheme="SHA2256B64URL", **options):

        """
        This version uses multihash, which unfortunately doesnt work on larger than 127 strings or on SHA3

        :param data: Any length and combination of bytes
        :return: URL and Filename safe string   hashname.b64encoding
        """
        if hashscheme == "SHA2256B64URL":
            return "SHA1B64URL." + base64.urlsafe_b64encode(encode(data, SHA1))
        elif hashscheme == "SHA2256B64URL":
            return "SHA2256B64URL." + base64.urlsafe_b64encode(encode(data, SHA2_256))
        elif hashscheme == "SHA2512B64URL":
            return "SHA2512B64URL." + base64.urlsafe_b64encode(encode(data, SHA2_512))
        elif hashscheme == "SHA3512B64URL":
            return "SHA3512B64URL." + base64.urlsafe_b64encode(encode(data, SHA3))
        else:
            raise ToBeImplementedException(name="CryptoLib.Curlhash for hashscheme=" + hashscheme)

    @staticmethod
    def _signable(date, data):
        """
        Returns a string suitable for signing and dating, current imp includes date and storage hash of data.
        Called by signature, so that same thing signed as compared

        :param date: Date on which it was signed
        :param data: Storage hash of data signed (as returned by Transport layer)
        :return: Signable or comparable string
        """
        return date.isoformat() + data

    @staticmethod
    def signature(keypair, date, data, verbose=False, **options):
        """
        Pair of verify(), signs date and data using public key function.

        :param keypair: Key that be used for signture
        :param date: Date that signing (usually now)
        :return: signature that can be verified with verify
        """
        #TODO-AUTHENTICATION - replace with better signing/verification e.g. from http://pydoc.net/Python/pycrypto/2.6.1/Crypto.Signature.PKCS1_v1_5/
        #TODO-AUTHENTICATION - note this will require reworking WordHash.decrypt
        return base64.urlsafe_b64encode(keypair.private.decrypt(CryptoLib._signable(date, data)))

    @staticmethod
    def verify(sig, hash=None): # { publickey=None, signature=None, date=None, hash=None, **unused }
        """
        Pair of signature(), compares signature and date against encrypted data.
        Typically called with \*\*block where block is a signature dictionary read from Transport with date transformed to datetime.

        :param publickey: String as exported by RSA.exportKey #TODO-CRYPT make paired function
        :param signature: Signature to decrypt
        :param date: Date it was signed
        :param hash: Unsigned to check against sig
        :return:
        """
        from MutableBlock import CommonList
        cl = CommonList(hash=sig.signedby).fetch(fetchlist=False)
        # Dont know what kind of list - e.g. MutableBlock or AccessControlList but dont care as only use keys
        keypair = cl.keypair    # Sideeffect of loading from dweb
        #b64decode requires a str, but signature may be unicode
        #TODO-AUTHENTICATION - replace with better signing/verification e.g. from http://pydoc.net/Python/pycrypto/2.6.1/Crypto.Signature.PKCS1_v1_5/
        #TODO-AUTHENTICATION - note this will require reworking WordHash.decrypt
        check = CryptoLib._signable(sig.date, hash or sig.hash)
        sigtocheck = base64.urlsafe_b64decode(str(sig.signature))
        if isinstance(keypair._key, RSA._RSAobj):
            return check == keypair.public.encrypt(sigtocheck, 32)[0]
        elif isinstance(keypair._key, WordHashKey):
            return keypair._key.verify(sigtocheck, check)
        else:
            raise ToBeImplementedException(name="verify for " + keypair.__class__.__name__)

    @staticmethod
    def dumps(data):
        """
        Convert arbitrary data into a JSON string that can be deterministically hashed or compared.
        Must be valid for loading with json.loads (unless change all calls to that).
        Exception: UnicodeDecodeError if data is binary

        :param data:    Any
        :return: JSON string that can be deterministically hashed or compared
        """
        # ensure_ascii = False was set otherwise if try and read binary content, and embed as "data" in StructuredBlock then complains
        # if it cant convert it to UTF8. (This was an example for the Wrenchicon), but loads couldnt handle return anyway.
        # sort_keys = True so that dict always returned same way so can be hashed
        # separators = (,:) gets the most compact representation
        return dumps(data, sort_keys=True, separators=(',', ':'), default=json_default)

    @staticmethod
    def loads(data):
        """
        Pair to dumps

        :param data:
        :return: Dict or Array from loading json in data
        """
        return loads(data)

    @classmethod
    def decryptdata(self, value, verbose=False):
        """
        Takes a dictionary that may contain { acl, encrypted } and returns the decrypted data.
        No assumption is made about waht is in the decrypted data

        :param value:
        :return:
        """
        if value.get("encrypted"):
            from MutableBlock import AccessControlList, KeyChain
            hash = value.get("acl")
            kc = KeyChain.find(publichash=hash)  # Matching KeyChain or None
            if kc:
                dec = kc.decrypt(data=value.get("encrypted"))  # Exception: DecryptionFail - unlikely since publichash matches
            else:
                acl = AccessControlList(hash=hash, verbose=verbose)  # TODO-AUTHENTICATION probably add person-to-person version
                dec = acl.decrypt(data=value.get("encrypted"), verbose=verbose)
            return dec
        else:
            return value

    # ============ METHODS dealing with Symetric keys ==============================
    @staticmethod
    def randomkey():
        """
        Return a key suitable for symetrically encrypting content or sessions

        :return:
        """
        #TODO-AUTHENTICATION - check this is the right function to use for 16 random bytes see http://stackoverflow.com/questions/20460061/pythons-pycrypto-library-for-random-number-generation-vs-os-urandom
        return os.urandom(16)
        #return Random.get_random_bytes(16)

    @classmethod
    def sym_encrypt(self, data, sym_key, b64=False, **options):
        iv = hashlib.sha1(data).digest()[0:AES.block_size]  # Not random, so can check result, but not checked cryptographically sound
        #iv = Random.new().read(AES.block_size) # The normal way
        cipher = AES.new(sym_key, AES.MODE_CFB, iv)
        res = iv + cipher.encrypt(data)
        if b64:
            res = base64.urlsafe_b64encode(res)
        return res

    @classmethod
    def sym_decrypt(self, data, sym_key, b64=False, **options):
        if b64:
            data = base64.urlsafe_b64decode(str(data))  # Cant work on unicode for some weird reason
        iv = data[0:AES.block_size]    # Matches iv that went into first cypher
        data = data[AES.block_size:]
        cipher = AES.new(sym_key, AES.MODE_CFB, iv)
        dec = cipher.decrypt(data)
        ivtarget = hashlib.sha1(dec).digest()[0:AES.block_size]
        if iv != ivtarget:
            raise DecryptionFail()
        return dec



class KeyPair(SmartDict):
    """
    This uses the CryptoLib functions to encapsulate KeyPairs
    """
    table = "kp"
    _allowunsafestore = False

    def preflight(self, dd=None):
        if not dd:
            dd = self.__dict__.copy()
        if dd["_key"].has_private() and not dd.get("_acl") and not self._allowunsafestore:
            raise SecurityWarning(message="Probably shouldnt be storing private key")   # Can set KeyPair._allowunsafestore to allow this when testing
        if dd.get("_key"):   # Based on whether the CommonList is master, rather than if the key is (key could be master, and CL not)
            dd["key"] = self.privateexport if dd["_key"].has_private() else self.publicexport
        return super(KeyPair, self).preflight(dd=dd)

    def __repr__(self):
        return "KeyPair" + repr(self.__dict__)  #TODO only useful for debugging,

    @classmethod
    def keygen(cls, keyclass=RSA, verbose=False, **options):
        """
        Generate a new RSA key

        :param options: unused
        :keyclass class: Can override default of RSA to WordHash
        :return: KeyPair
        """
        if verbose: print "Generating key for",keyclass
        if keyclass in (True, RSA, "RSA"):
            key=RSA.generate(1024, Random.new().read)
        elif keyclass in (WordHashKey,):
            key = WordHashKey.generate(strength=128)
        else:
            raise NotImplementedError(name="keygen for keyclass="+key.__class__.__name__)
        return cls(key=key)

    @property
    def key(self):
        """
        Returns key - maybe public or private
        :return:
        """
        return self._key

    @key.setter
    def key(self, value):
        """
        Sets a key - public or private
        :return:
        """
        if isinstance(value, basestring):  # Should be exported string, maybe public or private
            if "-----BEGIN " in value:
                self._key = RSA.importKey(value)
            elif "WORDHASH " in value:
                unused, public = value.split()
                self._key = WordHashKey(public=public)
            else:
                raise ToBeImplementedException(name="key import for "+value)
        else:
            self._key = value

    @property
    def private(self):
        """

        :return: Private (RSA) key
        """
        if not self._key.has_private():
            raise PrivateKeyException()
        return self._key

    @private.setter
    def private(self, value):
        """
        Sets the key from either a string,

        :param value: Either a string from exporting the key, or a RSA key
        :return:
        """
        self.key = value
        if not self._key.has_private():  # Check it was really a Private key
            raise PrivateKeyException()

    @property
    def public(self):
        """

        :return: Public (RSA) key
        """
        return self._key.publickey() # Note works on pub or private

    @public.setter
    def public(self, value):
        """
        Sets the key from either a string or a key.

        :param value: Either a string from exporting the key, or a RSA key
        :return:
        """
        self.key = value

    @property
    def publicexport(self):
        if isinstance(self._key, RSA._RSAobj):
            return self.public.exportKey("PEM")
        elif isinstance(self._key, WordHashKey):
                return self._key.publicexport()   # Not exportable
        else:
            raise ToBeImplementedException(name="exportKey for "+self._key.__class__.__name__)

    @property
    def privateexport(self):
        if isinstance(self._key, RSA._RSAobj):
            return self.private.exportKey("PEM")
        elif isinstance(self._key, WordHashKey):
            return ""  # Not exportable
        else:
            raise ToBeImplementedException(name="exportKey for "+self._key.__class__.__name__)

    @property
    def privatehash(self):
        """
        The hash of the key, note does NOT store the key itself

        :return:
        """
        return CryptoLib.Curlhash(self.privateexport)

    @privatehash.setter
    def privatehash(self, value):
        """
        Set a privatehash, note this implies where to get the actual data from
        Note that privatehash and publichash setters are identical

        :param value:
        :return:
        """
        self.key = Dweb.transport.rawfetch(hash=value)

    @property
    def publichash(self):
        return CryptoLib.Curlhash(self.publicexport)

    @publichash.setter
    def publichash(self, value):
        """
        Set a publichash, note this implies where to get the actual data from
        Note that privatehash and publichash setters are identical

        :param value:
        :return:
        """
        self.key = Dweb.transport.rawfetch(hash=value)
        #TODO-AUTHENTICATION what happens if cant find
        if self.publichash != value and self.privatehash != value:
            self._key = None    # Blank out bad key
            raise AuthenticationException(message="Retrieved key doesnt match hash="+value)
            #TODO-AUTHENTICATION copy this verification code up to privatehash

    def encrypt(self, data, b64=False):
        """
        :param data:
        :return: str, binary encryption of data
        """
        if False:
            data = data[0:86]       # Can only encrypt 86 bytes!
            enc = PKCS1_OAEP.new(self.public).encrypt(data)
            #return self.public.encrypt(data, 32)[0]    # warnings abound not to use RSA directly

        if False:
            session_key = Random.get_random_bytes(16)
            enckey = (PKCS1_OAEP.new(self.public).encrypt(session_key))
            # Encrypt the data with the AES session key
            cipher_aes = AES.new(session_key) #, AES.MODE_EAX)
            ciphertext, tag = cipher_aes.encrypt_and_digest(data)
            data = "".join(enckey, cipher_aes.nonce, tag, ciphertext)

        aeskey = Random.new().read(32)
        msg = CryptoLib.sym_encrypt(data, aeskey)
        cipher = PKCS1_OAEP.new(self._key.publickey())
        ciphertext = cipher.encrypt(aeskey)
        res = ciphertext + msg
        if b64:
            res = base64.urlsafe_b64encode(res)
        return res

    def decrypt(self, data, b64=False):
        if b64:
            data = base64.urlsafe_b64decode(data)
        enckey = data[0:128]    # Just the RSA encryption of the Aes key - 128 bytes
        data = data[128:]
        cipher = PKCS1_OAEP.new(self._key)
        aeskey = cipher.decrypt(enckey)     # Matches aeskey in encrypt
        return CryptoLib.sym_decrypt(data, aeskey)


class WordHashKey(object):
    """
    This is an odd, not really private/public key pair but it pretends to be.
    It uses a key selected by the mnemonic words as the "private" key, and its hash as the public key.
    The key is not stored with a keypair, either private or public since storing it would potentially expose it.

    _public  hash of private
    _private    binary key from the mnemonic words
    """
    def __init__(self, mnemonic=None, public=None):
        if mnemonic:
            self._private = str(Mnemonic("english").to_entropy(mnemonic))
            # TODO-AUTHENTICATION - in many places where use randomkey could allow setting with words
            self._public = CryptoLib.Curlhash(self._private)
        elif public:
            self._private = None
            self._public = public
        else:
            raise ToBeImplementedException("WordHashKey init if neither mnemonic or public")

    def publickey(self):  # Dummy, as functions are on key overall, not on private/public
        return self

    def sign(self, value, **options):
        return CryptoLib.sym_encrypt(value, self._private, b64=False, **options)    # b64 false because caller does it

    def verify(self, sigtocheck, check, **options):
        if self._private: # Check if we have _private, i.e. it is pretending to be on our KeyChain
            return CryptoLib.sym_encrypt(value, self._private, b64=False, **options) == check
        else:
            return True # Always verifies OK on for example Transport

    def decrypt(self, value, **options):  # Used by CryptoLib.signature to sign a date+data string
        return self.sign(value, **options)

    def has_private(self):
        return self._private is not None

    def publicexport(self):
        return "WORDHASH "+self._public     # _public is a hash already

    @classmethod
    def generate(cls, strength=128):
        return cls(mnemonic=Mnemonic("english").generate(strength=strength))

    @property
    def mnemonic(self):
        """
        Return the set of words to remember to regenerate this.

        :return:
        """
        return Mnemonic("english").to_mnemonic(self._private)

def json_default(obj):
    """
    Default JSON serialiser especially for handling datetime.

    :param obj: Anything json dumps can't serialize
    :return: string for extended types
    """
    if isinstance(obj, (datetime,)):    # Using isinstance rather than hasattr because __getattr__ always returns true
    #if hasattr(obj,"isoformat"):  # Especially for datetime
        return obj.isoformat()
    try:
        return obj.dumps()
    except:
        raise TypeError("Type %s not serializable" % obj.__class__.__name__)


