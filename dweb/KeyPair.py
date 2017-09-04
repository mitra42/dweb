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
from Errors import ToBeImplementedException

from CommonBlock import SmartDict
from CryptoLib import CryptoLib, SecurityWarning, WordHashKey, PrivateKeyException

# See Libsodium docs
# https://download.libsodium.org/doc/public-key_cryptography/authenticated_encryption.html
# https://pynacl.readthedocs.io/en/latest/encoding/
#TODO-BACKPORT - review this file


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

    naclkeyclasses = {  # Note JS also uses "NACL SEED"
        nacl.public.PublicKey: "NACL PUBLIC",
        nacl.public.PrivateKey: "NACL PRIVATE",
        nacl.signing.SigningKey: "NACL SIGNING",
        nacl.signing.VerifyKey: "NACL VERIFY",
    }

    def preflight(self, dd):
        if self._key_has_private(dd["_key"]) and not dd.get("_acl") and not self._allowunsafestore:
            raise SecurityWarning(message="Probably shouldnt be storing private key")  # Can set KeyPair._allowunsafestore to allow this when testing
        if dd.get(
                "_key"):  # Based on whether the CommonList is master, rather than if the key is (key could be master, and CL not)
            dd["key"] = self.privateexport if self._key_has_private(dd["_key"]) else self.publicexport
        return super(KeyPair, self).preflight(dd=dd)

    def __repr__(self):
        return "KeyPair" + repr(self.__dict__)  # TODO only useful for debugging,

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

    @property
    def key(self):
        """
        Returns key - maybe public or private (looks like most places are using _key instead of key
        :return:
        """
        return self._key

    def _importkey(self, value):
        # Import a key from a string
        # Call route is ... data.setter > ...> key.setter > _importkey
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
                keyclass = [k for k in KeyPair.naclkeyclasses if KeyPair.naclkeyclasses[k] == tag][
                    0]  # e.g. nacl.public.PrivateKey
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
        else:  # Its already a key
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
            raise ToBeImplementedException(name="mnemonic for " + self._key.__class__.__name__)

    def _exportkey(self, key):
        # Export any of a set of key classes, note those with explicit publicexport() etc methods should have been already handled.
        tag = self.naclkeyclasses.get(key.__class__)
        if tag:
            return tag + ":" + key.encode(nacl.encoding.URLSafeBase64Encoder)
        elif isinstance(key, RSA._RSAobj):
            return key.exportKey("PEM")
        else:
            raise ToBeImplementedException(name="export for " + key.__class__.__name__)

    @property
    def publicexport(self):
        if isinstance(self._key, WordHashKey):  # Handle own classes which have a publicexport() method
            return self._key.publicexport()  # (Dont use k as its a url already)
        else:
            return self._exportkey(self.public)

    @property
    def privateexport(self):
        if isinstance(self._key, WordHashKey):
            return ""  # Not exportable
        elif isinstance(self._key, (nacl.public.PublicKey, nacl.signing.VerifyKey)):  # Dont have private
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
            raise ToBeImplementedException(name="KeyPair._key_has_private for _key is " + key.__class__.__name__)

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
        if isinstance(self._key, RSA._RSAobj):
            # TODO currently it ignores "sign" which was introduced with NACL, if keep using RSA then implement here
            aeskey = CryptoLib.randomkey()
            msg = CryptoLib.sym_encrypt(data, aeskey)
            cipher = PKCS1_OAEP.new(
                self._key.publickey())  # Note can only encrypt the key with PKCS1_OAEP as it can only handle 86 bytes
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
            raise ToBeImplementedException(name="encrypt for" + self._key.__class__.__name__)

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
            enckey = data[0:128]  # Just the RSA encryption of the Aes key - 128 bytes
            data = data[128:]
            cipher = PKCS1_OAEP.new(self._key)
            aeskey = cipher.decrypt(enckey)  # Matches aeskey in encrypt
            return CryptoLib.sym_decrypt(data, aeskey)
        elif isinstance(self._key, (nacl.public.PrivateKey, nacl.signing.SigningKey)):
            assert signer, "Until PyNaCl bindings have secretbox we require a signer and have to add authentication"
            # Naclpublic comes from either one already stored on ACL or if it has a private key can be derived from that.
            # TODO-REFACTOR-NACL use a key dict in the keypair like in the JS
            naclpublic = (signer.naclpublic and self._importkey(signer.naclpublic)) or signer.keypair.naclpublic
            assert naclpublic
            box = nacl.public.Box(self.naclprivate, naclpublic)
            # Convert data to "str" first as its most likely unicode having gone through JSON.
            return box.decrypt(str(data),
                               encoder=(nacl.encoding.URLSafeBase64Encoder if b64 else nacl.encoding.RawEncoder))
        else:
            raise ToBeImplementedException(name="KeyPair.decrypt for " + self._key.__class__.__name__)

