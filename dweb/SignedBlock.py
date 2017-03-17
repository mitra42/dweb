# encoding: utf-8

from datetime import datetime
import dateutil.parser  # pip py-dateutil
from json import loads
from misc import MyBaseException, _print
from CryptoLib import CryptoLib, KeyPair
from CommonBlock import Transportable
from StructuredBlock import SmartDict, StructuredBlock


"""
A collection of classes that represent objects that are signed, dated, encrypted etc

Signed = { StructuredBlock|Hash, signatures: { date: ISO, signature: hex  publickey: hex }

The date is included in what is signed

Note they are not subclassed off StructuredBlock because they have, rather than are, StructuredBlocks
"""

class SignedBlockEmptyException(MyBaseException):
    msg = "Cant sign an empty block"

class Signature(SmartDict):
    """
    Encapsulate a signature - part of a SignedBlock
    Partial mirror of this is in dweb.js
    """
    pass

    @classmethod
    def sign(cls, keypair, hash):
        date = datetime.now()
        signature = CryptoLib.signature(keypair, date, hash)
        return cls({"date": date, "signature": signature, "signedby": keypair.store().publichash})

    def verify(self, hash=None):
        return CryptoLib.verify(self, hash=hash)

class Signatures(list):
    """
    A list of Signature
    """
    def earliest(self):
        """
        :return: earliest date of a list of signatures
        """
        return min(sig.date for sig in self)

    def verify(self, hash=None):
        """
        :param hash: hash to check (None to check hash in sigs)
        :return: True if all signatures verify
        """
        return all(s.verify(hash=hash) for s in self)

class SignedBlock(object):
    """
    A SignedBlock groups data with signatures - for internal use
    The signatures are stored as quads (hash of data; date; signature; hash of pubkey)
    So this object is not "Transportable"

    { Structured data, Hash, [ date, signature, publickey ]* }
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
        #Exception UnicodeDecodeError if data binary
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
            self._hash = self._structuredblock.store(verbose=verbose, **options) #TODO-REFACTOR-STORE
        return self._hash

    def __init__(self, hash=None, structuredblock=None, signatures=None, verbose=False, **options):
        """
        Create a signedblock - but dont sign it yet.
        Adapted into dweb.js

        :param hash: hash of block - will retrieve structuredblock if reqd
        :param structuredblock: dict, JSON string or StructuredBlock
        """
        if structuredblock and not isinstance(structuredblock, StructuredBlock):
            structuredblock = StructuredBlock(structuredblock) # Handles dict or json of dict
        self._structuredblock = structuredblock
        self._hash = hash
        self._signatures = Signatures(signatures or [])

    def _dirty(self):
        # TODO - could get smarter about this, and check probably hash against _hash before clearing it
        self._hash = None       # Cant be stored, as changed
        self._signatures = Signatures([])   # Cant be signed, as changed

    def date(self):
        """
        :return: Earliest signed date or None
        """
        if not self._signatures:
            return None # Undated
        else:
            return self._signatures.earliest()

    def sign(self, keypair, verbose=False, **options):
        """
        Add a signature to a StructuredBlock

        :param keypair:
        :return: self
        """
        if not (self._hash or self._structuredblock):
            raise SignedBlockEmptyException()
        self._signatures.append(Signature.sign(keypair=keypair, hash=self._h(verbose=verbose, **options)))
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
        if verify_atleastone and not len(self._signatures):
            return False
        return self._signatures.verify(hash=self._h(verbose=verbose, **options))

    def store(self, verbose=False, **options):
        """
        Store any signatures in the Transport layer, content must already have been stored before signing
        """
        for s in self._signatures:
            ss = s.copy()
            self._sb().transport.add(hash=self._h(verbose=verbose, **options), date = ss.date,
                                     signature = ss.signature, signedby = ss.signedby, verbose=verbose, **options)

    def content(self, **options):
        return self._sb().content()

    def path(self, urlargs, verbose=False):
        #if verbose: print "SignedBlock.path:", urlargs
        return self._sb(verbose=verbose).path(urlargs, verbose)  # Pass to SB and walk its path


class SignedBlocks(list):
    """
    A list of SignedBlock
    """

    @classmethod
    def fetch(cls, hash=None, verbose=False, **options):
        """
        Find all the related Signatures.

        :param hash:
        :param verbose:
        :param options:
        :return: SignedBlocks which is a list of SignedBlock
        """
        #key = CryptoLib.export(publickey) if publickey is not None else None,
        lines = Transportable.transport.list(hash=hash, verbose=verbose, **options)
        if verbose: print "SignedBlock.fetch found ",len(lines) if lines else None
        results = {}
        for block in lines:
            s = Signature(block)
            key = s.hash
            if not results.get(key,None):
                results[key] = SignedBlock(hash=key)
            if isinstance(s.date, basestring):
                s.date = dateutil.parser.parse(s.date)
            if CryptoLib.verify(s):
                results[key]._signatures.append(s)

        # Turn it into a list of SignedBlock - stores the hashes but doesnt fetch the data
        sbs = SignedBlocks([ results[key] for key in results])
        return sbs

    def latest(self):
        dated = { sb.date(): sb for sb in self} # Use date of first sig
        latest = max(key for key in dated)      # Find date of SB with latest first sig
        return dated[latest]

    def sorteddeduplicated(self):
        """
        Extract the latest, and return a deduplicated, ordered list of rest
        :return: latest signed block, [ signed blocks in date order excluding latest ]*
        """
        dated = {sb.date(): sb for sb in self}  # Extract date of first sig of each block
        sorted = dated.keys()
        sorted.sort()       # Earliest first
        return [ dated[date] for date in sorted ]
