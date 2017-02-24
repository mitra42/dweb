# encoding: utf-8
import dateutil.parser  # pip py-dateutil
from json import loads
from Block import Block
from CryptoLib import CryptoLib

class SmartDict(object):
    """
    The SmartDict class allows for merging of the functionality of a Dict and an object,
    allowing setting from a dictionary and access to elements by name.
    """
    #TODO Signature should be SmartDict
    def __getattr__(self, name):
        return self.__dict__.get(name)

    # Allow access to arbitrary attributes, allows chaining e.g. xx.data.len
    def __setattr__(self, name, value):
        if "date" in name and isinstance(value,basestring):
            value = dateutil.parser.parse(value)
        #return super(SmartDict, self).__setattr__(name, value)  << For some reason not working with multiple inheritance
        self.__dict__[name] = value

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)

    def __init__(self, data=None):
        """
        Create a new StructuredBlock

        :param data: Can be a dict, or a json string
        """
        if data:  # Just skip if no initialization
            if not isinstance(data, dict):
                # Its data - should be JSON
                data = loads(data)  # Will throw exception if it isn't JSON
            for k in data:
                self.__setattr__(k, data[k])

class StructuredLink(SmartDict):
    """
    A link inside the links field of a StructuredBlock

    { date: datetime, size: int, [ data: string | hash: multihash | links: [ link ]* }
    """

    def content(self, verbose=False, **options):
        """
        :return: content of block, fetching links (possibly recursively) if required
        """
        return (
            self.data or
            (self.hash and Block.block(self.hash, verbose=verbose, **options)._data) or
            (self.links and "".join(d.content(verbose=verbose, **options) for d in self.links)) or
            "")


class StructuredBlock(Block, SmartDict):
    """
    Encapsulates an JSON Dict and stores / retrieves over transports
    """

    @property
    def _data(self):
        """
        Override _data property of Block,

        :return: canonical json string that handles dates, and order in dictionaries
        """
        #TODO need to check that this doesnt have internal e.g. _* fields that might get stored, if so strip
        return CryptoLib.dumps(self.__dict__)

    def __init__(self, data=None):
        """
        Create a new StructuredBlock

        :param data: Can be a dict, or a json string
        """
        SmartDict.__init__(self, data)   # Cant use "super" as would use Block instead of SmartDic

    def store(self, verbose=False, **options):
        """
        Store this block on the underlying transport, return the hash for future id

        :return: hash of data
        """
        #store accesses the data via _data above
        hash = super(StructuredBlock, self).store(**options)
        if verbose: print "Structured Block.store: Hash=",hash
        return hash

    @classmethod
    def block(cls, hash, verbose=False, **options):
        """
        Locate and return a block, based on its multihash

        :param hash: Multihash
        :return: Block
        """
        if verbose: print "Fetching Superblock hash=",hash
        sb = super(StructuredBlock, cls).block(hash)     # Will create a SB and initialze
        if verbose: print "Block returning", str(sb)
        return sb


    #---------------------------------------------------------------------------------------------------------
    #METHODS TO DEAL WITH FILES, WHICH ARE STRUCTURED BLOCKS BUT DONT HAVE OWN TYPE AS INCLUDED BY OTHER THINGS
    #---------------------------------------------------------------------------------------------------------

    def content(self, verbose=False, **options):
        """
        :return: content of block, fetching links (possibly recursively) if required
        """
        return (
            self.data or
            (self.hash and Block.block(self.hash, verbose=verbose, **options)._data) or
            (self.links and "".join(d.content(verbose=verbose, **options) for d in self.links)) or
            "")





    #TODO - allow storing data | ref | list on creation
