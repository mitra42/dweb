# encoding: utf-8
import dateutil.parser  # pip py-dateutil
from misc import ObsoleteException

class Transportable(object):
    """
    Encapsulate any kind of object that can be transported

    Any subclass needs to implement:
     _data getter and setter to return the data and to load from opaque bytes returned by transport. (Note SmartDict does this)
     __init__(data=None, hash=None, ...) That can be called after raw data retrieved (default calls getter/setter for _data

    """
    transport = None

    def __init__(self, data=None, hash=None, verbose=False, **ignoredoptions):
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
        if verbose: print "Storing", self.__class__.__name__, "len=", len(data or self._data)
        self._hash = self.transport.rawstore(data=data or self._data)  # Note uses fact that _data will be subclassed
        if verbose: print self.__class__.__name__, ".stored: hash=", self._hash
        return self._hash   #TODO-REFACTOR-STORE change all "store" to return obj, as can access hash via ._hash

    def fetch(self, verbose=False, **options):
        """
        Retrieve the data of an object from the hash
        Usage typically XyzBlock(hash=A1B2).fetch()

        :return:
        """
        self._data = self.transport.rawfetch(hash=self._hash, verbose=verbose, **options)
        return self # For Chaining

    def file(self, verbose=False, contenttype=None, **options):
        return { "Content-type": contenttype or "application/octet-stream",
            "data": self._data }

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
        return self.__class__.__name__+"("+str(self.__dict__)+")"

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
        from CryptoLib import CryptoLib
        try:
            return CryptoLib.dumps(self) # Should call self.dumps below { k:self.__dict__[k] for k in self.__dict__ if k[0]!="_" })
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
        return {k: self.__dict__[k] for k in self.__dict__ if k[0] != "_"}  # Serialize the dict, excluding _xyz

    def copy(self):
        return self.__class__(self.__dict__.copy())

