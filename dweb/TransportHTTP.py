# encoding: utf-8

from sys import version as python_version
import requests             # For outgoing HTTP http://docs.python-requests.org/en/master/
from Transport import Transport, TransportURLNotFound
#from misc import ToBeImplementedException
from CryptoLib import CryptoLib
import urllib

#TODO-HTTP add support for HTTPS

class TransportHTTP(Transport):
    """
    HTTP transport class, will
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

    # TODO-REFACTOR need to scan and update this file

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

    def store(self, data=None, verbose=False, **options):
        """
        Store the data locally

        :param data: opaque data to store, or obj with _data method
        :return: hash of data
        """
        if not isinstance(data, basestring):
            data = data._data
        res = self._sendGetPost(True, "store", headers={"Content-Type": "application/octet-stream"}, urlargs=[], data=data )
        return str(res.text) # Should be the hash - need to return a str, not unicode which isn't supported by decode

    def block(self, hash=None, **options):
        """
        Fetch a block,
        Paired with DwebDispatcher.block

        :param options: parameters to block, must include "hash"
        :return:
        """
        res = self._sendGetPost(False, "block", urlargs=[hash], params=options)
        return res.text

    def add(self, hash=None, date=None, signature=None, signedby=None, verbose=False, **options):
        #TODO fix params docs here and elsewhere in Transport
        """
        Store in a DHT

        :param table:   Table to store in
        :param hash:     Key to store under
        :param value:   Value - usually a dict - to store.
        :param verbose: Report on activity - passed in options so passes through to sendGet
        :param options:
        :return:
        """
        if options.get("verbose",None): print "add", hash, date, signature, signedby, options
        value = self._add_value( hash=hash, date=date, signature=signature, signedby=signedby, verbose=verbose, **options)+ "\n"
        res = self._sendGetPost(True, "add", urlargs = [], headers={"Content-Type": "application/json"}, params={}, data=value)

    def list(self, hash=None, verbose=False, **options):
        """
        Method to retrieve record(s) matching a key.
        Copied to dweb.py

        :param table: Table to look for key in
        :param hash: Key to be retrieved (embedded in options for easier pass through)
        :return: list of dictionaries for each item retrieved
        """
        if verbose: print "list", hash, options
        res = self._sendGetPost(False, "list", urlargs=[hash], params=options)
        return res.json()

    def url(self, obj, command=None, hash=None, table=None, contenttype=None, **options):
        """

        :return: HTTP style URL to access this resource - not sure what this works on yet.
        """
        #TODO-REFACTOR need to fix TransportHTTP.url
        from MutableBlock import MutableBlock
        # Identical to ServerHTTP.url
        hash = hash or obj._hash
        url =  "http://%s:%s/%s/%s/%s"  \
               % (self.ipandport[0], self.ipandport[1], command or obj.transportcommand, table or obj.table, hash)
        # TODO-REFACTOR probably remove transportcommand in all places
        if contenttype:
            if command in ("update",):  # Some commands allow type as URL parameter
                url += "/" + urllib.quote(contenttype, safe='')
            else:
                url += "?contenttype=" + urllib.quote(contenttype, safe='')
        return url