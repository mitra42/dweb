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

    def url(self, url_output=None, **options):
        """
        Get the body of a URL based on the transport just used.

        :url_output str: "URL"/default for URL, "getpost" for getpost parms
        :return:
        """
        return self.transport.url(self, url_output=url_output, **options)

    def _setdata(self, value):
        super(StructuredBlock,self)._setdata(value) # Set _data and attributes from dictionary in data
        if self.links:
            self.links = [l if isinstance(l, StructuredBlock) else StructuredBlock(l) for l in self.links ]

    _data = property(SmartDict._getdata, _setdata)


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
        return (
            self.data or
            (self.hash and Transportable.transport.rawfetch(hash = self.hash, verbose=verbose, **options)) or # Hash must point to raw data, not another SB
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
            (self.hash and len(Transportable.transport.rawfetch(hash = self.hash, verbose=verbose, **options))) or
            (self.links and sum(l.size(verbose=verbose, **options) for l in self.links)) or # Each link is a SB
            None)

    def path(self, urlargs, verbose=False, **optionsignored):
        """
        Walk a path and return the SB at the end of that path

        :param urlargs:
        :return:    Found path or None
        """
        sb = self
        while urlargs:
            sb = sb.link(urlargs.pop(0))
        return sb




    #TODO - allow storing data | ref | list on creation
