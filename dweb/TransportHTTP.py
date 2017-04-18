# encoding: utf-8

from sys import version as python_version
import requests             # For outgoing HTTP http://docs.python-requests.org/en/master/
from Transport import Transport, TransportURLNotFound
from misc import ToBeImplementedException
from CryptoLib import CryptoLib
import urllib

#TODO-HTTP add support for HTTPS

class TransportHTTPBase(Transport):
    """
    Common parts for TransportHTTP and TransportDist
    """

    def _sendGetPost(self, post, command, urlargs=None, verbose=False, **options):
        """
        Construct a URL of form  baseurl / command / urlargs ? options

        :param post: True if should POST, else GET
        :param command: command passing to server
        :param urlargs: contactenated to command in order given
        :param verbose: if want to display IRL used, place IN params to send to server
        :param params:  passed to requests.get, forms arguments after "?"
        :param headers: passe to requests.get, sent as HTTP headers
        :param options:
        :return: Response - can access via .text, .content and .headers
        """
        url = self.baseurl + command
        if urlargs:
            url += "/" + "/".join(urllib.quote(u) for u in urlargs)
        if verbose: print "sending","POST" if post else "GET","request to",url,options
        try:
            r = None
            r = requests.post(url, **options) if post else requests.get(url, **options)
            r.raise_for_status()
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            if r is not None and (r.status_code == 404):
                raise TransportURLNotFound(url=url, options=options)
            else:
                print e
                #TODO-LOGGING: logger.error(e)
                raise e # For now just raise it
        #print r.status_code, r.text # r.json()
        return r    # r is a response

    def info(self, verbose=False, **options):
        if verbose: print "%s.info" % self.__class__.__name__
        res = self._sendGetPost(False, "info", urlargs=[], verbose=verbose, params=options)
        return res.json()

class TransportHTTP(TransportHTTPBase):
    """
    Subclass of Transport.
    Implements the raw primitives as HTTP calls to ServerHTTP which interprets them.
    """

    def __init__(self, ipandport=None, verbose=False, **options):
        """
        Use blah

        :param blah:
        """
        self.ipandport = ipandport
        self.verbose = verbose
        self.baseurl = "http://%s:%s/" % (ipandport[0], ipandport[1])   # Note trailing /

    @classmethod
    def setup(cls, ipandport=None, **options):
        """
        Called to deliver a transport instance of a particular class.
        Copied to dweb.js

        :param options: Options to subclasses init method
        :return: None
        """
        return cls(ipandport=ipandport, **options)


    #see other !ADD-TRANSPORT-COMMAND - add a function copying the format below
    # TransportHTTPBase handles: info()

    def rawfetch(self, hash=None, verbose=False, **options):
        if verbose: print "TransportHTTP.rawfetch(%s)" % hash
        res = self._sendGetPost(False, "rawfetch", urlargs=[hash], verbose=verbose, params=options)
        return res.text

    def rawlist(self, hash, verbose=False, **options):
        if verbose: print "list", hash, options
        res = self._sendGetPost(False, "rawlist", urlargs=[hash], params=options)
        return res.json()   # Data version of list - an array

    def rawreverse(self, hash, verbose=False, **options):
        if verbose: print "reverse", hash, options
        res = self._sendGetPost(False, "rawreverse", urlargs=[hash], params=options)
        return res.json()   # Data version of list - an array

    def rawstore(self, data=None, verbose=False, **options):
        res = self._sendGetPost(True, "rawstore", headers={"Content-Type": "application/octet-stream"}, urlargs=[], data=data, verbose=verbose)
        return str(res.text) # Should be the hash - need to return a str, not unicode which isn't supported by decode

    def rawadd(self, hash=None, date=None, signature=None, signedby=None, verbose=False, **options):
        if verbose: print "add", hash, date, signature, signedby, options
        value = self._add_value( hash=hash, date=date, signature=signature, signedby=signedby, verbose=verbose, **options)+ "\n"
        res = self._sendGetPost(True, "rawadd", urlargs = [], headers={"Content-Type": "application/json"}, params={}, data=value)

    def url(self, obj, command=None, hash=None, table=None, contenttype=None, url_output=None, **options):
        """

        :return: HTTP style URL to access this resource - not sure what this works on yet.
        """
        # Identical code in TransportHTTP and ServerHTTP.url
        hash = hash or obj._hash
        if command in ["file"]:
            if url_output=="getpost":
                return [False, command, [table or obj.table, hash]]
            else:
                url = "http://%s:%s/%s/%s/%s" \
                    % (self.ipandport[0], self.ipandport[1], command, table or obj.table, hash)
        else:
            if url_output=="getpost":
                raise ToBeImplementedException(name="TransportHTTP.url:command="+(command or "None")+",url_output="+url_output)
            else:
                url =  "http://%s:%s/%s/%s"  \
                    % (self.ipandport[0], self.ipandport[1], command or "rawfetch", hash)
        if contenttype:
            if command in ("update",):  # Some commands allow type as URL parameter
                url += "/" + urllib.quote(contenttype, safe='')
            else:
                url += "?contenttype=" + urllib.quote(contenttype, safe='')
        return url
