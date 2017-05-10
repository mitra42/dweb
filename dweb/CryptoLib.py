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
from multihash import encode, SHA1,SHA2_256, SHA2_512, SHA3
import nacl.secret
import nacl.utils
import nacl.encoding
import nacl.hash
import nacl.public
import nacl.signing

from misc import MyBaseException, ToBeImplementedException
import sha3 # To add to hashlib
from CommonBlock import Transportable, SmartDict
from Dweb import Dweb


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
                             "SHA3256B64URL": hashlib.sha3_256, "BLAKE2": None,
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
        Returns a string suitable for signing and dating, current implementation includes date and storage hash of data.
        Called by signature, so that same thing signed as compared

        :param date: Date on which it was signed
        :param data: Storage hash of data signed (as returned by Transport layer) - will convert to str if its unicode
        :return: Signable or comparable string
        """
        return date.isoformat() + str(data)

    @staticmethod
    def signature(keypair, date, data, verbose=False, **options):
        """
        Pair of verify(), signs date and data using public key function.

        :param keypair: Key that be used for signture
        :param date: Date that signing (usually now)
        :return: signature that can be verified with verify
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
        assert keypair
        #b64decode requires a str, but signature may be unicode
        #TODO-AUTHENTICATION - replace with better signing/verification e.g. from http://pydoc.net/Python/pycrypto/2.6.1/Crypto.Signature.PKCS1_v1_5/
        #TODO-AUTHENTICATION - note this will require reworking WordHash.decrypt
        check = CryptoLib._signable(sig.date, hash or sig.hash)
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
        # see http://stackoverflow.com/questions/20460061/pythons-pycrypto-library-for-random-number-generation-vs-os-urandom
        return nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)    # 32 bytes - required for SecretBox
        #return os.urandom(16)
        #return Random.new().read(32)
        #return Random.get_random_bytes(16)

    @classmethod
    def sym_encrypt(self, data, sym_key, b64=False, **options):
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
        if self.defaultlib == CryptoLib.CRYPTO:
            iv = hashlib.sha1(data).digest()[0:AES.block_size]  # Not random, so can check result, but not checked cryptographically sound
            #iv = Random.new().read(AES.block_size) # The normal way
            cipher = AES.new(sym_key, AES.MODE_CFB, iv)             # Key can be any, or at least 16 or 32 bytes.
            res = iv + cipher.encrypt(data)
            if b64:
                res = CryptoLib.b64enc(res)
            return res
        elif self.defaultlib == CryptoLib.NACL:
            if isinstance(sym_key, basestring):
                sym_key = nacl.secret.SecretBox(sym_key)    # Requires 32 bytes
            encoder = nacl.encoding.URLSafeBase64Encoder if b64 else nacl.encoding.RawEncoder
            return sym_key.encrypt(data, encoder=encoder)    # Can take nonce parameter if reqd, but usually not,
            # return is EncryptedMessage instance which isinstance(basestring)
        else:
            raise ToBeImplementedException(name="keygen for keyclass="+key.__class__.__name__)

    @classmethod
    def sym_decrypt(self, data, sym_key, b64=False, **options):
        #print data.__class__.__name__,len(data),b64
        if self.defaultlib == CryptoLib.CRYPTO:
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
        elif self.defaultlib == CryptoLib.NACL:
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
            raise ToBeImplementedException(name="keygen for keyclass=" + key.__class__.__name__)


