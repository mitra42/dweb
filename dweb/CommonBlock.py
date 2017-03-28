# encoding: utf-8
import dateutil.parser  # pip py-dateutil
import base64
from misc import ObsoleteException, _print

class Transportable(object):
    """
    Encapsulate any kind of object that can be transported

    Any subclass needs to implement:
     _data getter and setter to return the data and to load from opaque bytes returned by transport. (Note SmartDict does this)
     __init__(data=None, hash=None, ...) That can be called after raw data retrieved (default calls getter/setter for _data

    Fields:
    _data   Usually a virtual property (see getter and setter) that stores data to dictionary etc
    _hash   Hash of block holding the data
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
        Store this block on the underlying transport, return the hash for future id.
        Note this calls _data which is typically a getter/setter that returns subclass specific results.
        Exception: UnicodeDecodeError - if data is binary

        :return: hash of data
        """
        if verbose: print "Storing", self.__class__.__name__, "len=", len(data or self._data)
        print "XXX@51",data, self._data,
        self._hash = self.transport.rawstore(data=data or self._data)  # Note uses fact that _data will be subclassed
        if verbose: print self.__class__.__name__, ".stored: hash=", self._hash
        return self

    def dirty(self):
        """
        Flag an object as dirty, i.e. needing writing back to dWeb.
        Subclasses should handle this to clear for example _signatures

        """
        self._hash = None

    def fetch(self, verbose=False, **options):
        """
        Retrieve the data of an object from the hash
        Usage typically XyzBlock(hash=A1B2).fetch()

        :return:
        """
        if verbose: print "Transportable.file _hash=",self._hash, "len data=",len(self._data) if self._data else 0
        if self._hash and ((not self._data) or (len(self._data) <= 2)): # See if its dirty, Empty data is '{}'
            self._data = self.transport.rawfetch(hash=self._hash, verbose=verbose, **options)
        return self # For Chaining

    def file(self, verbose=False, contenttype=None, **options):
        return { "Content-type": contenttype or "application/octet-stream",
            "data": self._data }

    def url(self, url_output=None, table=None, **options):
        """
        Get the body of a URL based on the transport just used.
        Subclasses must define _table if want to support URL's
        And retrieval depends on that _table being in ServerHTTP.LetterToClass

        :param str url_output: "URL"/default for URL, "getpost" for getpost parms
        :return:    URL or other representation of this object
        """
        table = table or self._table
        if not table:
            raise AssertionFail(message=self.__class__.__name__+" doesnt support url()")
        return self.transport.url(self, url_output=url_output, table=table, **options)


class SmartDict(Transportable):
    """
    The SmartDict class allows for merging of the functionality of a Dict and an object,
    allowing setting from a dictionary and access to elements by name.

     _acl If set (on master) defines storage as encrypted
    """
    def __getattr__(self, name):
        return self.__dict__.get(name)

    # Allow access to arbitrary attributes, allows chaining e.g. xx.data.len
    def __setattr__(self, name, value):
        # THis code was running self.dirty() - problem is that it clears hash during loading from the dWeb
        if name[0] != "_":
            if "date" in name and isinstance(value,basestring):
                value = dateutil.parser.parse(value)
        return super(SmartDict, self).__setattr__(name, value)  # Calls any property esp _data

    def __str__(self):
        return self.__class__.__name__+"("+str(self.__dict__)+")"

    def __repr__(self):
        return repr(self.__dict__)

    def __init__(self, data=None, hash=None, verbose=False, **options):
        """

        :param hash: Object to fetch data from
        :param data: Used via _data's setter function to initialize object
        :param options: Set fields of SmartDict AFTER initialized from data
        """
        super(SmartDict, self).__init__(data=data, hash=hash) # Uses _data.setter to set data
        for k in options:
            self.__setattr__(k, options[k])

    def preflight(self, dd=None):
        """
        Run before converting to data, by default does nothing, typically subclassed to turn objects into hashes
        :return:
        """
        if not dd:
            dd = self.__dict__  # Note this isnt a copy, so cant make changes below
        return {
            k: dd[k].store()._hash if isinstance(dd[k], Transportable) else dd[k]
            for k in dd
            if k[0] != '_'
        }

    def _getdata(self):
        """
        By default SmartDict subclasses are stored as JSON (CryptoLib.dumps) of the __dict__

        Exception: UnicodeDecodeError - if its binary

        :return: canonical json string that handles dates, and order in dictionaries
        """
        from CryptoLib import CryptoLib
        print "XXX@152", self
        try:
            res = CryptoLib.dumps(self.preflight()) # Should call self.dumps below { k:self.__dict__[k] for k in self.__dict__ if k[0]!="_" })
        except UnicodeDecodeError as e:
            print "Unicode error in StructuredBlock"
            print self.__dict__
            raise e
        if self._acl:   # Need to encrypt
            encdata = CryptoLib.sym_encrypt(res, base64.urlsafe_b64decode(self._acl.accesskey), b64=True)
            dic = {"encrypted": encdata, "acl": self._acl._publichash}
            res = CryptoLib.dumps(dic)
        return res

    def _setdata(self, value):
        # Note separarated from @_data.setter to make subclassing easier
        from CryptoLib import CryptoLib
        if value:  # Just skip if no initialization
            if not isinstance(value, dict):
                # Its data - should be JSON
                value = CryptoLib.loads(value)  # Will throw exception if it isn't JSON
            if value.get("encrypted"):
                from MutableBlock import AccessControlList
                acl = AccessControlList(hash=value.get("acl"), verbose=self.verbose)    #TODO-AUTHENTICATION probably add person-to-person version
                dec = acl.decrypt(data = value.get("encrypted"))
                value = CryptoLib.loads(dec)
            for k in value:
                self.__setattr__(k, value[k])

    _data = property(_getdata, _setdata)


    def dumps(self):    # Called by json_default
        return {k: self.__dict__[k] for k in self.__dict__ if k[0] != "_"}  # Serialize the dict, excluding _xyz

    def copy(self):
        return self.__class__(self.__dict__.copy())

