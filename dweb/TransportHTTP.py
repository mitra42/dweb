# encoding: utf-8

from TransportHTTPBase import TransportHTTPBase
#TODO-BACKPORT - review this file

#TODO-HTTP add support for HTTPS

class TransportHTTP(TransportHTTPBase):
    """
    Subclass of Transport.
    Implements the raw primitives as HTTP calls to ServerHTTP which interprets them.
    """

    @classmethod
    def setup(cls, options, verbose):   #TODO-BACKPORT find callers
        """
        Called to deliver a transport instance of a particular class.
        Copied to dweb.js

        :param options: Options to subclasses init method
        :return: None
        """
        return cls( options=options, verbose=verbose,)


    #see other !ADD-TRANSPORT-COMMAND - add a function copying the format below
    # TransportHTTPBase handles: info()

    def rawfetch(self, url=None, verbose=False, **options):
        if verbose: print "TransportHTTP.rawfetch(%s)" % url
        res = self._sendGetPost(False, "rawfetch", urlargs=[url], verbose=verbose, params=options)
        return res.text

    def rawlist(self, url, verbose=False, **options):
        if verbose: print "list", url, options
        res = self._sendGetPost(False, "rawlist", urlargs=[url], params=options)
        return res.json()   # Data version of list - an array

    def rawreverse(self, url, verbose=False, **options):
        if verbose: print "reverse", url, options
        res = self._sendGetPost(False, "rawreverse", urlargs=[url], params=options)
        return res.json()   # Data version of list - an array

    def rawstore(self, data=None, verbose=False, **options):
        res = self._sendGetPost(True, "rawstore", headers={"Content-Type": "application/octet-stream"}, urlargs=[], data=data, verbose=verbose)
        return str(res.text) # Should be the url - need to return a str, not unicode which isn't supported by decode

    def rawadd(self, url=None, date=None, signature=None, signedby=None, verbose=False, **options):
        if verbose: print "add", url, date, signature, signedby, options
        value = self._add_value( url=url, date=date, signature=signature, signedby=signedby, verbose=verbose, **options)+ "\n"
        res = self._sendGetPost(True, "rawadd", urlargs = [], headers={"Content-Type": "application/json"}, params={}, data=value)

