# encoding: utf-8

from datetime import datetime
from json import loads
from CryptoLib import CryptoLib
from StructuredBlock import StructuredBlock

"""
A collection of classes that represent objects that are signed, dated, encrypted etc

For a block { ... }
Signed = { signed: {...}, signatures: { date: ISO, hash: hex  publickey: hex }

The date is optional, but recommended
The date is included in the sig

Note they are not subclassed off StructuredBlock because they have, rather than are, StructuredBlocks
"""

# TODO-SIGNED update docs on SignedBlocks

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
            sb = self._sb(create=True)
            self._sb().__setattr__(name, value)   # Pass to SB - should create if not already there
            self._dirty()                         # Note recurses but just once

    def __getattr__(self, name):
        if name and name[0] == "_":
            return self.__dict__.get(name, None)    # Get _structuredblock, _hash etc locally
        else:
            return self._sb().__getattr__(name)  # Pass to SB - should create if not already there

    def __repr__(self):
        return "SignedBlock(%s)" % self.__dict__

    def _sb(self, verbose=False, create=False, **options):
        """
        :return: StructuredBlock, retrieve if necessary, can be None
        """
        if not self._structuredblock and self._hash:
            self._structuredblock = StructuredBlock.block(self._hash, verbose=verbose, **options)
        if create and not self._structuredblock:
            self._structuredblock = StructuredBlock()
        return self._structuredblock

    def _h(self, verbose=False, **options):
        """
        :param options: undefined but may add one to prevent storing
        :return: hash of StructuredBlock suitable for signing, will store block first, may be None
        """
        if not self._hash and self._structuredblock:
            self._hash = self._structuredblock.store(verbose=verbose, **options)
        return self._hash

    def __init__(self, hash=None, structuredblock=None, signatures=None, verbose=False, **options):
        """
        Create a signedblock - but dont sign it yet
        :param hash: hash of block - will retrieve structuredblock if reqd
        :param structuredblock: dict, JSON string or StructuredBlock
        """
        if structuredblock and not isinstance(structuredblock, StructuredBlock):
            structuredblock = StructuredBlock(structuredblock) # Handles dict or json of dict
        self._structuredblock = structuredblock
        self._hash = hash
        self._signatures = signatures or []

    def _dirty(self):
        # TODO - could get smarter about this, and check probably hash against _hash before clearing it
        self._hash = None       # Cant be stored, as changed
        self._signatures = []   # Cant be signed, as changed

    def sign(self, keypair, verbose=False, **options):
        """
        Add a signature to a StructuredBlock
        :param keypair:
        :return: self
        TODO move to public key / private key pair
        """
        date = datetime.now()
        signature = CryptoLib.signature(keypair, date, self._h(verbose=verbose, **options) )
        self._signatures.append({ "date": date, "signature": signature, "publickey": CryptoLib.exportpublic(keypair)})
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
            verified = CryptoLib.verify(s["publickey"], s["signature"], s["date"],  self._h(verbose=verbose, **options))
            if not verified:
                return False
        return True

    def store(self, verbose=False, **options):
        for s in self._signatures:
            #DHT_store(self, table, key, value, **options)
            ss = s.copy()
            ss["hash"] = self._h(verbose=verbose, **options)
            self._sb().transport.DHT_store("signedby",s["publickey"],ss, verbose=verbose, **options)

    @classmethod
    def fetch(cls, publickey, verbose=False, **options):
        lines = StructuredBlock.transport.DHT_fetch("signedby", CryptoLib.exportpublic(publickey), verbose=verbose, **options)
        if verbose: print "SignedBlock.fetch found ",len(lines)
        results = {}
        for block in [ loads(line) for line in lines ]:
            key = block["hash"]
            if not results.get(key,None):
                results[key] = SignedBlock(hash=key)
            results[key]._signatures.append(block)
        # Turn it into a list of SignedBlock - stores the hashes but doesnt fetch the data
        sbs = [ results[key] for key in results]
        return sbs