class KeyPair(SmartDict):
    """
    This uses the CryptoLib functions to encapsulate KeyPairs of different Public Key systems.
    Currently supports: RSA; and the PyNaCl bindings to LibSodium
    It is intended to provide a consistent interface to the application, masking the characteristics of different crypto systems underneath.
    """
    table = "kp"
    _allowunsafestore = False
    KEYTYPESIGN = 1
    KEYTYPEENCRYPT = 2
    KEYTYPESIGNANDENCRYPT = 3

    naclkeyclasses = {
        nacl.public.PublicKey: "NACL PUBLIC",
        nacl.public.PrivateKey: "NACL PRIVATE",
        nacl.signing.SigningKey: "NACL SIGNING",
        nacl.signing.VerifyKey: "NACL VERIFY",
    }

    def preflight(self, dd):
        if self._key_has_private(dd["_key"]) and not dd.get("_acl") and not self._allowunsafestore:
            raise SecurityWarning(message="Probably shouldnt be storing private key")   # Can set KeyPair._allowunsafestore to allow this when testing
        if dd.get("_key"):   # Based on whether the CommonList is master, rather than if the key is (key could be master, and CL not)
            dd["key"] = self.privateexport if self._key_has_private(dd["_key"]) else self.publicexport
        return super(KeyPair, self).preflight(dd=dd)

    def __repr__(self):
        return "KeyPair" + repr(self.__dict__)  #TODO only useful for debugging,

    @classmethod
    def keygen(cls, keyclass=None, keytype=None, mnemonic=None, seed=None, verbose=False, **options):
        """
        Generate a new key pair
        ERR: ValueError - wrong size seed

        :param options: unused
        :keyclass class: RSA, CryptoLib.NACL, or WordHashKey
        :keytype int: one of KEYTYPESIGN, KEYTYPEENCRYPT or KEYTYPESIGNANDENCRYPT (latter not supported)
        :mnemonic string: Words to convert into seed for key (valid with NACL and WordHashKey)
        :seed binary: Seed to keygen (valid with keyclass=NACL, invalid with mnemonic)
        :return: KeyPair
        """
        #assert keytype  # Required parameter
        if not keyclass:
            keyclass = RSA if CryptoLib.defaultlib == CryptoLib.CRYPTO else CryptoLib.NACL
        if verbose: print "Generating key for",keyclass
        if mnemonic:
            seed = str(Mnemonic("english").to_entropy(mnemonic))
        if keyclass in (RSA, "RSA"):
            if seed:
                raise ToBeImplementedException(name="keygen - support for RSA with seeds")
            key=RSA.generate(1024, Random.new().read)
        elif keyclass in (CryptoLib.NACL,):
            if keytype == cls.KEYTYPESIGN:
                key = nacl.signing.SigningKey(seed) if seed else nacl.signing.SigningKey.generate() #ValueError if seed != 32 bytes
            elif keytype == cls.KEYTYPEENCRYPT:
                key=nacl.public.PrivateKey(seed) if seed else nacl.public.PrivateKey.generate() #ValueError if seed != 32 bytes
            else:
                raise ToBeImplementedException(name="keygen for keytype="+str(keytype))
        elif keyclass in (WordHashKey,):
            key = WordHashKey(mnemonic=mnemonic) if mnemomic else WordHashKey.generate(strength=256)    # Must be 32 bytes=156 for symkey (was using 128)
        else:
            raise ToBeImplementedException(name="keygen for keyclass="+keyclass.__class__.__name__)
        return cls(key=key)

    @property
    def key(self):
        """
        Returns key - maybe public or private (looks like most places are using _key instead of key
        :return:
        """
        return self._key

    def _importkey(self, value):
        # Import a key
        assert isinstance(value, basestring)  # Should be exported string, maybe public or private
        # First tackle standard formats created by exporting functionality on keys
        if "-----BEGIN " in value:
            return RSA.importKey(value)
        elif ":" in value:
            tag, hash = value.split(':')
            # Tackle our own formats always xyz:key
            if tag == "WORDHASH":
                return WordHashKey(public=hash)
            elif tag in KeyPair.naclkeyclasses.values():
                keyclass = [k for k in KeyPair.naclkeyclasses if KeyPair.naclkeyclasses[k] == tag][0]  # e.g. nacl.public.PrivateKey
                return keyclass(str(hash), nacl.encoding.URLSafeBase64Encoder)
            else:
                raise ToBeImplementedException(name="key import for " + value)
        else:
            raise ToBeImplementedException(name="key import for " + value)

    @key.setter
    def key(self, value):
        """
        Sets a key - public or private from a KeyPair or a string that can be imported
        :return:
        """
        if isinstance(value, basestring):  # Should be exported string, maybe public or private
            self._key = self._importkey(value)
        else:   # Its already a key
            self._key = value

    @property
    def private(self):
        """

        :return: Private (RSA) key
        """
        if not self.has_private():
            raise PrivateKeyException()
        return self._key

    @private.setter
    def private(self, value):
        """
        Sets the key from a string, or a key (doesnt appear to be used)

        :param value: Either a string from exporting the key, or a RSA key
        :return:
        """
        self.key = value
        if not self.has_private():  # Check it was really a Private key
            raise PrivateKeyException()

    @property
    def public(self):
        """
        Return the public side of any Private/Public key pair suitable for encryption or verification
        
        :return: Public (RSA) key
        """
        k = self._key
        if isinstance(k, RSA._RSAobj):
            return k.publickey()
        elif isinstance(k, WordHashKey):
            return k._public
        elif isinstance(k, nacl.public.PrivateKey):
            return k.public_key
        elif isinstance(k, nacl.signing.SigningKey):
            return k.verify_key
        else:
            raise ToBeImplementedException(name="public for " + k.__class__.__name__)

    @public.setter
    def public(self, value):
        """
        Sets the key from either a string or a key. (Doesnt appear to be being used)

        :param value: Either a string from exporting the key, or a RSA key
        :return:
        """
        self.key = value

    @property
    def mnemonic(self):
        if isinstance(self._key, (nacl.public.PrivateKey, nacl.signing.SigningKey)):
            return Mnemonic("english").to_mnemonic(self._key.encode(nacl.encoding.RawEncoder))
        else:
            raise ToBeImplementedException(name="mnemonic for "+self._key.__class__.__name__)

    def _exportkey(self, key):
        # Export any of a set of key classes, note those with explicit publicexport() etc methods should have been already handled.
        tag = self.naclkeyclasses.get(key.__class__)
        if tag:
            return tag+":"+key.encode(nacl.encoding.URLSafeBase64Encoder)
        elif isinstance(key, RSA._RSAobj):
            return key.exportKey("PEM")
        else:
            raise ToBeImplementedException(name="export for "+key.__class__.__name__)

    @property
    def publicexport(self):
        if isinstance(self._key, WordHashKey):  # Handle own classes which have a publicexport() method
            return self._key.publicexport()   # (Dont use k as its a hash already)
        else:
            return self._exportkey(self.public)

    @property
    def privateexport(self):
        if isinstance(self._key, WordHashKey):
            return ""  # Not exportable
        elif isinstance(self._key, (nacl.public.PublicKey, nacl.signing.VerifyKey)):    # Dont have private
            raise PrivateKeyException()
        else:
            return self._exportkey(self._key)

    @staticmethod
    def _key_has_private(key):
        # Helper function used by has_private and preflight
        if isinstance(key, (RSA._RSAobj, WordHashKey)):
            return key.has_private()
        elif isinstance(key, (nacl.public.PrivateKey, nacl.signing.SigningKey)):
            return True
        elif isinstance(key, (nacl.public.PublicKey, nacl.signing.VerifyKey)):
            return True
        else:
            raise ToBeImplementedException(name="KeyPair._key_has_private for _key is "+key.__class__.__name__)

    @property
    def naclprivate(self):
        if isinstance(self._key, nacl.public.PrivateKey):
            return self._key
        if isinstance(self._key, nacl.signing.SigningKey):
            return nacl.public.PrivateKey(self._key.encode(nacl.encoding.RawEncoder))
        else:
            raise PrivateKeyException()

    @property
    def naclpublic(self):
        # Return the public key, for NACL this made by turning SigningKey into PrivateKey into Publickey
        if isinstance(self._key, nacl.public.PublicKey):
            return self._key
        if isinstance(self._key, (nacl.public.PrivateKey, nacl.signing.SigningKey)):
            return self.naclprivate.public_key
        else:
            raise ToBeImplementedException(name="naclpublic for _key is "+self._key.__class__.__name__)
            #return None

    def naclpublicexport(self):
        # Export the public encryption key, for NACL this made by turning SigningKey into PrivateKey into Publickey
        if isinstance(self._key, (nacl.public.PrivateKey,nacl.signing.SigningKey)):
            return self._exportkey(self.naclpublic)
        else:
            return None

    def has_private(self):
        return self._key_has_private(self._key)

    def encrypt(self, data, b64=False, signer=None):
        """
        Encrypt a string, the destination string has to include any information needed by decrypt, e.g. Nonce etc

        :param data:
        :b64 bool:  Trye if want result encoded
        :signer AccessControlList or KeyPair: If want result signed (currently ignored for RSA, reqd for NACL)
        :return: str, binary encryption of data
        """
        if isinstance(self._key,RSA._RSAobj):
            #TODO currently it ignores "sign" which was introduced with NACL, if keep using RSA then implement here
            aeskey = CryptoLib.randomkey()
            msg = CryptoLib.sym_encrypt(data, aeskey)
            cipher = PKCS1_OAEP.new(self._key.publickey())  # Note can only encrypt the key with PKCS1_OAEP as it can only handle 86 bytes
            ciphertext = cipher.encrypt(aeskey)
            res = ciphertext + msg
            if b64:
                res = CryptoLib.b64enc(res)
            return res
        elif isinstance(self._key, (nacl.public.PrivateKey, nacl.signing.SigningKey)):
            assert signer, "Until PyNaCl bindings have secretbox we require a signer and have to add authentication"
            box = nacl.public.Box(signer.keypair.naclprivate, self.naclpublic)
            return box.encrypt(data, encoder=(nacl.encoding.URLSafeBase64Encoder if b64 else nacl.encoding.RawEncoder))
        else:
            raise ToBeImplementedException(name="encrypt for"+self._key.__class__.__name__)

    def decrypt(self, data, b64=False, signer=None):
        """
        Decrypt date encrypted with encrypt (above)        

        :param data:
        :b64 bool:  Try if want result encoded
        :signer AccessControlList: If result was signed (currently ignored for RSA, reqd for NACL)
        """
        if isinstance(self._key, RSA._RSAobj):
            if b64:
                data = CryptoLib.b64dec(data)
            enckey = data[0:128]    # Just the RSA encryption of the Aes key - 128 bytes
            data = data[128:]
            cipher = PKCS1_OAEP.new(self._key)
            aeskey = cipher.decrypt(enckey)     # Matches aeskey in encrypt
            return CryptoLib.sym_decrypt(data, aeskey)
        elif isinstance(self._key, (nacl.public.PrivateKey, nacl.signing.SigningKey)):
            assert signer, "Until PyNaCl bindings have secretbox we require a signer and have to add authentication"
            # Naclpublic comes from either one already stored on ACL or if it has a private key can be derived from that.
            naclpublic = (signer.naclpublic and self._importkey(signer.naclpublic))  or signer.keypair.naclpublic
            assert naclpublic
            box = nacl.public.Box(self.naclprivate, naclpublic)
            #Convert data to "str" first as its most likely unicode having gone through JSON.
            return box.decrypt(str(data), encoder=(nacl.encoding.URLSafeBase64Encoder if b64 else nacl.encoding.RawEncoder))
        else:
            raise ToBeImplementedException(name="KeyPair.decrypt for "+self._key.__class__.__name__)

