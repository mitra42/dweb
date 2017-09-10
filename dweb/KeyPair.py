# encoding: utf-8

from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from mnemonic import Mnemonic
import nacl.secret
import nacl.utils
import nacl.encoding
import nacl.hash
import nacl.public
import nacl.signing
from Errors import ToBeImplementedException, EncryptionException

from util_multihash import encode, SHA1, SHA2_256, SHA2_512, SHA3
from base58 import b58encode
from SmartDict import SmartDict

# See Libsodium docs
# https://download.libsodium.org/doc/public-key_cryptography/authenticated_encryption.html
# https://pynacl.readthedocs.io/en/latest/encoding/

#TODO-BACKPORT - review this file


class KeyPair(SmartDict):
    """
    Encapsulates public key cryptography

    Fields:
    _key    Holds a structure, that may depend on cryptographic library used.

    Constants:
    KeyPair.KEYTYPESIGN=1, KEYTYPEENCRYPT=2, KEYTYPESIGNANDENCRYPT=3  specify which type of key to generate

    PyNaCl implementation
    Note JS uses libsodium bindings which are similar but not exactly the same.

    _key = {
        sign: { publicKey: Uint8Array, privateKey: Uint8Array, keyType: "ed25519" }
        encrypt: { publicKey: Uint8Array, privateKey: Uint8Array},
        seed: Uint8Array,
    }
     */

    This uses the CryptoLib functions to encapsulate KeyPairs of different Public Key systems.
    Currently supports: RSA; and the PyNaCl bindings to LibSodium
    It is intended to provide a consistent interface to the application, masking the characteristics of different crypto systems underneath.
    """
    table = "kp"
    _allowunsafestore = False

    KEYTYPESIGN = 1             # Want a signing key
    KEYTYPEENCRYPT = 2          # Want a key for encryption
    KEYTYPESIGNANDENCRYPT = 3   # Want both types of key - this is usually used for encryption due to libsodium-wrappers limitations.

    """  TODO-BACKPORT shouldnt need this
    naclkeyclasses = {  # Note JS also uses "NACL SEED"
        nacl.public.PublicKey: "NACL PUBLIC",
        nacl.public.PrivateKey: "NACL PRIVATE",
        nacl.signing.SigningKey: "NACL SIGNING",
        nacl.signing.VerifyKey: "NACL VERIFY",
    }
    """

    def __repr__(self):
        return "KeyPair" + repr(self.__dict__)  # TODO only useful for debugging,


    @property
    def key(self): return self._key # Unused

    @key.setter
    def key(self, value):
        """
        Set a key, convert formats or generate key if required.
        """
        if isinstance(value, basestring):  # Should be exported string, maybe public or private
            self._key = self._importkey(value)
        else:  # Its already a key
            self._key = value

            if isinstance(value, dict): # Dictionary of options
                if value.get("mnemonic",None):
                    # TODO-BACKPORT access mnemonic to seed
                    raise ToBeImplementedException(message="multihash needs implementing")
                    """
                    if (value.mnemonic === "coral maze mimic half fat breeze thought champion couple muscle snack heavy gloom orchard tooth alert cram often ask hockey inform broken school cotton") { // 32 byte
                        value.seed = "01234567890123456789012345678901";  #Note this is seed from mnemonic above
                        console.log("Faking mnemonic encoding for now")
                    } else {
                        assert False, "MNEMONIC STILL TO BE IMPLEMENTED"    #TODO-mnemonic
                    }
                    """
                if value.get("passphrase",None):
                    pp = value["passphrase"]
                    for i in range(0,100):  # 100 iterations
                        pp = KeyPair.sha256(pp) # Its write length for seed = i.e. 32 bytes
                    value["seed"] = pp
                if value.get("keygen", None):
                    assert nacl.bindings.crypto_box_SECRETKEYBYTES == nacl.bindings.crypto_sign_SEEDBYTES,"Presuming seeds same size (they are on JS"
                    value["seed"] = nacl.utils.random(nacl.bindings.crypto_sign_SEEDBYTES)
                    del value["keygen"]
                if value.get("seed", None):
                    value = KeyPair._keyfromseed(value["seed"], self.KEYTYPESIGNANDENCRYPT, self.verbose);  #TODO-BACKPORT does this exist/work
            self._key = value

    def preflight(self, dd):
        """
        Subclasses SmartDict.preflight, checks not exporting unencrypted private keys, and exports private or public.

        :param dd: dict of fields, maybe processed by subclass
        :returns: dict of fields suitable for storing in Dweb
        """
        if self._key_has_private(dd["_key"]) and not dd.get("_acl") and not self._allowunsafestore:
            raise SecurityWarning(message="Probably shouldnt be storing private key")  # Can set KeyPair._allowunsafestore to allow this when testing
        if dd.get("_key"):  # Based on whether the CommonList is master, rather than if the key is (key could be master, and CL not)
            dd["key"] = self.privateexport() if self._key_has_private(dd["_key"]) else self.publicexport()  #TODO-BACKPORT note moved from attr to function
        return super(KeyPair, self).preflight(dd=dd)

    @classmethod
    def _keyfromseed(cls, seed, keytype, verbose):
        """
        Generate a key from a seed,

        :param seed:    uint8array or binary string (not urlsafebase64) to generate key from
        :param keytype: One of KeyPair.KEYTYPExyz to specify type of key wanted
        :returns:       Dict suitable for storing in _key
        """
        key = {}
        key["seed"] = seed
        if keytype == cls.KEYTYPESIGN or keytype == cls.KEYTYPESIGNANDENCRYPT:
            key["sign"] = nacl.signing.SigningKey(seed)     # ValueError if seed != 32 bytes
        if keytype == cls.KEYTYPEENCRYPT or keytype == cls.KEYTYPESIGNANDENCRYPT:
            key["encrypt"] = nacl.public.PrivateKey(seed)   # ValueError if seed != 32 bytes
        return key

    """
    OBS - but don't delete as contains old code for other crypto. '
    @classmethod
    def keygen(cls, keyclass=None, keytype=None, mnemonic=None, seed=None, verbose=False, **options):
        "-""
        Generate a new key pair
        ERR: ValueError - wrong size seed

        :param options: unused
        :keyclass class: RSA, CryptoLib.NACL, or WordHashKey
        :keytype int: one of KEYTYPESIGN, KEYTYPEENCRYPT or KEYTYPESIGNANDENCRYPT (latter not supported)
        :mnemonic string: Words to convert into seed for key (valid with NACL and WordHashKey)
        :seed binary: Seed to keygen (valid with keyclass=NACL, invalid with mnemonic)
        :return: KeyPair
        "-""
        # assert keytype  # Required parameter
        if not keyclass:
            keyclass = RSA if CryptoLib.defaultlib == CryptoLib.CRYPTO else CryptoLib.NACL
        if verbose: print "Generating key for", keyclass
        if mnemonic:
            seed = str(Mnemonic("english").to_entropy(mnemonic))
        if keyclass in (RSA, "RSA"):
            if seed:
                raise ToBeImplementedException(name="keygen - support for RSA with seeds")
            key = RSA.generate(1024, Random.new().read)
        elif keyclass in (CryptoLib.NACL,):
            if keytype == cls.KEYTYPESIGN:
                key = nacl.signing.SigningKey(
                    seed) if seed else nacl.signing.SigningKey.generate()  # ValueError if seed != 32 bytes
            elif keytype == cls.KEYTYPEENCRYPT:
                key = nacl.public.PrivateKey(
                    seed) if seed else nacl.public.PrivateKey.generate()  # ValueError if seed != 32 bytes
            else:
                raise ToBeImplementedException(name="keygen for keytype=" + str(keytype))
        elif keyclass in (WordHashKey,):
            key = WordHashKey(mnemonic=mnemonic) if mnemonic else WordHashKey.generate(
                strength=256)  # Must be 32 bytes=156 for symkey (was using 128)
        else:
            raise ToBeImplementedException(name="keygen for keyclass=" + keyclass.__class__.__name__)
        return cls(key=key)
    END OF OBS BUT NOT DELETABLE
    """

    def _importkey(self, value):
        """
        Import a key, sets fields of _key without disturbing any already set unless its SEED.

        :param value: "xyz:1234abc" where xyz is one of "NACL PUBLIC, NACL SEED, NACL VERIFY" and 1234bc is a ursafebase64 string
                Note NACL PRIVATE, NACL SIGNING,  are not yet supported as "NACL SEED" is exported

        """
        if isinstance(value, (list,tuple)):
            for i in value: self._importkey(value)
        else:
            assert isinstance(value, basestring)  # Should be exported string, maybe public or private
            # First tackle standard formats created by exporting functionality on keys
            """
            #RSA not supported currently
            if "-----BEGIN " in value:
                return RSA.importKey(value)
            else
            """
            if ":" in value:
                tag, hash = value.split(':')
                """
                #WORDHASH not supported currently - probably never will be
                # Tackle our own formats always xyz:key
                if tag == "WORDHASH":
                    return WordHashKey(public=hash)
                else
                """
                if not self._key:
                    self._key = {}
                if tag == "NACL PUBLIC":    self._key["encrypt"] = nacl.public.PrivateKey(str(hash),  nacl.encoding.URLSafeBase64Encoder);
                if tag == "NACL VERIFY":    self._key["sign"] = nacl.signing.VerifyKey(str(hash), nacl.encoding.URLSafeBase64Encoder);
                if tag == "NACL SEED":      self._key = self._keyfromseed(hash, self.KEYTYPESIGNANDENCRYPT )
                else:
                    raise EncryptionException(message="Unsupported key for import: "+tag)
            else:
                raise EncryptionException(message="Badly formatted key for import: " + value)


    def publicexport(self):
        """
        :return: an array include one or more "NACL PUBLIC:abc123", or "NACL VERIFY:abc123" urlsafebase64 string
        """
        res = []
        if self._key.get("encrypt", None):
            res.append("NACL PUBLIC:"+self._key["encrypt"].encode(nacl.encoding.URLSafeBase64Encoder))
        if self._key.get("sign", None):
            res.append("NACL VERIFY:"+self._key["sign"].encode(nacl.encoding.URLSafeBase64Encoder))

    """
    OBSOLETE - not used now
    @property
    def private(self):
        #:return: Private (RSA) key
        if not self.has_private():
            raise PrivateKeyException()
        return self._key

    @private.setter
    def private(self, value):
        #Sets the key from a string, or a key (doesnt appear to be used)
        #:param value: Either a string from exporting the key, or a RSA key
        #:return:
        "=""
        self.key = value
        if not self.has_private():  # Check it was really a Private key
            raise PrivateKeyException()

    @property
    def public(self):
        #Return the public side of any Private/Public key pair suitable for encryption or verification

        #:return: Public (RSA) key
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
        "-""
        Sets the key from either a string or a key. (Doesnt appear to be being used)

        :param value: Either a string from exporting the key, or a RSA key
        :return:
        "-""
        self.key = value

    @property
    def mnemonic(self):
        if isinstance(self._key, (nacl.public.PrivateKey, nacl.signing.SigningKey)):
            return Mnemonic("english").to_mnemonic(self._key.encode(nacl.encoding.RawEncoder))
        else:
            raise ToBeImplementedException(name="mnemonic for " + self._key.__class__.__name__)


    """

    def privateexport(self):
        #if isinstance(self._key, WordHashKey):
        #    return ""  # Not exportable
        #elif isinstance(self._key, (nacl.public.PublicKey, nacl.signing.VerifyKey)):  # Dont have private
        res = []
        if self._key.get("seed", None):
            res.append("NACL SEED:" + self._key["seed"])
        else:
            raise EncryptionException(message="No seed to export")

    @staticmethod
    def _key_has_private(key):
        """
        :param key:
        :return: true if the _key has a private version (or sign or encrypt or seed)
        """
        # Helper function used by has_private and preflight
        #if isinstance(key, (RSA._RSAobj, WordHashKey)):
        #    return key.has_private()
        if isinstance(key.get("encrypt",None), nacl.public.PrivateKey) or isinstance(key.get("sign",None), nacl.public.SigningKey):
            return True
        if isinstance(key.get("encrypt", None), nacl.public.PublicKey) or isinstance(key.get("sign", None),
                                                                                          nacl.public.VerifyKey):
            return False
        raise EncryptionException(mesage="Unrecognized keys" + repr(key))

    def has_private(self):
        """
        :return: true if key has a private version (or sign or encrypt or seed)
        """
        return self._key_has_private(self._key)

    """
    # OBSPLETE - NOT USED ANY MORE
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
            raise ToBeImplementedException(name="naclpublic for _key is " + self._key.__class__.__name__)
            # return None

    def naclpublicexport(self):
        # Export the public encryption key, for NACL this made by turning SigningKey into PrivateKey into Publickey
        if isinstance(self._key, (nacl.public.PrivateKey, nacl.signing.SigningKey)):
            return self._exportkey(self.naclpublic)
        else:
            return None
    """

    def encrypt(self, data, b64=False, signer=None):
        """
         Encrypt a string, the destination string has to include any information needed by decrypt, e.g. Nonce etc

         :param data:   String to encrypt
         :b64 bool:  True if want result encoded in urlsafebase64
         :signer AccessControlList or KeyPair: If want result signed (currently ignored for RSA, reqd for NACL)
         :return: str, binary encryption of data or urlsafebase64
        """
        """
        #NOT SUPPORTING RSA
        if isinstance(self._key, RSA._RSAobj):
            # TODO currently it ignores "sign" which was introduced with NACL, if keep using RSA then implement here
            aeskey = KeyPair.randomkey()
            msg = KeyPair.sym_encrypt(data, aeskey)
            cipher = PKCS1_OAEP.new(
                self._key.publickey())  # Note can only encrypt the key with PKCS1_OAEP as it can only handle 86 bytes
            ciphertext = cipher.encrypt(aeskey)
            res = ciphertext + msg
            if b64:
                res = KeyPair.b64enc(res)
            return res
        """
        #if isinstance(self._key, (nacl.public.PrivateKey, nacl.signing.SigningKey)):
        assert signer, "Until PyNaCl bindings have secretbox we require a signer and have to add authentication"
        nonce = nacl.utils.random(nacl.bindings.crypto_box_NONCEBYTES)

        box = nacl.public.Box(signer.keypair._key["sign"], self._key["encrypt"])
        return box.encrypt(data, nonce=nonce, encoder=(nacl.encoding.URLSafeBase64Encoder if b64 else nacl.encoding.RawEncoder))

    def decrypt(self, data, b64=False, signer=None):
        """
        Decrypt date encrypted with encrypt (above)

        :param data:  urlsafebase64 or Uint8array, starting with nonce
        :param signer AccessControlList: If result was signed (currently ignored for RSA, reqd for NACL)
        :param outputformat: Compatible with LibSodium, typicall "text" to return a string
        :return: Data decrypted to outputformat
        :raises: EnryptionError if no encrypt.privateKey, CodingError if !data||!signer
        """
        """
        #NOt supporting
        if isinstance(self._key, RSA._RSAobj):
            if b64:
                data = KeyPair.b64dec(data)
            enckey = data[0:128]  # Just the RSA encryption of the Aes key - 128 bytes
            data = data[128:]
            cipher = PKCS1_OAEP.new(self._key)
            aeskey = cipher.decrypt(enckey)  # Matches aeskey in encrypt
            return KeyPair.sym_decrypt(data, aeskey)
        elif isinstance(self._key, (nacl.public.PrivateKey, nacl.signing.SigningKey)):
        """
        if not data: raise EncryptionException(message="Cant decrypt empty data")
        if not signer: raise EncryptionException(message="Until PyNaCl bindings have secretbox we require a signer and have to add authentication")
        nonce = data[0:nacl.bindings.crypto_box_NONCEBYTES]
        data = data[nacl.bindings.crypto_box_NONCEBYTES:]
        box = nacl.public.Box(self._key["encrypt"], signer.keypair._key["sign"])
        # Convert data to "str" first as its most likely unicode having gone through JSON.
        return box.decrypt(str(data), nonce=nonce,
                           encoder=(nacl.encoding.URLSafeBase64Encoder if b64 else nacl.encoding.RawEncoder))

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

    def sign(self, date, url, verbose=False, **options):
        """
        Sign and date a url using public key function.
        Pair of "verify()"

        :param date: Date that signing (usually now)
        :param url: URL being signed, it could really be any data,
        :return: signature that can be verified with verify
        """
        assert date and url
        signable = KeyPair._signable(date, url)
        sig = self._key["sign"].sign(signable, nacl.encoding.URLSafeBase64Encoder).signature
        # Can uncommen next line if seeing problems veriying things that should verify ok - tests immediate verification
        self.verify(date, url, sig)
        return sig

    def verify(self, date, url, urlb64sig): #TODO-BACKPORT change footprint on JS (and called from Signature.verify)
        """
        Verify a signature generated by sign()
        TODO - this is not yet incorporated - should be in CommonList and currently just generates an assertion fail if not verified.

        :param signable: date and url exactly as signed.
        :param urlb64sig: urlsafebase64 encoded signature
        """
        sig = nacl.encoding.URLSafeBase64Encoder.decode(urlb64sig)
        signable = self._signable(date, url)  # If its not already a string, assume its a Signature and get its date and url fields
        try:
            self._key["sign"].verify_key.verify(signable, sig, encoder=nacl.encoding.RawEncoder)
        except nacl.exceptions.BadSignatureError:
            1 / 0  # This really shouldnt be happenindg - catch it and figure out why
            return False
        else:
            return True

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
            return data  # Its not a string to un-b64
        if isinstance(data, unicode):
            data = str(data)  # b64 doesnt like unicode
        try:
            return nacl.encoding.URLSafeBase64Encoder.decode(data)
        except TypeError as e:
            print "Cant urlsafe_b64decode data", data.__class__.__name__, data
            raise e

    @staticmethod
    def b64enc(data):
        """
        Encode arbitrary data to b64

        :param data:
        :return:
        """
        if data is None:
            return None  # Json can handle none
        elif not isinstance(data, basestring):
            return data  # Dont b64enc hope inner parts are encoded with their own dumps
        # Dont believe need to convert from unicode to str first
        try:
            return nacl.encoding.URLSafeBase64Encoder.encode(data)
        except TypeError as e:
            print "Cant urlsafe_b64encode data", data.__class__.__name__, e, data
            raise e
        except Exception as e:
            print "b64enc error:", e  # Dont get exceptions printed inside dumps, just obscure higher level one
            raise e

    @staticmethod
    def randomkey():
        """
        Return a key suitable for symetrically encrypting content or sessions

        :return:
        """
        # see http://stackoverflow.com/questions/20460061/pythons-pycrypto-library-for-random-number-generation-vs-os-urandom
        return nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)  # 32 bytes - required for SecretBox
        # return os.urandom(16)
        # return Random.new().read(32)
        # return Random.get_random_bytes(16)


    @classmethod
    def sym_encrypt(cls, data, sym_key, b64=False, **options):
        """
        Pair of sym_decrypt
        ERR: DecryptFail if cant decrypt - this is to be expected if unsure if have valid key (e.g. in acl.decrypt)

        :param data:        # Data to encrypt
        :param sym_key:     Key of arbitrary length - for consistency use KeyPair.randomkey() to generate or "SecretBox"
        :param b64:         True if want output in base64
        :param options:     Unused
        :return:            Encrypted string, either str or EncodedMessage (which is subclass of str)
        """
        if isinstance(sym_key, basestring):
            sym_key = nacl.secret.SecretBox(sym_key)  # Requires 32 bytes
        nonce = nacl.utils.random(nacl.bindings.crypto_secretbox_NONCEBYTES)
        encoder = nacl.encoding.URLSafeBase64Encoder if b64 else nacl.encoding.RawEncoder
        return sym_key.encrypt(data, nonce=nonce, encoder=encoder)  # Can take nonce parameter if reqd, but usually not,
        # return is EncryptedMessage instance which isinstance(basestring)
        #TODO-BACKPORT this wont work - need to return nonce+encrypted then convert to URLsafe


    @classmethod
    def sym_decrypt(cls, data, sym_key, b64=False, **options):
        """
        Decrypt data based on a symetric key

        :param data:    urlsafebase64 string or Uint8Array
        :param sym_key: symetric key encoded in urlsafebase64 or Uint8Array
        :param outputformat:    Libsodium output format one of "uint8array", "text", "base64" or "urlsafebase64"
        :returns:       decrypted data in selected outputformat
        """
        if not data:
            raise EncryptionException(message="Keypair.sym_decrypt meaningless to decrypt undefined, null or empty strings")
        if isinstance(sym_key, basestring):
            sym_key = nacl.secret.SecretBox(sym_key)  # Requires 32 bytes
        encoder = nacl.encoding.URLSafeBase64Encoder if b64 else nacl.encoding.RawEncoder
        if b64:
            data = str(data)  # URLSafeBase64Encoder can't handle Unicode
        nonce = data[0:nacl.bindings.crypto_secretbox_NONCEBYTES]
        data = data[nacl.bindings.crypto_secretbox_NONCEBYTES:]
        try:
            return sym_key.decrypt(data, nonce=nonce, encoder=encoder)
        except nacl.exceptions.CryptoError as e:
            raise DecryptionFail()  # Is expected in some cases, esp as looking for a valid key in acl.decrypt

    @staticmethod
    def sha256(data):
        """
        data:       String or Buffer containing string of arbitrary length
        returns:    32 byte Uint8Array with SHA256 hash
        """
        return nacl.hash.sha256(data, encoder=nacl.encoding.RawEncoder)

    @staticmethod
    def multihashsha256_58(data):   # Base58 of a Multihash of a Sha2_256 of data - as used by IPFS
        return b58encode(bytes(encode(data, SHA2_256)))
