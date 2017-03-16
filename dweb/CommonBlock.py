# encoding: utf-8
import dateutil.parser  # pip py-dateutil


class Transportable(object):
    """
    Encapsulate any kind of object that can be transported
    """
    transport = None    #TODO-REFACTOR replace all Block.transport with Transportable.transport, and move setup here

    def __init__(self, data=None, hash=None, verbose=False):
        """
        Create a new Transportable element - storing its data and hash if known.
        Subclassed to initialize from that information

        :param data: Any opaque bytes to store
        :param hash: Hash of those opaque bytes
        """
        self._data = data   # Note will often call the @_data.setter function
        self._hash = hash
        #TODO-VERIFY - can verify at this point

    @classmethod
    def setup(cls, transportclass=None, **transportoptions):
        """
        Setup the Transportable class with a particular transport

        :param transportclass: Subclass of Transport
        :param transportoptions: Dictionary of options
        """
        cls.transport = transportclass.setup(**transportoptions)

    def store(self, data=None, verbose=False, **options):
        """
        Store this block on the underlying transport, return the hash for future id
        Exception: UnicodeDecodeError - if data is binary

        :return: hash of data
        """
        if verbose: print "Storing len=", len(data or self._data)
        self._hash = self.transport.store(data=data or self._data)  # Note uses fact that _data will be subclassed
        if verbose: print self.__class__.__name__, ".stored: hash=", self._hash
        return self._hash   #TODO-REFACTOR change all "store" to return obj, as can access hash via ._hash

    @classmethod
    def block(cls, hash=hash, verbose=False, **options):
        """
        Locate and return data, based on its multihash and creating appropriate object
        Exceptions: TransportBlockNotFound if invalid hash.
        Copied to dweb.js.

        :param hash: Multihash
        :return: new instance of cls
        """
        if verbose: print "Fetching block", "hash=", hash or self._hash
        data = cls.transport.block(hash=hash)
        if verbose: print "Block returning data len=", len(data)
        return cls(data=data, hash=hash)

class SmartDict(Transportable):
    """
    The SmartDict class allows for merging of the functionality of a Dict and an object,
    allowing setting from a dictionary and access to elements by name.
    """
    def __getattr__(self, name):
        return self.__dict__.get(name)

    # Allow access to arbitrary attributes, allows chaining e.g. xx.data.len
    def __setattr__(self, name, value):
        if "date" in name and isinstance(value,basestring):
            value = dateutil.parser.parse(value)
        return super(SmartDict, self).__setattr__(name, value)  # Calls any property esp _data

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)

    def __init__(self, data=None, hash=None, verbose=False, **options):
        super(SmartDict, self).__init__(data=data, hash=hash) # Uses _data.setter to set data
        for k in options:
            self.__setattr__(k, options[k])

    def _getdata(self):
        """
        By default SmartDict subclasses are stored as JSON (CryptoLib.dumps) of the __dict__

        Exception: UnicodeDecodeError - if its binary

        :return: canonical json string that handles dates, and order in dictionaries
        """
        #TODO need to check that this doesnt have internal e.g. _* fields that might get stored, if so strip
        from CryptoLib import CryptoLib
        try:
            return CryptoLib.dumps(self.__dict__)
        except UnicodeDecodeError as e:
            print "Unicode error in StructuredBlock"
            print self.__dict__
            raise e

    def _setdata(self, value):
        # Note separarated from @_data.setter to make subclassing easier
        from CryptoLib import CryptoLib
        if value:  # Just skip if no initialization
            if not isinstance(value, dict):
                # Its data - should be JSON
                value = CryptoLib.loads(value)  # Will throw exception if it isn't JSON
            for k in value:
                self.__setattr__(k, value[k])

    _data = property(_getdata, _setdata)


    def dumps(self):    # Called by json_default
        return self.__dict__    # Can serialize the dict

    def copy(self):
        return self.__class__(self.__dict__.copy())

