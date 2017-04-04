# encoding: utf-8
from CommonBlock import Transportable

class Block(Transportable):
    """
    Encapsulates an opaque block
    _data holds the data to store, note it might be a property that returns that value.
    """
    table = "b"

    def __repr__(self):
        #Exception UnicodeDecodeError if data binary
        return "%s('%s')" % (self.__class__.__name__, self._data)

    def size(self, verbose=False, **options):   #TODO-REFACTOR-SIZE replace all size with @property
        return len(self._data)

    def content(self):
        return self._data

