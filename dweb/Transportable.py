# encoding: utf-8
from Errors import AssertionFail
from Dweb import Dweb
#TODO-BACKPORT - review this file

class Transportable(object):
    """
    Encapsulate any kind of object that can be transported

    Any subclass needs to implement:
     _data getter and setter to return the data and to load from opaque bytes returned by transport. (Note SmartDict does this)
     __init__(data=None, url=None, ...) That can be called after raw data retrieved (default calls getter/setter for _data

    Fields
    _url   URL of data stored
    _data   Data (if its opaque)
    _needsfetch True if need to fetch from Dweb
    """

    def __init__(self, data=None, **ignoredoptions):    #TODO-BACKPORT check callers
        """
        Create a new Transportable element - storing its data and url if known.
        Subclassed to initialize from that information

        :param data: Any opaque bytes to store
        :param url: Hash of those opaque bytes
        """
        self._data = data   # Note will often call the @_data.setter function   #TODO-BACKPORT check

    def transport():
        """
        Find transport for this object,
        if not yet stored this._url will be undefined and will return default transport

        returns: instance of subclass of Transport
        """
        return Dweb.transport(this._url);

    def _setdata(self, value):
        self._data = value  # Default behavior, assumes opaque bytes, and not a dict - note subclassed in SmartDict

    def _getdata(self):
        return self._data;  # Default behavior - opaque bytes

    _data = property(_getdata, _setdata)

    def store(self, data=None, verbose=False, **options):
        """
        Store this block on the underlying transport, return the url for future id.
        Note this calls _data which is typically a getter/setter that returns subclass specific results.
        Exception: UnicodeDecodeError - if data is binary

        :return: url of data
        """
        if verbose: print "Storing", self.__class__.__name__, "len=", len(data or self._data)
        #TODO-BACKPORT figure out best way to get default Transport for storing
        self._url = self.transport().rawstore(data=data or self._data, verbose=verbose)  # Note uses fact that _data will be subclassed
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
            self._data = self.transport().rawfetch(url=self._url, verbose=verbose, **options)
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
            raise AssertionFail(message=self.__class__.__name__+" doesnt support xurl()")
        return self.transport().xurl(self, url_output=url_output, table=table, **options) #TODO-BACKPORT default transport for this?
