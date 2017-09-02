# encoding: utf-8
import dateutil.parser  # pip py-dateutil
import base64
from misc import ObsoleteException, _print, ToBeImplementedException, AssertionFail
from Dweb import Dweb
#TODO-BACKPORT - review this file

class Transportable(object):
    """
    Encapsulate any kind of object that can be transported

    Any subclass needs to implement:
     _data getter and setter to return the data and to load from opaque bytes returned by transport. (Note SmartDict does this)
     __init__(data=None, url=None, ...) That can be called after raw data retrieved (default calls getter/setter for _data

    Fields:
    _data   Usually a virtual property (see getter and setter) that stores data to dictionary etc
    _url   Hash of block holding the data
    _fetched    True if has been fetched from url
    _dirty      True if needs writing to dWeb
    """

    def __init__(self, data=None, url=None, verbose=False, **ignoredoptions):
        """
        Create a new Transportable element - storing its data and url if known.
        Subclassed to initialize from that information

        :param data: Any opaque bytes to store
        :param url: Hash of those opaque bytes
        """
        self._data = data   # Note will often call the @_data.setter function
        self._url = url
        if url and not data: self._needsfetch = True
        #TODO-VERIFY - can verify at this point


    def store(self, data=None, verbose=False, **options):
        """
        Store this block on the underlying transport, return the url for future id.
        Note this calls _data which is typically a getter/setter that returns subclass specific results.
        Exception: UnicodeDecodeError - if data is binary

        :return: url of data
        """
        if verbose: print "Storing", self.__class__.__name__, "len=", len(data or self._data)
        self._url = Dweb.transport.rawstore(data=data or self._data, verbose=verbose)  # Note uses fact that _data will be subclassed
        if verbose: print self.__class__.__name__, ".stored: url=", self._url
        return self

    def dirty(self):
        """
        Flag an object as dirty, i.e. needing writing back to dWeb.
        Subclasses should handle this to clear for example _signatures

        """
        self._url = None

    def fetch(self, verbose=False, **options):
        """
        Retrieve the data of an object from the url
        Usage typically XyzBlock(url=A1B2).fetch()

        :return:
        """
        if verbose: print "Transportable.fetch _url=",self._url
        if self._needsfetch:
            self._data = Dweb.transport.rawfetch(url=self._url, verbose=verbose, **options)
            self._needsfetch = False
        return self # For Chaining

    def file(self, verbose=False, contenttype=None, **options):
        return { "Content-type": contenttype or "application/octet-stream",
            "data": self._data }

    def xurl(self, url_output=None, table=None, **options): #TODO-BACKPORT rename
        """
        Get the body of a URL based on the transport just used.
        Subclasses must define table if want to support URL's
        And retrieval depends on that table being in ServerHTTP.LetterToClass

        :param str url_output: "URL"/default for URL, "getpost" for getpost parms
        :return:    URL or other representation of this object
        """
        table = table or self.table
        if not table:
            raise AssertionFail(message=self.__class__.__name__+" doesnt support url()")
        return Dweb.transport.url(self, url_output=url_output, table=table, **options)


