# encoding: utf-8

from json import dumps, loads
import base64
import hashlib
from datetime import datetime
from Crypto import Random
from Crypto.PublicKey import RSA
#from Crypto.Cipher import AES, PKCS1_OAEP
from misc import ToBeImplementedException
import sha3 # To add to hashlib

class CryptoLib(object):
    """
    Encapsulate all the Crypto functions in one place so can revise independently of rest of dweb

    """

    @staticmethod
    def Curlhash(data, hashscheme="SHA3256B64URL", **options):
        """
        :param data: Any length and combination of bytes
        :return: URL and Filename safe string   hashname.b64encoding
        """
        if hashscheme == "SHA1B64URL":
            return "SHA1B64URL." + base64.urlsafe_b64encode(hashlib.sha1(data).digest())
        elif hashscheme == "SHA3256B64URL":
            return "SHA3256B64URL." + base64.urlsafe_b64encode(hashlib.sha3_256(data).digest())
        elif hashscheme == "SHA3512B64URL":
            return "SHA3512256B64URL." + base64.urlsafe_b64encode(hashlib.sha3_512(data).digest())
        else:
            raise ToBeImplementedException(name="CryptoLib.urlhash for hashscheme="+hashscheme)

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
        return base64.urlsafe_b64encode(keypair.decrypt(CryptoLib._signable(date, data)))

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
        pubkey = CryptoLib.importpublic(sig.publickey)
        #b64decode requires a str, but signature may be unicode
        decrypted = pubkey.encrypt(base64.urlsafe_b64decode(str(sig.signature)), 32)[0]
        check = CryptoLib._signable(sig.date, hash or sig.hash)
        return check == decrypted

    @staticmethod
    def dumps(data):
        """
        Convert arbitrary data into a JSON string that can be deterministically hashed or compared.
        Must be valid for loading with json.loads (unless change all calls to that).

        :param data:    Any
        :return: JSON string that can be deterministically hashed or compared
        """
        # ensure_ascii = False was set otherwise if try and read binary content, and embed as "data" in StructuredBlock then complains
        # if it cant convert it to UTF8. (This was an example for the Wrenchicon), but loads couldnt handle return anyway.
        # sort_keys = True so that dict always returned same way so can be hashed
        # separators = (,:) gets the most compact representation
        return dumps(data, sort_keys=True, separators=(',', ':'), default=json_default)

    @staticmethod
    def keygen():
        """
        Create a public/private key pair.

        :return: key which has .publickey() method
        """
        return RSA.generate(1024, Random.new().read)

    @staticmethod
    def importpublic(exportedstr):
        """
        Import a public key, pair with export().

        :param exported: Exported public key
        :return: RSAobj containing just the public key
        """
        return RSA.importKey(exportedstr)

    @staticmethod
    def export(keypair, private=False, filename=None):
        """
        Export a public key, pair with importpublic

        :param keypair: RSA obj - could be private key or public key
        :return: String for export
        """
        if not private:
            keypair = keypair.publickey()   # Note this works if keypair is publickey
        exp = keypair.exportKey("PEM")
        if filename:
            with open(filename, 'wb') as f:
                f.write(exp)
        else:
            return exp



    # See http://stackoverflow.com/questions/28426102/python-crypto-rsa-public-private-key-with-large-file

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
