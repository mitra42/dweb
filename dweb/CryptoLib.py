# encoding: utf-8

from json import dumps, loads
import base64
import hashlib
from datetime import datetime
from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP

from misc import MyBaseException, ToBeImplementedException, AssertionFail
import sha3 # To add to hashlib
from multihash import encode, SHA1,SHA2_256, SHA2_512, SHA3
from CommonBlock import Transportable

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
        #TODO-AUTHENTICATION maybe use keypair's decrypt but didn't work in brief test
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
        keypair = KeyPair(hash=sig.signedby)     # Sideeffect of loading from dweb
        #b64decode requires a str, but signature may be unicode
        #TODO-AUTHENTICATION maybe use keypair's encrypt but didn't work in brief test
        decrypted = keypair.public.encrypt(base64.urlsafe_b64decode(str(sig.signature)), 32)[0]
        check = CryptoLib._signable(sig.date, hash or sig.hash)
        return check == decrypted

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


class KeyPair(Transportable):
    """
    This uses the CryptoLib functions to encapsulate KeyPairs
    """

    def __init__(self, hash=None, key=None, data=None):
        if data:                            # Support data kwarg so can call from Transportable.store
            key = data
        if key:
            self.public = key               # Converts if key is an exported string, also works if key is privatekey
        elif hash:
            self.publichash = hash          # Side effect of loading from dWeb, note also works if its hash of publickey
        else:
            self._key = None

    @property
    def _data(self):
        return

    def __repr__(self):
        return "KeyPair" + repr(self.__dict__)  #TODO only useful for debugging,

    @classmethod
    def keygen(cls, **options):
        """
        Generate a new key

        :param options: unused
        :return: KeyPair
        """
        return cls(key=RSA.generate(1024, Random.new().read))

    @property
    def private(self):
        """

        :return: Private (RSA) key
        """
        if not self._key.has_private:
            raise PrivateKeyException()
        return self._key

    @private.setter
    def private(self, value):
        """
        Sets the key from either a string,

        :param value: Either a string from exporting the key, or a RSA key
        :return:
        """
        if isinstance(value, basestring):   # Should be exported string, maybe public or private
            self._key = RSA.importKey(value)
        else:
            self._key = value
        if not self._key.has_private:   # Check it was really a Private key
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
        Sets the key from either a string,

        :param value: Either a string from exporting the key, or a RSA key
        :return:
        """
        if isinstance(value, basestring):   # Should be exported string, maybe public or private
            self._key = RSA.importKey(value)
        else:
            self._key = value

    @property
    def publicexport(self):
        return self.public.exportKey("PEM")

    @property
    def privateexport(self):
        return self.private.exportKey("PEM")

    @property
    def privatehash(self):
        return CryptoLib.Curlhash(self.privateexport)

    @privatehash.setter
    def privatehash(self, value):
        """
        Set a privatehash, note this implies where to get the actual data from
        Note that privatehash and publichash setters are identical

        :param value:
        :return:
        """
        self._key = RSA.importKey(self.transport.block(hash=value)) #TODO what happens if cant find

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
        self._key = RSA.importKey(self.transport.block(hash=value))
        #TODO-AUTHENTICATION what happens if cant find
        if self.publichash != value:
            self._key = None    # Blank out bad key
            raise AuthenticationException("Retrieved key doesnt match hash="+value)
            #TODO-AUTHENTICATION copy this verification code up to privatehash

    def store(self, private=False, verbose=False):
        #TODO-REFACTOR-STORE to return obj, not hash
        hash = super(KeyPair, self).store(data=self.privateexport if private else self.publicexport, verbose=verbose)
        if hash != (self.privatehash if private else self.publichash):
            raise AssertionFail("Stored hash of key should match local hash algorithm")
        return self # For chaining

    def encrypt(self, data):
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
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(aeskey, AES.MODE_CFB, iv)
        msg = iv + cipher.encrypt(data)

        random_generator = Random.new().read
        rsakey = RSA.generate(1024, random_generator)
        cipher = PKCS1_OAEP.new(rsakey.publickey())
        ciphertext = cipher.encrypt(aeskey)
        return ciphertext + msg         #TODO-AUTHENTICATION need to B64 it

    def decrypt(self, data):
        #TODO-AUTHENTICATION need to un-B64 it
        enckey = data[0:128]    # Just the RSA key - 128 bytes
        data = data[128:]
        iv = data[0:AES.block_size]    # Matches iv that went into first cypher
        data = data[AES.block_size:]
        cipher = PKCS1_OAEP.new(self._key)
        aeskey = cipher.decrypt(enckey)     # Matches aeskey in encrypt
        cipher = AES.new(aeskey, AES.MODE_CFB, iv)
        msg = cipher.decrypt(data)
        return msg

        if False:
            return PKCS1_OAEP.new(self.private).decrypt(data)
        #return self.private.decrypt(data)   #  warnings abound not to use RSA directly #TODO-AUTHENTICATE - sig verification was assuming this.


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


