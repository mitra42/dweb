# encoding: utf-8
#TODO-BACKPORT - review this file

from json import dumps, loads
import base64
import hashlib
from datetime import datetime
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from mnemonic import Mnemonic
from multihash import encode, SHA1,SHA2_256, SHA2_512, SHA3
import nacl.secret
import nacl.utils
import nacl.encoding
import nacl.hash
import nacl.public
import nacl.signing

from misc import MyBaseException, ToBeImplementedException

# See Libsodium docs
# https://download.libsodium.org/doc/public-key_cryptography/authenticated_encryption.html
# https://pynacl.readthedocs.io/en/latest/encoding/

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
    CRYPTO=0
    NACL=1
    defaultlib = 1  # CRYPRO | NACL
    libname = ["Crypto","NACL"][defaultlib]

    @staticmethod
    #def Curlhash(data, hashscheme="SHA3256B64URL", **options):
    def Curlhash(data, hashscheme=None, **options):
        """
        Hashing - using either Crypto or NACL.
        There is a multihash version under development below.

        :param data: Any length and combination of bytes
        :return: URL and Filename safe string   hashname.b64encoding
        """
        if not hashscheme:
            hashscheme = ("SHA3256B64URL", "BLAKE2")[CryptoLib.defaultlib]
        if CryptoLib.defaultlib == CryptoLib.CRYPTO:
            hashfunction = { "SHA1B64URL": hashlib.sha1, "SHA256B64URL": hashlib.sha256, "SHA512B64URL": hashlib.sha512,
                             "BLAKE2": None, #"SHA3256B64URL": hashlib.sha3_256,
                             "SIPHASH24": None, "SIPHASHX24": None}[hashscheme]
            if not hashfunction:
                raise ToBeImplementedException(name="CryptoLib.Curlhash for Crypto hashscheme=" + hashscheme)
            else:
                return hashscheme + "." + CryptoLib.b64enc(hashfunction(data).digest())
        elif CryptoLib.defaultlib == CryptoLib.NACL:
            hashfunction = {"SHA1B64URL": None, "SHA256B64URL": nacl.hash.sha256, "SHA512B64URL": nacl.hash.sha512,
                            "SHA3256B64URL": None, "BLAKE2": nacl.hash.blake2b,
                            "SIPHASH24": nacl.hash.siphash24}[hashscheme]
            if not hashfunction:
                raise ToBeImplementedException(name="CryptoLib.Curlhash for NACL hashscheme=" + hashscheme)
            else:
                return hashscheme + "." + hashfunction(data, encoder=nacl.encoding.URLSafeBase64Encoder)
        else:
            raise ToBeImplementedException(name="CryptoLib.Curlhash for lib="+str(CryptoLib.defaultlib))

    @staticmethod
    def Multihash_Curlhash(data, hashscheme="SHA2256B64URL", **options):
        if CryptoLib.defaultlib != CryptoLib.CRYPTO: raise ToBeImplementedException(name="Multihash_Curlhash to include NACL")
        """
        This version will uses multihash, which unfortunately doesnt work on larger than 127 strings or on SHA3

        :param data: Any length and combination of bytes
        :return: URL and Filename safe string   hashname.b64encoding
        """
        if hashscheme == "SHA2256B64URL":
            return hashscheme+ "." + CryptoLib.b64enc(encode(data, SHA1))
        elif hashscheme == "SHA2256B64URL":
            return hashscheme+ "." + CryptoLib.b64enc(encode(data, SHA2_256))
        elif hashscheme == "SHA2512B64URL":
            return hashscheme+ "." + CryptoLib.b64enc(encode(data, SHA2_512))
        elif hashscheme == "SHA3512B64URL":
            return hashscheme+ "." + CryptoLib.b64enc(encode(data, SHA3))
        else:
            raise ToBeImplementedException(name="CryptoLib.Multihash_Curlhash for hashscheme=" + hashscheme)


    @staticmethod
    def _signable(date, data):
        """
        Returns a string suitable for signing and dating, current implementation includes date and storage url of data.
        Called by signature, so that same thing signed as compared

        :param date: Date on which it was signed
        :param data: Storage url of data signed (as returned by Transport layer) - will convert to str if its unicode
        :return: Signable or comparable string
        COPIED TO JS 2017-05-23
        """
        return date.isoformat() + str(data)

    @staticmethod
    def signature(keypair, date, data, verbose=False, **options):
        """
        Pair of verify(), signs date and data using public key function.

        :param keypair: Key that be used for signture
        :param date: Date that signing (usually now)
        :return: signature that can be verified with verify
        COPIED TO JS 2017-05-23
        """
        signable = CryptoLib._signable(date, data)
        if isinstance(keypair._key, RSA._RSAobj):
            # TODO-AUTHENTICATION - replace with better signing/verification e.g. from http://pydoc.net/Python/pycrypto/2.6.1/Crypto.Signature.PKCS1_v1_5/
            # TODO-AUTHENTICATION - note this will require reworking WordHash.decrypt
            return CryptoLib.b64enc(keypair.private.decrypt(signable))
        elif isinstance(keypair._key, nacl.signing.SigningKey):
            sig=keypair._key.sign(signable, nacl.encoding.URLSafeBase64Encoder).signature
            #Can uncommen next line if seeing problems veriying things that should verify ok - tests immediate verification
            #keypair._key.verify_key.verify(signable, nacl.encoding.URLSafeBase64Encoder.decode(sig))
            return sig
        elif isinstance(keypair._key, WordHashKey):
            return CryptoLib.b64enc(keypair._key.sign(signable))
        else:
            raise ToBeImplementedException(name="signature for key ="+keypair._key.__class__.__name__)

    @staticmethod
    def verify(sig, url=None):
        """
        Pair of signature(), compares signature and date against encrypted data.
        Typically called with \*\*block where block is a signature dictionary read from Transport with date transformed to datetime.

        :return:
        """
        from CommonList import CommonList
        cl = CommonList(url=sig.signedby).fetch(fetchlist=False)
        # Dont know what kind of list - e.g. MutableBlock or AccessControlList but dont care as only use keys
        keypair = cl.keypair    # Sideeffect of loading from dweb
        assert keypair
        #b64decode requires a str, but signature may be unicode
        #TODO-AUTHENTICATION - replace with better signing/verification e.g. from http://pydoc.net/Python/pycrypto/2.6.1/Crypto.Signature.PKCS1_v1_5/
        #TODO-AUTHENTICATION - note this will require reworking WordHash.decrypt
        check = CryptoLib._signable(sig.date, url or sig.url)
        if isinstance(keypair._key, RSA._RSAobj):
            sigtocheck = CryptoLib.b64dec(str(sig.signature))
            return check == keypair.public.encrypt(sigtocheck, 32)[0]
        elif isinstance(keypair._key, WordHashKey):
            sigtocheck = CryptoLib.b64dec(str(sig.signature))
            return keypair._key.verify(sigtocheck, check)
        elif isinstance(keypair._key, nacl.signing.VerifyKey):
            try:
                z = CryptoLib.b64dec(str(sig.signature))
                keypair._key.verify(check, z, encoder=nacl.encoding.RawEncoder)
            except nacl.exceptions.BadSignatureError:
                1/0 # This really shouldnt be happenindg - catch it and figure out why
                return False
            else:
                return True
        else:
            raise ToBeImplementedException(name="verify for " + keypair._key.__class__.__name__)

    @staticmethod
    def b64dec(data):
        """
        Decode arbitrary data encoded using b64enc
        
        :param data:    b64 encoding of arbitrary binary
        :return: str    arbitrary binary
        """
        if data is None:
            return None
        if not isinstance(data, basestring):
            return data # Its not a string to un-b64
        if isinstance(data, unicode):
            data = str(data)    # b64 doesnt like unicode
        try:
            if CryptoLib.defaultlib == CryptoLib.CRYPTO:
                return base64.urlsafe_b64decode(data)
            elif CryptoLib.defaultlib == CryptoLib.NACL:
                return nacl.encoding.URLSafeBase64Encoder.decode(data)
            else:
                raise ToBeImplementedException(name="b64dec for Cryptolib=" + CryptoLib.libname)
        except TypeError as e:
            print "Cant urlsafe_b64decode data",data.__class__.__name__,data
            raise e

    @staticmethod
    def b64enc(data):
        """
        Encode arbitrary data to b64 

        :param data: 
        :return: 
        """
        if  data is None:
            return None # Json can handle none
        elif not isinstance(data, basestring):
            return data # Dont b64enc hope inner parts are encoded with their own dumps
        else:   # Dont believe need to convert from unicode to str first
            try:
                if CryptoLib.defaultlib == CryptoLib.CRYPTO:
                    return base64.urlsafe_b64encode(data)
                elif CryptoLib.defaultlib == CryptoLib.NACL:
                    return nacl.encoding.URLSafeBase64Encoder.encode(data)
                else:
                    raise ToBeImplementedException(name="b64enc for Cryptolib="+CryptoLib.libname)
            except TypeError as e:
                print "Cant urlsafe_b64encode data", data.__class__.__name__, e, data
                raise e
            except Exception as e:
                print "b64enc error:", e # Dont get exceptions printed inside dumps, just obscure higher level one
                raise e

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
        if data is None:
            pass        # For breakpoint
        assert data is not None
        return loads(data)

    @classmethod
    def decryptdata(cls, value, verbose=False):
        """
        Takes a dictionary that may contain { acl, encrypted } and returns the decrypted data.
        No assumption is made about waht is in the decrypted data

        :param value:
        :return:
        """
        if value.get("encrypted"):
            from AccessControlList import AccessControlList
            from KeyChain import KeyChain
            url = value.get("acl")
            kc = KeyChain.find(publicurl=url)  # Matching KeyChain or None
            if kc:
                dec = kc.decrypt(data=value.get("encrypted"))  # Exception: DecryptionFail - unlikely since publicurl matches
            else:
                acl = AccessControlList(url=url, verbose=verbose)  # TODO-AUTHENTICATION probably add person-to-person version
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
        # see http://stackoverflow.com/questions/20460061/pythons-pycrypto-library-for-random-number-generation-vs-os-urandom
        return nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)    # 32 bytes - required for SecretBox
        #return os.urandom(16)
        #return Random.new().read(32)
        #return Random.get_random_bytes(16)

    @classmethod
    def sym_encrypt(cls, data, sym_key, b64=False, **options):
        """
        Pair of sym_decrypt
        ERR: DecryptFail if cant decrypt - this is to be expected if unsure if have valid key (e.g. in acl.decrypt)
        
        :param data:        # Data to encrypt
        :param sym_key:     Key of arbitrary length - for consistency use CryptoLib.randomkey() to generate or "SecretBox"
        :param b64:         True if want output in base64
        :param options:     Unused
        :return:            Encrypted string, either str or EncodedMessage (which is subclass of str)
        """
        #TODO-AUTHENTICATION - maybe encrypted strings need to tag which method used.
        if cls.defaultlib == CryptoLib.CRYPTO:
            iv = hashlib.sha1(data).digest()[0:AES.block_size]  # Not random, so can check result, but not checked cryptographically sound
            #iv = Random.new().read(AES.block_size) # The normal way
            cipher = AES.new(sym_key, AES.MODE_CFB, iv)             # Key can be any, or at least 16 or 32 bytes.
            res = iv + cipher.encrypt(data)
            if b64:
                res = CryptoLib.b64enc(res)
            return res
        elif cls.defaultlib == CryptoLib.NACL:
            if isinstance(sym_key, basestring):
                sym_key = nacl.secret.SecretBox(sym_key)    # Requires 32 bytes
            encoder = nacl.encoding.URLSafeBase64Encoder if b64 else nacl.encoding.RawEncoder
            return sym_key.encrypt(data, encoder=encoder)    # Can take nonce parameter if reqd, but usually not,
            # return is EncryptedMessage instance which isinstance(basestring)
        else:
            raise ToBeImplementedException(name="sym_encrypt for defaultlib="+cls.defaultlib)

    @classmethod
    def sym_decrypt(cls, data, sym_key, b64=False, **options):
        #print data.__class__.__name__,len(data),b64
        if cls.defaultlib == CryptoLib.CRYPTO:
            if b64:
                data = CryptoLib.b64dec(str(data))  # Cant work on unicode for some weird reason
            iv = data[0:AES.block_size]    # Matches iv that went into first cypher
            data = data[AES.block_size:]
            cipher = AES.new(sym_key, AES.MODE_CFB, iv)
            dec = cipher.decrypt(data)
            ivtarget = hashlib.sha1(dec).digest()[0:AES.block_size]
            if iv != ivtarget:
                raise DecryptionFail()
            return dec
        elif cls.defaultlib == CryptoLib.NACL:
            if isinstance(sym_key, basestring):
                sym_key = nacl.secret.SecretBox(sym_key)    # Requires 32 bytes
            encoder = nacl.encoding.URLSafeBase64Encoder if b64 else nacl.encoding.RawEncoder
            if b64:
                data = str(data)    # URLSafeBase64Encoder can't handle Unicode
            try:
                return sym_key.decrypt(data, encoder=encoder)    # Can take nonce parameter if reqd, but usually not,
            except nacl.exceptions.CryptoError as e:
                raise DecryptionFail() # Is expected in some cases, esp as looking for a valid key in acl.decrypt
        else:
            raise ToBeImplementedException(name="sym_decrypt for defaultlib=" + cls.defaultlib)

