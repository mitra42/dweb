# encoding: utf-8
from Errors import AssertionFail
from Dweb import Dweb

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

    def __init__(self, data=None, **ignoredoptions):
        """
        Create a new Transportable element - storing its data and url if known.
        Subclassed to initialize from that information

        :param data: Any opaque bytes to store
        :param url: Hash of those opaque bytes
        """
        self._setdata(data)   # Note will often call the @_data.setter function
        self._url = None

    def transport(self):
        """
        Find transport for this object,
        if not yet stored this._url will be undefined and will return default transport

        returns: instance of subclass of Transport
        """
        return Dweb.transport(self._url);

    def _setdata(self, value):
        self._data = value  # Default behavior, assumes opaque bytes, and not a dict - note subclassed in SmartDict

    def _getdata(self):
        return self._data;  # Default behavior - opaque bytes

    def store(self, verbose=False):
        """
        Store this block on the underlying transport, return the url for future id.
        Note this calls _data which is typically a getter/setter that returns subclass specific results.
        Exception: UnicodeDecodeError - if data is binary

        :return: url of data
        """
        if verbose: print "Storing", self.__class__.__name__
        if self._url:           # If already stored
            return self._url        # Return url
        data = self._getdata()      # Note assumes _getdata() will be sublassed to construct outgoing data
        if (verbose): print "Transportable.store data=", data
        self._url = self.transport().rawstore(data=data, verbose=verbose)
        if verbose: print self.__class__.__name__, ".stored: url=", self._url
        return self

    def dirty(self):
        """
        Mark an object as needing storing again, for example because one of its fields changed.
        Flag as dirty so needs uploading - subclasses may delete other, now invalid, info like signatures
        """
        self._url = None

    @classmethod
    def fetch(cls, url=None, verbose=False):
        """
        Fetch the data for a url, subclasses act on the data, typically storing it and returns data not self

        :param url:	string of url to retrieve
        :return:	string - arbitrary bytes retrieved.
        """
        if verbose: print "Transportable.fetch _url=",url
        return Dweb.transport(url).rawfetch(url=url, verbose=verbose)

    def file(self, verbose=False, contenttype=None, **options): #TODO-API
        return { "Content-type": contenttype or "application/octet-stream",
            "data": self._getdata() }

    def xurl(self, url_output=None, table=None, **options): #TODO-BACKPORT rename - maybe don't need
        """
        Get the body of a URL based on the transport just used.
        Subclasses must define table if want to support URL's
        And retrieval depends on that table being in Dweb.LetterToClass

        :param str url_output: "URL"/default for URL, "getpost" for getpost parms
        :return:    URL or other representation of this object
        """
        table = table or self.table
        if not table:
            raise AssertionFail(message=self.__class__.__name__+" doesnt support xurl()")
        return self.transport().xurl(self, url_output=url_output, table=table, **options) #TODO-BACKPORT default transport for this?
