# encoding: utf-8
import urllib
#from Errors import _print
from Block import Block
from StructuredBlock import StructuredBlock
from MutableBlock import MutableBlock
from MyHTTPServer import MyHTTPRequestHandler, exposed
from Errors import ToBeImplementedException
from Transportable import Transportable
from KeyPair import KeyPair
from Dweb import Dweb
from sys import version as python_version
from json import loads, dumps
if python_version.startswith('3'):
    from urllib.parse import urlparse
else:
    from urlparse import urlparse        # See https://docs.python.org/2/library/urlparse.html

#TODO-API needs writing up

class DwebHTTPRequestHandler(MyHTTPRequestHandler):

    #defaultipandport = ('192.168.1.156', 4243)
    defaultipandport = (u'localhost', 4243)
    defaulthttpoptions = { "ipandport": defaultipandport }
    onlyexposed = True          # Only allow calls to @exposed methods

    @classmethod
    def HTTPToLocalGateway(cls):
        """
        DWeb HTTP server, all this one does is gateway from HTTP Transport to Local Transport, allowing calls to happen over net.
        One instance of this will be created for each request, so don't override __init__()
        Initiate with something like: DwebHTTPRequestHandler.serve_forever()

        :return: Never Returns
        """
        from TransportLocal import TransportLocal # Avoid circular references
        tl = TransportLocal.setup({ "local": { "dir": "../cache_http" }}, verbose=False)# HTTP server is storing locally
        Dweb.transports["local"] = tl
        Dweb.transportpriority.append(tl)
        cls.serve_forever(verbose=True)    # Uses defaultipandport
        #TODO-HTTP its printing log, put somewhere instead

    #see other !ADD-TRANSPORT-COMMAND - add a function copying the format below

    @exposed
    def sandbox(self, foo, bar, **kwargs):
        # Changeable, just for testing HTTP
        print "foo=",foo,"bar=",bar, kwargs
        return { 'Content-type': 'application/json',
                 'data': { "FOO": foo, "BAR": bar, "kwargs": kwargs}
               }


    @exposed
    def info(self, **kwargs):
        return { 'Content-type': 'application/json',
                 'data': { "type:": "http"}
               }

    @exposed
    def rawfetch(self, url=None, contenttype="application/octet-stream", **kwargs):
        """
        Retrieve a block, Paired with TransportHTTP.fetch
        Exceptions: TransportBlockNotFound if url invalid

        :param url: block to retrieve
        :return: { Content-Type, data: raw data from block
        """
        #print "ServerHTTP.rawfetch url=",url
        return {"Content-type": contenttype,
                "data": Dweb.transport(url).rawfetch(url=url)} # Should be raw data returned

    @exposed
    def rawlist(self, url=None, **kwargs):
        """
        Retrieve a list of objects - Paired with TransportHTTP.list

        :param url: key to retrieve values for
        :return:
        """
        return { 'Content-type': 'application/json',
                 'data': Dweb.transport(url).rawlist(url=url, **kwargs)
               }

    @exposed
    def rawreverse(self, url=None, **kwargs):
        """
        Retrieve a list of objects - Paired with TransportHTTP.list

        :param url: key to retrieve values for
        :return:
        """
        return {'Content-type': 'application/json',
                'data': Dweb.transport(url).rawreverse(url=url, **kwargs)
                }

    @exposed
    def rawstore(self, data=None, **kwargs):
        url = Dweb.transport().rawstore(data=data, **kwargs)
        multihash = urlparse(url).path.split('/')[-1]
        url = "http://%s:%s/rawfetch/%s" % (self.ipandport[0],self.ipandport[1],multihash)
        return { "Content-type": "application/octet-stream", "data": url }

    @exposed
    def rawadd(self, data=None, verbose=False, **kwargs):
        """
        Pass raw data on to transport layer,

        :param data: Dictionary to add {url, signature, date, signedby} or json string of it.
        """
        if isinstance(data, basestring): # Assume its JSON
            data = loads(data)    # HTTP just delivers bytes    //TODO-HTTP obviously wron
        data["verbose"]=verbose
        return  { "Content-type": "application/octet-stream",
                  "data":  Dweb.transport(data["signedby"]).rawadd(**data)
                  }
        #url=None, date=None, signature=None, signedby=None, verbose=False, **options):

    @exposed
    def content(self, table=None, url=None, urlargs=None, contenttype=None, verbose=False, **kwargs):
        return Dweb.transport(url).fetch("content", cls=table, url=url, path=urlargs, verbose=verbose, contenttype=contenttype, **kwargs  )

    @exposed
    def file(self, table=None, url=None, urlargs=None, contenttype=None, verbose=False, **kwargs):
        #TODO-EFFICIENCY - next call does 2 fetches
        #verbose=True
        return Dweb.transport(url).fetch(command="file", cls=table, url=url,path=urlargs, verbose=verbose, contenttype=contenttype, **kwargs  )

if __name__ == "__main__":
    DwebHTTPRequestHandler.HTTPToLocalGateway() # Run local gateway

