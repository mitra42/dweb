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

Note they are not subclassed off StructuredBlock because they have, rather than are, StructuredBlocks
"""

class SignedBlock(object):
    """
    A SignedBlock groups data with signatures - for internal use
    Its stored as quads (hash of data; date; signature; pubkey)
    """
    """
    It has following properties
    Attribute           Access
    _structuredblock    _sb()   Structured data
    _hash               _h()    Hash of data once stored, (accessing this will cause it to be stored)
    _signatures                 Array of signatures
    """
    def __setattr__(self, name, value):
        if name and name[0] == "_":
            super(SignedBlock, self).__setattr__(name, value)   # Save _structuredblock, _hash etc locally
        else:
            self._sb().__setattr__(name, value)   # Pass to SB - should create if not already there
            self._dirty()                         # Note recurses but just once

    def __getattr__(self, name):
        if name and name[0] == "_":
            return super(SignedBlock, self).__getattr__(name)  # Save _structuredblock, _hash etc locally
        else:
            return self._sb().__getattr__(name)  # Pass to SB - should create if not already there

    def __repr__(self):
        return "SignedBlock(%s)" % self.__dict__

    def _sb(self, verbose=False, **options):
        """
        :return: StructuredBlock, retrieve if necessary, can be None
        """
        if not self._structuredblock and self._hash:
            self._structuredblock = StructuredBlock.block(self._hash, verbose=verbose, **options)
        return self._structuredblock

    def _h(self, verbose=False, **options):
        """
        :param options: undefined but may add one to prevent storing
        :return: hash of StructuredBlock suitable for signing, will store block first, may be None
        """
        if not self._hash and self._structuredblock:
            self._hash = self._structuredblock.store(verbose=verbose, **options)
        return self._hash

    def __init__(self, hash=None, structuredblock=None, verbose=False, **options):
        """
        Create a signedblock - but dont sign it yet
        :param hash: hash of block - will retrieve structuredblock if reqd
        :param structuredblock: dict, JSON string or StructuredBlock
        """
        if structuredblock and not isinstance(structuredblock, StructuredBlock):
            structuredblock = StructuredBlock(structuredblock) # Handles dict or json of dict
        self._structuredblock = structuredblock
        self._dirty()       # Clear signatures and hash

    def _dirty(self):
        # TODO - could get smarter about this, and check probably hash against _hash before clearing it
        self._hash = None       # Cant be stored, as changed
        self._signatures = []   # Cant be signed, as changed

    def _signable(self, date, verbose=False, **options):
        """
        Return a string suitable for signing with Private key - concatenates date and data
        Side effect of storing the block if not yet stored
        :param date:
        :return:
        """
        return date.isoformat()+self._h(verbose=verbose, **options) # Note side effect of storing the block if not yet stored

    def sign(self, keypair, verbose=False):
        """
        Add a signature to a StructuredBlock
        :param keypair:
        :return: self
        TODO move to public key / private key pair
        """
        date = datetime.now()
        signature = base64.urlsafe_b64encode(keypair.decrypt(self._signable(date, verbose=verbose)))
        self._signatures.append({ "date": date, "signature": signature, "publickey": keypair.publickey().exportKey("PEM") } )
        return self

    def verify(self, verbose=False, verify_atleastone=False, **options):
        """
        Verify the signatures on a block (if any)
        :param verbose: True for debugging output
        :param verify_atleastone: True if should fail if no signatures
        :param options: unused
        :return: True if all signatures present match
        """
        if verbose: print "SignedBlock.verify",self
        if verify_atleastone and not self._signatures:
            return False
        for s in self._signatures:
            base = self._signable(s["date"])
            if verbose: print "SignedBlock.verify.base=",base
            pubkey = RSA.importKey(s["publickey"])
            decrypted = pubkey.encrypt(base64.urlsafe_b64decode(s["signature"]),32)[0]
            if verbose: print "SignedBlock.verify.decrypted=",decrypted
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
