# encoding: utf-8

from datetime import datetime
from StructuredBlock import SmartDict
from Dweb import Dweb


"""
A collection of classes that represent objects that are signed, dated, encrypted etc

Signed = { StructuredBlock|Hash, signatures: { date: ISO, signature: hex  publickey: hex }

The date is included in what is signed

Note they are not subclassed off StructuredBlock because they have, rather than are, StructuredBlocks
"""

class Signature(SmartDict):
    """
    The Signature class holds a signed entry that can be added to a CommonList.
    The url of the signed object is stored with the signature in CommonList.add()

    Fields:
    date:       Date stamp (according to browser) when item signed
    url:       URL of object signed
    signature:  Signature of the date and url
    signedby:   Public URL of list signing this (list should have a public key)
    """
    table = "sig"

    def __init__(self, dic, verbose=False):
        super(Signature, self).__init__(dic, verbose)
        #For compatability with JS not parsing into date
        #if isinstance(self.date, basestring):
        #    self.date = dateutil.parser.parse(self.date)

    def signable(self):
        """
        Returns a string suitable for signing and dating, current implementation includes date and storage url of data.

        :return: Signable or comparable string
        """
        return self.date.isoformat() + self.url

    @classmethod
    def sign(cls, commonlist, url, verbose=False):
        """
        Sign and date a url.

        :param commonlist: Subclass of CommonList containing a private key to sign with.
        :param url: of item being signed
        :return: Signature (dated with current time on browser)
        """
        date = datetime.now()
        if not commonlist._publicurl:
            commonlist.store(verbose=verbose)
        assert commonlist._publicurl, "publicurl must be set by now"
        sig = cls({"date": date, "url": url, "signedby": commonlist._publicurl}, verbose)
        sig.signature = commonlist.keypair.sign(sig.signable())
        return sig

    def verify(self, commonlist, verbose=False):
        return commonlist.verify(self, verbose)


    @classmethod
    def filterduplicates(cls, arr):
        """
        Utility function to allow filtering out of duplciates

        :param arr: Array of Signature
        :returns: Array of Signature containing on the first occuring instance of a signature (note first in array, not necessarily first by date)
        """
        res = []
        # Remove duplicate signatures
        for i in arr:
            if sig.url not in [ s.url for s in res]:
                res.append(sig)
        return res

    def fetchdata(self, verbose=False):
        """
        Find the block signed by this signature, usually a Structured Block but not always

        :return:
        """
        self.data = self.data or SmartDict.fetch(self.url, verbose)     # Note SmartDict.fetch changes to appropriate class
