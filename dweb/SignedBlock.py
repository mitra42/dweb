# encoding: utf-8

from datetime import datetime
import dateutil.parser  # pip py-dateutil
from json import loads
from misc import MyBaseException, AssertionFail, _print
from CryptoLib import CryptoLib, KeyPair
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

class SignedBlocks(list):
    """
    A list of StructuredBlocks with signatures
    #TODO - probably replace with a CommonList for the signatures, and then convert to StructuredBlocks list
    """

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
            return SignedBlocks([])    # Its ok to fail as list may be empty
        else:
            if verbose: print "SignedBlocks.fetch found ",len(lines) if lines else None
            results = {}
            for block in lines:
                #TODO - can push this deduplication adn verification into the Signatures class
                s = Signature(block)
                key = s.hash
                if not results.get(key, None):
                    if fetchblocks:
                        results[key] = UnknownBlock(hash=key).fetch()  # Was StructuredBlock, but we don't know its a SB
                    else:
                        results[key] = UnknownBlock(hash=key)  # Was StructuredBlock, but we don't know its a SB
                if CryptoLib.verify(s):
                    if not results[key]._signatures:
                        results[key]._signatures = Signatures([])
                    results[key]._signatures.append(s)

            # Turn it into a list of StructuredBlock - stores the hashes but doesnt fetch the data
            sbs = SignedBlocks([ results[key] for key in results])
        return sbs

    def _dated(self):
        """
        :return: { sb.earliestsignaturedate: sb * }
        """
        return {sb._signatures.earliest(): sb for sb in self}  # Use date of first sig
        #TODO I think this should be by latest as if republish earlier block it gets lost

    def latest(self):
        dated = self._dated()
        latest = max(key for key in dated)      # Find date of SB with latest first sig
        return dated[latest]

    def sorteddeduplicated(self):
        """
        Extract the latest, and return a deduplicated, ordered list
        :return: latest signed block, [ signed blocks in date order excluding latest ]*
        """
        dated = self._dated()
        sorted = dated.keys()
        sorted.sort()       # Earliest first
        return [ dated[date] for date in sorted ]

    def resolvetables(self):
        """
        Takes a list of deduped SignedBlocks, and fetches them to determine their real class

        :return:
        """
