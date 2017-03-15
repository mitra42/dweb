# encoding: utf-8


class Block(object):
    """
    Encapsulates an opaque block
    _data holds the data to store, note it might be a property that returns that value.
    """
    transport = None
    table = "b"
    transportcommand="block"

    def __init__(self, hash=None, data=None, verbose=False):
        #TODO-BLOCK check calls to __init__ and make sure use dic for hash
        #TODO-BLOCK make block use _hash rather than hash passed
        self._hash = hash
        self._data = data

    def __repr__(self):
        #Exception UnicodeDecodeError if data binary
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

    def store(self, table=None, verbose=False, **options):
        # type: (object, str, bool) -> str
        """
        Store this block on the underlying transport, return the hash for future id
        Uses the table of the class, which might be oerridden in superclass
        Exception: UnicodeDecodeError - if data is binary

        :param table: table to store in
        :return: hash of data
        """
        if verbose: print "Storing len=", len(self._data)
        self._hash = self.transport.store(table=table or self.table, data=self._data)
        if verbose: print "Block.store: Table=", table or self.table, "Hash=", self._hash
        return self._hash

    @classmethod
    def block(cls, hash, table=None, verbose=False, **options):
        """
        Locate and return a block, based on its multihash.
        Exceptions: TransportBlockNotFound if invalid hash.
        Copied to dweb.js.

        :rtype: Block
        :param hash: Multihash
        :return: Block
        """
        if verbose: print "Fetching block table=", table or cls.table, "hash=", hash
        data = cls.transport.block(table=table or cls.table, hash=hash)
        if verbose: print "Block returning data len=", len(data)
        return Block(data=data)

    def url(self, **options):
        """
        Get the body of a URL based on the transport just used.
        :return:
        """
        return self.transport.url(self, **options)
