# encoding: utf-8

from hmac import HMAC
from datetime import datetime
from json import loads, dumps

import hashlib
import base64

from Crypto import Random
#from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA

from StructuredBlock import StructuredBlock
"""
A collection of classes that represent objects that are signed, dated, encrypted etc

For a block { ... }
Signed = { signed: {...}, signatures: { date: ISO, hmac: hex  publickey: hex }

The date is optional, but recommended
The date is included in the sig
"""

class SignedBlock(StructuredBlock):

    def __init__(self, data):
        """
        Create a signedblock - but dont sign it yet
        :param data: dict, JSON string or StructuredBlock
        """
        if not isinstance(data, StructuredBlock):
            data = StructuredBlock(data) # Handles dict or json of dict
        self.signed = data
        self.signatures = []

    def _hasheddata(self, date):
        base = date.isoformat() + self.signed._data      # Data is a canonical string suitable for signing
        return HMAC("", base, hashlib.sha1).digest()

    def sign(self, keypair):
        """
        Add a signature to a StructuredBlock
        :param keypair:
        :return: self
        TODO move to public key / private key pair
        """
        date = datetime.now()
        h = self._hasheddata(date)
        signature = base64.urlsafe_b64encode(keypair.decrypt(h))   # 32 is a random unused parameter, -1 strips trailing CR
        self.signatures.append({ "date": date, "signature": signature, "publickey": keypair.publickey().exportKey("PEM") } )
        return self

    def verify(self):
        for s in self.signatures:
            base = self._hasheddata(s["date"])
            pubkey = RSA.importKey(s["publickey"])
            decrypted = pubkey.encrypt(base64.urlsafe_b64decode(s["signature"]),32)[0]
            if decrypted != base:
                return False
        return True

    @classmethod
    def keygen(cls):
        """
        Create a public/private key pair,
        :return: key which has .publickey() method
        """
        return RSA.generate(1024, Random.new().read)

#http://stackoverflow.com/questions/28426102/python-crypto-rsa-public-private-key-with-large-file