class SmartDict(Transportable):
    """
    The SmartDict class allows for merging of the functionality of a Dict and an object,
    allowing setting from a dictionary and access to elements by name.

     _acl If set (on master) defines storage as encrypted
    """
    def __init__(self, data=None, url=None, verbose=False, **options):
        """

        :param url: Object to fetch data from
        :param data: Used via _data's setter function to initialize object
        :param options: Set fields of SmartDict AFTER initialized from data
        """
        super(SmartDict, self).__init__(data=data, url=url) # Uses _data.setter to set data
        for k in options:
            self.__setattr__(k, options[k])

    def __getattr__(self, name):
        return self.__dict__.get(name)

    # Allow access to arbitrary attributes, allows chaining e.g. xx.data.len
    def __setattr__(self, name, value):
        # THis code was running self.dirty() - problem is that it clears url during loading from the dWeb
        if name[0] != "_":
            if "date" in name and isinstance(value,basestring):
                value = dateutil.parser.parse(value)
        return super(SmartDict, self).__setattr__(name, value)  # Calls any property esp _data

    def _setproperties(self, value):
        for k in value:
            self.__setattr__(k, value[k])

    def __str__(self):
        return self.__class__.__name__+"("+str(self.__dict__)+")"

    def __repr__(self):
        return repr(self.__dict__)

    def preflight(self, dd):
        """
        Run before converting to data, by default strips any attributes starting with "_", and turns objects into urles
        :return:
        """
        res = {
            k: dd[k].store()._url if isinstance(dd[k], Transportable) else dd[k]
            for k in dd
            if k[0] != '_'
        }
        res["table"] = res.get("table",self.table)  # Assumes if used table as a field, that not relying on it being the table for loading
        assert res["table"]
        return res

    def _getdata(self):
        """
        By default SmartDict subclasses are stored as JSON (CryptoLib.dumps) of the __dict__

        Exception: UnicodeDecodeError - if its binary

        :return: canonical json string that handles dates, and order in dictionaries
        """
        from CryptoLib import CryptoLib
        try:
            res = CryptoLib.dumps(self.preflight(self.__dict__.copy())) # Should call self.dumps below { k:self.__dict__[k] for k in self.__dict__ if k[0]!="_" })
        except UnicodeDecodeError as e:
            print "Unicode error in StructuredBlock"
            print self.__dict__
            raise e
        if self._acl:   # Need to encrypt
            encdata = self._acl.encrypt(res, b64=True)
            dic = {"encrypted": encdata, "acl": self._acl._publicurl, "table": self.table}
            res = CryptoLib.dumps(dic)
        return res

    def _setdata(self, value):
        """
        Set the data from a dictionary
        Note separated from @_data.setter to make subclassing easier
        COPIED TO PYTHON 2017-5-27
        
        :param value: JSON string or dictionary
        """

        from CryptoLib import CryptoLib
        if value:  # Just skip if no initialization
            if not isinstance(value, dict):
                # Its data - should be JSON
                value = CryptoLib.loads(value)  # Will throw exception if it isn't JSON
            if "encrypted" in value:
                value = CryptoLib.loads(CryptoLib.decryptdata(value))    # Decrypt, null operation if not encrypted
            self._setproperties(value)

    _data = property(_getdata, _setdata)


    def dumps(self):    # Called by json_default, but preflight() is used in most scenarios rather than this
        return {k: self.__dict__[k] for k in self.__dict__ if k[0] != "_"}  # Serialize the dict, excluding _xyz

    def copy(self):
        return self.__class__(self.__dict__.copy())


class UnknownBlock(SmartDict):
    """
    A class for when we don't know if its a StructuredBlock, or MutableBlock or something else
    """
    def __init__(self, data=None, url=None, verbose=False, **options):
        """

        :param url: Object to fetch data from
        :param data: Used via _data's setter function to initialize object
        :param options: Set fields of SmartDict AFTER initialized from data
        """
        if options:
            raise ToBeImplementedException(name="UnknownBlock.__init__ with options") # Normally don't pass options as dont know obj to set
        if data:
            raise ToBeImplementedException(name="UnknownBlock.__init__ with data")  # Normally don't pass data as dont know type of obj to set - if have data, then use to determine type
        super(UnknownBlock, self).__init__(url=url, verbose=verbose) # Uses _data.setter to set data

    def fetch(self, verbose=False, **options):
        """
        Retrieve the data of an object from the url
        Usage typically foo = UnknownBlock(url=A1B2).fetch()

        :return:
        """
        from ServerHTTP import LetterToClass
        from CryptoLib import CryptoLib
        if verbose: print "Transportable.fetch _url=", self._url
        data = Dweb.transport.rawfetch(url=self._url, verbose=verbose, **options)
        dic = CryptoLib.loads(data)
        table = dic["table"]
        if not table:
            raise ToBeImplementedException(name="Table field stored in "+self._url)
        cls = LetterToClass.get(table, None)
        if not cls:
            raise ToBeImplementedException(name="LetterToClass for "+table)
        newobj = cls(url=self._url, data=dic)
        return newobj  # For caller to store
