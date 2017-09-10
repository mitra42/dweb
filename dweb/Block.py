# encoding: utf-8

from Transportable import Transportable

class Block(Transportable):
    """
    Encapsulates an opaque block
    _data holds the data to store, note it might be a property that returns that value.
    """
    table = "b"

    def __repr__(self):
        #Exception UnicodeDecodeError if data binary
        return "%s('%s')" % (self.__class__.__name__, self._data)

    def size(self, verbose=False, **options):
        return len(self._getdata())

    def content(self):
        return self._getdata()

    @classmethod
    def fetch(cls, url, verbose):
        data = super(Block, cls).fetch(url, verbose)
        blk = cls(data=data)
        return blk