class WordHashKey(object):   #TODO-LIBSODIUM-CHECK-THIS-FUNCTION maybe replace with deterministic pub key from mnemonic
    """
    This is an odd, not really private/public key pair but it pretends to be.
    It uses a key selected by the mnemonic words as the "private" key, and its hash as the public key.
    The key is not stored with a keypair, either private or public since storing it would potentially expose it.

    _public  hash of private
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
            raise ToBeImplementedException("WordHashKey init if neither mnemonic or public")

    def publickey(self):  # Dummy, as functions are on key overall, not on private/public
        #if CryptoLib.defaultlib != CryptoLib.CRYPTO: raise ToBeImplementedException(name="#TODO-LIBSODIUM")
        return self

    def sign(self, value, **options):
        #if CryptoLib.defaultlib != CryptoLib.CRYPTO: raise ToBeImplementedException(name="#TODO-LIBSODIUM")
        return CryptoLib.sym_encrypt(value, self._private, b64=False, **options)    # b64 false because caller does it

    def verify(self, sigtocheck, check, **options):
        #if CryptoLib.defaultlib != CryptoLib.CRYPTO: raise ToBeImplementedException(name="#TODO-LIBSODIUM")
        if self._private: # Check if we have _private, i.e. it is pretending to be on our KeyChain
            return CryptoLib.sym_encrypt(value, self._private, b64=False, **options) == check
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
        return "WORDHASH:"+self._public     # _public is a hash already

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


