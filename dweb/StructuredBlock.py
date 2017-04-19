# encoding: utf-8
from json import loads
from Block import Block
from CryptoLib import CryptoLib
from CommonBlock import Transportable, SmartDict
from Dweb import Dweb


class StructuredBlock(SmartDict):
    """
    Encapsulates an JSON Dict and stores / retrieves over transports.
    Note that data is data contained *in* the SB, while _data is data representation *of* the SB.
    Similarly hash is a pointer to data contained *in* the SB, while _hash is the the hash of the data representing the SB.

    Certain sets of data fields have meaning in different applications
    { data: str; hash: multihash; links [ StructuredBlock* ] } refer to content
    _signatures are used for signing in subclasses of CommonList (e.g. MutableBlock, ACL)


    """

    # Uses SmartDict._data and SmartDict._data.setter from superclass
    # SmartDict.__init__(hash=None, data=None) used, it will call @_data.setter here
    table = "sb"

    #---------------------------------------------------------------------------------------------------------
    #METHODS THAT EXTEND OR REPLACE THOSE ON SMARTDICT or TRANSPORTABLE
    #Files have either hash or data or links field set,
    #---------------------------------------------------------------------------------------------------------

    def __init__(self, data=None, hash=None, verbose=False, **options):
        from SignedBlock import Signatures
        if verbose: print "StructuredBlock.__init__",hash, data[0:50] if data else "None", options
        super(StructuredBlock, self).__init__(data=data, hash=hash, verbose=verbose, **options)
        self._signatures = Signatures([])

    def store(self, verbose=False, **options):
        """
        Store content if not already stored (note it must have been stored prior to signing)
        Store any signatures in the Transport layer
        """
        if not self._hash:
            super(StructuredBlock, self).store(verbose=verbose, **options)    # Sets self._hash   #TODO-EFFICIENCY DONT STORE IF NOT CHANGED
        for s in self._signatures:
            ss = s.copy()
            Dweb.transport.add(hash=self._hash, date = ss.date,
                                     signature = ss.signature, signedby = ss.signedby, verbose=verbose, **options)
        return self # For chaining

    @property
    def links(self):
        return self.__dict__.get("links")

    @links.setter
    def links(self, value):
        """
        Convert returned list to array of StructuredBlocks

        :param value:  [ link as dict or StructuredBlock
        :return:
        """
        self.__dict__["links"] = [l if isinstance(l, StructuredBlock) else StructuredBlock(l) for l in value ]

    def dirty(self):
        super(StructuredBlock, self).dirty()
        from SignedBlock import Signatures
        self._signatures = Signatures([]) # Cant be signed if changed from stored version

    #---------------------------------------------------------------------------------------------------------
    #METHODS TO DEAL WITH FILES, WHICH ARE STRUCTURED BLOCKS BUT DONT HAVE OWN TYPE AS INCLUDED BY OTHER THINGS
    #Files have either hash or data or links field set,
    #---------------------------------------------------------------------------------------------------------

    def link(self, item):
        """
        Find a link of a SB either by integer or by name

        :param item: int or string
        :return:
        """
        if isinstance(item, int):
            return self.links[item]
        else:
            for sl in self.links:
                if sl.name == item:
                    return sl
        return None

    def content(self, verbose=False, **options):
        """
        Return the content of the SB.
        Note that this has to use the hash or data fields to get the content held, rather than _hash or _data which represents the SB itself.
        :return: content of block, fetching links (possibly recursively) if required
        """
        self.fetch()
        return (
            self.data or
            (self.hash and Dweb.transport.rawfetch(hash = self.hash, verbose=verbose, **options)) or # Hash must point to raw data, not another SB
            (self.links and "".join(l.content(verbose=verbose, **options) for l in self.links)) or # Each link is a SB
            "")

    def file(self, contenttype=None, verbose=False, **options):
        """
        Return content as a dict, with any meta-data for HTTP to return

        :param contenttype:
        :param verbose:
        :param options:
        :return:
        """
        if verbose: print "StructuredBlock.file: contenttype=",contenttype,"options=",options,self
        self.fetch(verbose=verbose, **options)
        return {
            "Content-type": contenttype or self.__dict__.get("Content-type", None) or "application/octet-stream",
            "data": self.content(verbose=verbose, **options)
        }



    def size(self, verbose=False, **options):
        """
        Return the length of the content of the SB.
        Note that this has to use the hash or data fields to get the content held, rather than _hash or _data which represents the SB itself.

        :return: Size of content, or None if cant calculate
        """
        if verbose: print "SB.size: size=", self.__dict__.get("size",None), "data=", self.data, "hash=", self.hash, "links=", self.links
        return (
            self.__dict__.get("size",None) or
            (self.data and len(self.data)) or
            (self.hash and len(Dweb.transport.rawfetch(hash = self.hash, verbose=verbose, **options))) or
            (self.links and sum(l.size(verbose=verbose, **options) for l in self.links)) or # Each link is a SB
            None)

    def path(self, urlargs, verbose=False, **optionsignored):
        """
        Walk a path and return the SB at the end of that path

        :param urlargs:
        :return:    Found path or None
        """
        self.fetch(verbose=verbose)
        sb = self
        while urlargs:
            sb = sb.link(urlargs.pop(0))
        return sb


    #---------------------------------------------------------------------------------------------------------
    #METHODS TO DEAL WITH SIGNATURES, STORED IN _signatures field
    #Files have either hash or data or links field set,
    #---------------------------------------------------------------------------------------------------------

    def sign(self, commonlist, verbose=False, **options):
        """
        Add a signature to a StructuredBlock
        Note if the SB has a _acl field it will be encrypted first, then the hash of the encrypted block used for signing.

        :param CommonList commonlist:   List its going on - has a ACL with a private key
        :return: self
        """
        from SignedBlock import Signature
        if not self._hash:
            self.store()  # Sets _hash which is needed for signatures #TODO-EFFICIENCY only store if not stored
        self._signatures.append(Signature.sign(commonlist=commonlist, hash=self._hash, verbose=verbose))
        return self  # For chaining

    def verify(self, verbose=False, verify_atleastone=False, **options):
        """
        Verify the signatures on a block (if any)

        :param verbose: True for debugging output
        :param verify_atleastone: True if should fail if no signatures
        :param options: unused
        :return: True if all signatures present match
        """
        if verbose: print "StructuredBlock.verify", self
        if verify_atleastone and not len(self._signatures):
            return False
        return self._signatures.verify(hash=self._hash)

    #---------------------------------------------------------------------------------------------------------
    #METHODS TO DEAL WITH ENCRYPTION, STORED IN _acl field
    #Files have either hash or data or links field set,
    #---------------------------------------------------------------------------------------------------------

    #Javascript has _date, earliestdate() & compare() to support dating based on signatures.