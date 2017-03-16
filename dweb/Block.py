# encoding: utf-8
from CommonBlock import Transportable

class Block(Transportable):
    """
    Encapsulates an opaque block
    _data holds the data to store, note it might be a property that returns that value.
    """
    OBStable = "b"  #TODO-REFACTOR-TABLE is it needed ?

    def __repr__(self):
        #Exception UnicodeDecodeError if data binary
        return "%s('%s')" % (self.__class__.__name__, self._data)

    def size(self, verbose=False, **options):   #TODO-REFACTOR-SIZE replace all size with @property
        return len(self._data)


    def url(self, **options):
        # TODO-REFACTOR-URL need to scan and update this function
        """
        Get the body of a URL based on the transport just used.
        :return:
        """
        return self.transport.url(self, **options)
