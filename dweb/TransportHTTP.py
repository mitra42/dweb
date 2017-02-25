# encoding: utf-8

import requests             # For outgoing HTTP http://docs.python-requests.org/en/master/
from Transport import Transport
from misc import ToBeImplementedException
from CryptoLib import CryptoLib

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
        self.options = options
        self.verbose = verbose
        self.baseurl = "http://%s:%s/" % (ipandport[0], ipandport[1])

    @classmethod
    def setup(cls, ipandport=None, **options):
        """
        Called to deliver a transport instance of a particular class

        :param options: Options to subclasses init method
        :return: None
        """
        return cls(ipandport=ipandport, **options)

    #TODO-HTTP merge sendPost and sendGet if appropriate
    def _sendPost(self, command, **options):
        url = self.baseurl + command
        #print 'sending POST request to',url,options
        try:
            r = requests.post(url, **options)
            r.raise_for_status()
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            print e
            #TODO-LOGGING: logger.error(e)
            raise e # For now just raise it
        #print r.status_code, r.text # r.json()
        return r    # r is a response

    def _sendGet(self, command, **options):
        url = self.baseurl + command
        #print 'sending GET request to',url,options
        try:
            r = requests.get(url, **options)
            r.raise_for_status()
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            print e
            #TODO-LOGGING: logger.error(e)
            raise e # For now just raise it
        #print r.status_code, r.text # r.json()
        return r    # r is a "Response"

    def store(self, data):
        """
        Store the data locally

        :param data: opaque data to store
        :return: hash of data
        """
        res = self._sendPost("store", headers={"Content-Type": "application/octet-stream"}, data=data )
        return str(res.text) # Should be the hash - need to return a str, not unicode which isn't supported by decode

    def block(self, **options):
        """
        Fetch a block,
        Paired with DwebDispatcher.block

        :param options: parameters to block, must include "hash"
        :return:
        """
        res = self._sendGet("block", params=options)
        return res.text

    def DHT_store(self, table=None, key=None, value=None, **options): # Expecting: table, key, value
        """
        Store in a DHT

        :param table:   Table to store in
        :param key:     Key to store under
        :param value:   Value - usually a dict - to store.
        :param verbose: Report on activity - passed in options so passes through to sendGet
        :param options:
        :return:
        """
        if options.get("verbose",None): print "DHT_store",table, key, value, options
        res = self._sendPost("DHT_store", headers={"Content-Type": "application/octet-stream"}, params={"table": table, "key": key}, data=CryptoLib.dumps(value))

    def DHT_fetch(self, table, key, verbose=False, **options):
        """
        Method that should always be subclassed to retrieve record(s) matching a key

        :param table: Table to look for key in
        :param key: Key to be retrieved
        :return: list of dictionaries for each item retrieved
        """
        if options.get("verbose",None): print "DHT_fetch",table, key, options
        res = self._sendGet("DHT_fetch", params={"table": table, "key": key})
        return res.json()

