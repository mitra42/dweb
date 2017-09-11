# encoding: utf-8
from sys import version as python_version
if python_version.startswith('3'):
    from urllib.parse import urlparse
else:
    from urlparse import urlparse        # See https://docs.python.org/2/library/urlparse.html

from Transport import Transport
from TransportHTTPBase import TransportHTTPBase
from Errors import CodingException
from Dweb import Dweb
from KeyPair import KeyPair

#TODO-HTTP add support for HTTPS

class TransportHTTP(TransportHTTPBase):
    """
    Subclass of Transport.
    Implements the raw primitives as HTTP calls to ServerHTTP which interprets them.
    """

    defaulthttpoptions = {
        "ipandport": ['localhost', 4243]
    }
    urlschemes = ['http']


    def __repr__(self):
        return self.__class__.__name__ + " " + dumps(self.options)

    @classmethod
    def setup(cls, options, verbose):
        """
        Called to deliver a transport instance of a particular class.
        Copied to dweb.js

        :param options: Options to subclasses init method
        :return: new instance of TransportHTTP
        """
        t = cls( Transport.mergeoptions(cls.defaulthttpoptions, options), verbose=verbose)
        Dweb.transports["http"] = t
        Dweb.transportpriority.append(t)
        return t

    @staticmethod
    def _multihash(data=None, url=None):
        """
        Return a multihash (string of form Q....

        :param data:    optional - data to hash
        :param url:     url to pull multihash from (last part of path)
        :return:        string of form Q.... (base58 of multihash of sha256 of data)
        """
        if data:
            return KeyPair.multihashsha256_58(data)
        if url:
            if isinstance(url,basestring):
               url = urlparse(url)
            return url.path.split('/')[-1]

    def url(self, data=None, multihash=None): #TODO-API
        """
         Return an identifier for the data without storing

         :param string|Buffer data   arbitrary data
         :return string              valid id to retrieve data via rawfetch
         """
        if data:
            multihash = TransportLocal._multihash(data=data)
        return "http://"+this.options["http"]["ipandport"][0]+":"+this.options["http"]["ipandport"][1]+"/rawfetch/"+ multihash

    #see other !ADD-TRANSPORT-COMMAND - add a function copying the format below
    # TransportHTTPBase handles: info()

    def rawfetch(self, url=None, verbose=False, **options):
        if verbose: print "TransportHTTP.rawfetch(%s)" % url
        multihash = self._multihash(url=url)
        res = self._sendGetPost(False, "rawfetch", urlargs=[multihash], verbose=verbose, params=options)
        return res.text

    def rawlist(self, url, verbose=False, **options):
        if verbose: print "list", url, options
        if not url:
            raise CodingException(message="TransportHTTP.rawlist requires a url")
        multihash = self._multihash(url=url)
        res = self._sendGetPost(False, "rawlist", urlargs=[multihash], params=options)
        return res.json()   # Data version of list - an array

    def rawreverse(self, url, verbose=False, **options):
        if verbose: print "reverse", url, options
        if not url:
            raise CodingException(message="TransportHTTP.rawlist requires a url")
        multihash = self._multihash(url=url)
        res = self._sendGetPost(False, "rawreverse", urlargs=[multihash], params=options)
        return res.json()   # Data version of list - an array

    def rawstore(self, data=None, verbose=False, **options):
        if not data:
            raise CodingException(message="TransportHTTP.rawstore requires data")
        res = self._sendGetPost(True, "rawstore", headers={"Content-Type": "application/octet-stream"}, urlargs=[], data=data, verbose=verbose)
        return str(res.text) # Should be the url - need to return a str, not unicode which isn't supported by decode

    def rawadd(self, url=None, date=None, signature=None, signedby=None, verbose=False, **options):
        if verbose: print "add", url, date, signature, signedby, options
        if not url:
            raise CodingException(message="TransportHTTP.rawlist requires a url")
        value = self._add_value( url=url, date=date, signature=signature, signedby=signedby, verbose=verbose, **options)+ "\n"
        if not (url and date and signature and signedby):
            raise CodingException(message="TransportHTTP.rawadd requires all args:"+value)
        # Note this is sending url, not multihash in the urlargs, that is what was signed. Should convert to multihash before storing.
        res = self._sendGetPost(True, "rawadd", urlargs = [], headers={"Content-Type": "application/json"}, params={}, data=value)

