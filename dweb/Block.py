# encoding: utf-8

class Block(object):
    """
    Encapsulates an opaque block
    _data holds the data to store, note it might be a property that returns that value.
    """
    transport = None

    def __init__(self, data=None):
        self._data = data

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self._data)

    def size(self, verbose=False, **options):
        return len(self._data)

    @classmethod
    def setup(cls, transportclass=None, **transportoptions):
        """
        Setup the Block class with a particular transport

        :param transportclass: Subclass of Transport
        :param transportoptions: Dictionary of options
        """
        cls.transport = transportclass.setup(**transportoptions)

    def store(self, verbose=False, **options):
        """
        Store this block on the underlying transport, return the hash for future id

        :param data: Opaque data to store
        :return: hash of data
        """
        if verbose: print "Storing len=",len(self._data)
        hash = self.transport.store(self._data)
        if verbose: print "Block.store: Hash=",hash
        return hash

    @classmethod
    def block(cls, hash, verbose=False, **options):
        """
        Locate and return a block, based on its multihash
        Exceptions: TransportBlockNotFound if invalid hash

        :param hash: Multihash
        :return: Block
        """
        if verbose: print "Fetching block hash=",hash
        data = cls.transport.block(hash=hash)
        if verbose: print "Block returning data len=",len(data)
        return Block(data=data)


