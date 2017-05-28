# encoding: utf-8

from datetime import datetime
import dateutil.parser  # pip py-dateutil
from json import loads
from misc import MyBaseException, AssertionFail, _print, ToBeImplementedException
from CryptoLib import CryptoLib
from KeyPair import KeyPair
from CommonBlock import Transportable, UnknownBlock
from StructuredBlock import SmartDict, StructuredBlock
from Transport import TransportURLNotFound, TransportFileNotFound
from Dweb import Dweb


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
    Encapsulate a signature - On the _signatures field of a signed StructuredBlock
    Partial mirror of this is in dweb.js
    """

    def __init__(self, block):
        super(Signature, self).__init__(block)
        if isinstance(self.date, basestring):
            self.date = dateutil.parser.parse(self.date)


    @classmethod
    def sign(cls, commonlist, hash, verbose=False):
        date = datetime.now()
        signature = CryptoLib.signature(commonlist.keypair, date, hash)
        if not commonlist._publichash:
            commonlist.store(verbose=verbose)
        return cls({"date": date, "signature": signature, "signedby": commonlist._publichash})

    def verify(self, hash=None):
        return CryptoLib.verify(self, hash=hash)

    def block(self, fetchblocks=True):
        """
        Find the block signed by this signature, usually a Structured Block but not always

        :return:
        """
        if fetchblocks:
            return UnknownBlock(hash=self.hash).fetch()  # We don't know its a SB, UnknownBlock.fetch() will convert
        else:
            return UnknownBlock(hash=self.hash)  # We don't know its a SB


class Signatures(list):
    """
    A list of Signature (note on Javascript this is just a list, and earliest is  static methods on the Signature class)
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

    @classmethod
    def fetch(cls, hash=None, verbose=False, fetchblocks=False, **options):
        """
        Find all the related Signatures.
        Exception: TransportURLNotFound if empty or bad URL

        :param hash:
        :param verbose:
        :param options:
        :return: SignedBlocks which is a list of StructuredBlock
        """
        #key = CryptoLib.export(publickey) if publickey is not None else None,
        assert hash is not None
        if verbose: print "SignedBlocks.fetch looking for hash=",hash,"fetchblocks=", fetchblocks
        try:
            lines = Dweb.transport.rawlist(hash=hash, verbose=verbose, **options)
        except (TransportURLNotFound, TransportFileNotFound) as e:
            return Signatures([])    # Its ok to fail as list may be empty
        else:
            if verbose: print "Signatures.fetch found ",len(lines) if lines else None
            results = {}
            sigs = Signatures(Signature(s) for s in lines )
            if fetchblocks:
                raise ToBeImplementedException(name="fetchblocks for Signatures")    # Note havent defined a way to store the block on the sig
            return Signatures([ s for s in sigs if CryptoLib.verify(s) ])

    def blocks(self, fetchblocks=True, verbose=False):
        results = {}
        for s in self:
            hash = s.hash
            if not results.get(hash, None):

                if fetchblocks:
                    results[hash] = UnknownBlock(hash=hash).fetch()  # We don't know its a SB, UnknownBlock.fetch() will convert
                else:
                    results[hash] = UnknownBlock(hash=hash)  # We don't know its a SB
            if not results[hash]._signatures:
                results[hash]._signatures = Signatures([])
            results[hash]._signatures.append(s)
        return [ results[hash] for hash in results]

    def latest(self):
        dated = self._dated()
        latest = max(key for key in dated)      # Find date of SB with latest first sig
        return dated[latest]
