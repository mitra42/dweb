# encoding: utf-8
#from Errors import _print
from json import loads, dumps
from sys import version as python_version
if python_version.startswith('3'):
    from urllib.parse import urlparse
else:
    from urlparse import urlparse        # See https://docs.python.org/2/library/urlparse.html
from ServerBase import MyHTTPRequestHandler, exposed


"""
For documentation on this project see https://docs.google.com/document/d/1FO6Tdjz7A1yi4ABcd8vDz4vofRDUOrKapi3sESavIcc/edit# 
"""

#TODO-API needs writing up
#TODO-PYTHON3 - whole file needsporting to Python2/3 compatability
#TODO-LOG setup generic logger and move all print calls to use it

class DwebGatewayHTTPRequestHandler(MyHTTPRequestHandler):

    defaulthttpoptions = { "ipandport": (u'localhost', 4244) }
    onlyexposed = True          # Only allow calls to @exposed methods
    expectedExceptions = []     # List any exceptions that you "expect" (and dont want stacktraces for)

    @classmethod
    def DwebGatewayHTTPServeForever(cls, httpoptions={}, verbose=False):
        """
        DWeb HTTP server, all this one does is gateway from HTTP Transport to Local Transport, allowing calls to happen over net.
        One instance of this will be created for each request, so don't override __init__()
        Initiate with something like: DwebGatewayHTTPRequestHandler.serve_forever()

        Services exposed:
        /info           Returns data structure describing gateway

        :return: Never Returns
        """
        httpoptions = mergeoptions(cls.defaulthttpoptions, httpoptions) # Deepcopy to merge options
        if (verbose): print("Starting server with options=",httpoptions)
        #TODO any code needed once (not per thread) goes here.
        cls.serve_forever(ipandport=httpoptions["ipandport"], verbose=verbose)    # Uses defaultipandport

    @exposed    # Exposes this function for outside use
    def sandbox(self, foo, bar, **kwargs):
        # Changeable, just for testing HTTP etc, feel free to play with in your branch, and expect it to be overwritten on master branch.
        print("foo=",foo,"bar=",bar, kwargs)
        return { 'Content-type': 'application/json',
                 'data': { "FOO": foo, "BAR": bar, "kwargs": kwargs}
               }

    @exposed
    def info(self, **kwargs):   # http://.../info
        """
        Return info about this server
        The content of this may change, make sure to retain the "type" field.

        ConsumedBy:
            "type" consumed by status function TransportHTTP (in Dweb client library)
        Consumes:
        """
        return { 'Content-type': 'application/json',
                 'data': { "type": "gateway",
                           "services": [ ]}     # A list of names of services supported below  (not currently consumed anywhere)
               }


if __name__ == "__main__":
    DwebGatewayHTTPRequestHandler.DwebGatewayHTTPServeForever({'ipandport': (u'localhost',4244)}) # Run local gateway