class WordHashKey(object):   #TODO-LIBSODIUM-CHECK-THIS-FUNCTION maybe replace with deterministic pub key from mnemonic
    """
    This is an odd, not really private/public key pair but it pretends to be.
    It uses a key selected by the mnemonic words as the "private" key, and its url as the public key.
    The key is not stored with a keypair, either private or public since storing it would potentially expose it.

    _public  url of private
    _private    binary key from the mnemonic words
    """
    def __init__(self, mnemonic=None, public=None):
        #if CryptoLib.defaultlib != CryptoLib.CRYPTO: raise ToBeImplementedException(name="#TODO-LIBSODIUM")
        if mnemonic:
            self._private = str(Mnemonic("english").to_entropy(mnemonic))
            # TODO-AUTHENTICATION - in many places where use randomkey could allow setting with words
            self._public = CryptoLib.Curlhash(self._private)
        elif public:
            self._private = None
            self._public = public
        else:
            raise ToBeImplementedException(name="WordHashKey init if neither mnemonic or public")

    def publickey(self):  # Dummy, as functions are on key overall, not on private/public
        #if CryptoLib.defaultlib != CryptoLib.CRYPTO: raise ToBeImplementedException(name="#TODO-LIBSODIUM")
        return self

    def sign(self, value, **options):
        #if CryptoLib.defaultlib != CryptoLib.CRYPTO: raise ToBeImplementedException(name="#TODO-LIBSODIUM")
        return CryptoLib.sym_encrypt(value, self._private, b64=False, **options)    # b64 false because caller does it

    def verify(self, sigtocheck, check, **options):
        #if CryptoLib.defaultlib != CryptoLib.CRYPTO: raise ToBeImplementedException(name="#TODO-LIBSODIUM")
        if self._private: # Check if we have _private, i.e. it is pretending to be on our KeyChain
            return CryptoLib.sym_encrypt(value, self._private, b64=False, **options) == check   #TODO-this is wrong "value" doest exist
        else:
            return True # Always verifies OK on for example Transport

    #def decrypt(self, value, **options):  # Used by CryptoLib.signature to sign a date+data string
    #    #if CryptoLib.defaultlib != CryptoLib.CRYPTO: raise ToBeImplementedException(name="#TODO-LIBSODIUM")
    #    return self.sign(value, **options)

    def has_private(self):
        #if CryptoLib.defaultlib != CryptoLib.CRYPTO: raise ToBeImplementedException(name="#TODO-LIBSODIUM")
        return self._private is not None

    def publicexport(self):
        #if CryptoLib.defaultlib != CryptoLib.CRYPTO: raise ToBeImplementedException(name="#TODO-LIBSODIUM")
        return "WORDHASH:"+self._public     # _public is a url already

    @classmethod
    def generate(cls, strength=256):    # Move up to 32 bytes (note at 16 byte = 128 bit it breaks the symkey in LibSodium
        #if CryptoLib.defaultlib != CryptoLib.CRYPTO: raise ToBeImplementedException(name="#TODO-LIBSODIUM")
        return cls(mnemonic=Mnemonic("english").generate(strength=strength))

    @property
    def mnemonic(self):
        #if CryptoLib.defaultlib != CryptoLib.CRYPTO: raise ToBeImplementedException(name="#TODO-LIBSODIUM")
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
    except Exception as e:
        raise TypeError("Type %s not serializable (%s %s)" % (obj.__class__.__name__, e.__class__.__name__, e))


