# encoding: utf-8
from json import loads
from Block import Block
from CryptoLib import CryptoLib
from CommonBlock import Transportable, SmartDict

class StructuredBlock(SmartDict):
    """
    Encapsulates an JSON Dict and stores / retrieves over transports.
    Note that data is data contained *in* the SB, while _data is data representation *of* the SB.
    Similarly hash is a pointer to data contained *in* the SB, while _hash is the the hash of the data representing the SB.
    """

    # Uses SmartDict._data and SmartDict._data.setter from superclass
    # SmartDict.__init__(hash=None, data=None) used, it will call @_data.setter here
    _table = "sb"

    def fetch(self, verbose=False, **options):
        return self # No action needed on a SB (block loads it)

    def url(self, **options):
        """
        Get the body of a URL based on the transport just used.
        :return:
        """
        return self.transport.url(self, **options)

    def _setdata(self, value):
        super(StructuredBlock,self)._setdata(value) # Set _data and attributes from dictionary in data
        if self.links:
            self.links = [l if isinstance(l, StructuredBlock) else StructuredBlock(l) for l in self.links ]

    _data = property(SmartDict._getdata, _setdata)

    def store(self, verbose=False, **options):
        """
        Store this block on the underlying transport, return the hash for future id
        Exception: UnicodeDecodeError if data is binary

        :return: hash of data
        """
        self._hash = Transportable.transport.store(data=self, verbose=verbose, **options)   # Uses self._data to get data
        if verbose: print "Structured Block.stored: Hash=",self._hash
        return self._hash   #TODO-REFACTOR-STORE

    #---------------------------------------------------------------------------------------------------------
    #METHODS TO DEAL WITH FILES, WHICH ARE STRUCTURED BLOCKS BUT DONT HAVE OWN TYPE AS INCLUDED BY OTHER THINGS
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
        return (
            self.data or
            (self.hash and Transportable.transport.block(hash = self.hash, verbose=verbose, **options)) or # Hash must point to raw data, not another SB
            (self.links and "".join(l.content(verbose=verbose, **options) for l in self.links)) or # Each link is a SB
            "")


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
            (self.hash and len(Transportable.transport.block(hash = self.hash, verbose=verbose, **options))) or
            (self.links and sum(l.size(verbose=verbose, **options) for l in self.links)) or # Each link is a SB
            None)

    def path(self, urlargs, verbose=False):
        """
        Walk a path and return the SB at the end of that path

        :param urlargs:
        :return:
        """
        sb = self
        while urlargs:
            sb = sb.link(urlargs.pop(0))
        return sb




    #TODO - allow storing data | ref | list on creation
