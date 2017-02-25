# encoding: utf-8
from json import dumps
from sys import version as python_version
from cgi import parse_header, parse_multipart
import BaseHTTPServer       # See https://docs.python.org/2/library/basehttpserver.html for docs on how servers work
                            # also /System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/BaseHTTPServer.py for good error code list
import urlparse             # See https://docs.python.org/2/library/urlparse.html
from misc import MyBaseException, ToBeImplementedException
from Block import Block

if python_version.startswith('3'):
    from urllib.parse import parse_qs, parse_qsl
    from http.server import BaseHTTPRequestHandler
else:
    from urlparse import parse_qs, parse_qsl
    from BaseHTTPServer import BaseHTTPRequestHandler



#TODO-HTTP return errors using send_error and backport to sqlite_models
#TODO-HTTP add support for HTTPS

class HTTPdispatcherException(MyBaseException):
    httperror = 501     # Unimplemented
    msg = "HTTP request {req} not recognized"

class HTTPargrequiredException(MyBaseException):
    httperror = 400     # Unimplemented
    msg = "HTTP request {req} requires {arg}"

class HTTPdispatcher():
    """
    Simple (standard) HTTPdispatcher,
    Subclasses should define "exposed" as a list of exposed methods
    """
    exposed = []

    @staticmethod
    def _checkargs(req, arglist, kwargs):
        for arg in arglist:
            if arg not in kwargs:
                raise HTTPargrequiredException(req=req, arg=arg)  # Will be caught in MyHTTPRequestHandler._dispatch

    @classmethod
    def dispatch(cls, req, **kwargs):
        """
        Dispatch a request - drawn from the URL, to a function with the same name, pass any args,

        :param req: main part of URL passed (after /)
        :param kwargs: args either in URL or in postparams
        :return: result of dispatched method
        """
        verbose=False   # Cant pass thru kwargs
        #"sms_poll": sms_poll,
        #"sms_incoming": sms_incoming
        if verbose: print "HTTPdispatcher.dispatch",req,kwargs
        #TODO - switch tis round to test "exposed" on retrieved function instead of list
        if req in cls.exposed:
            return getattr(cls, req)(**kwargs)
        else:
            if verbose: print "HTTPdispatcher.dispatch unimplemented:"+req
            raise HTTPdispatcherException(req=req)  # Will be caught in MyHTTPRequestHandler._dispatch


class MyHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    Generic HTTPRequestHandler, extends BaseHTTPRequestHandler, to make it easier to use
    """
    # Carefull - do not define __init__ as it is run for each incoming request.
    #TODO-HTTP add support for longer (streamed) files on both upload and download

    @classmethod
    def serve_forever(cls, dispatchclass=None, ipandport=None, verbose=False, **options):
        """
        Start a server,

        :param dispatchclass: Class to use for dispatcher, else use defaultdispatchclass
        :param ipandport: Ip and port to listen on, else use defaultipandport
        :param verbose: If want debugging
        :param options: Stored on class for access by handlers
        :return: Never returns
        """
        cls.dispatchclass = dispatchclass or cls.defaultdispatchclass
        cls.ipandport = ipandport or cls.defaultipandport
        cls.verbose = verbose
        cls.options = options
        if verbose: print "Setup server at",cls.ipandport
        BaseHTTPServer.HTTPServer( cls.ipandport, cls).serve_forever() # Start http server

    def _dispatch(self, **vars):
        """
        Support function - dispatch the function found with postparams &/or URL arguments (former take precedence)
        Special argument vars["data"] has posted data or JSON

        :param vars: dictionary of vars - typically from post, but also data="..."
        :return:
        """
        try:
            verbose=False   # Cant pass through vars as they are postvariables
            o = urlparse.urlparse(self.path)
            argvars =  dict(parse_qsl(o.query))     # Look for arguments in URL
            if verbose: print "Handler._dispatch", o.path[1:], vars, argvars
            argvars.update(vars)                    # URL args are updated by any from postparms
            res = self.dispatchclass.dispatch(o.path[1:], **argvars)    # The main part - call a dispatchable staticmethod
            if verbose: print "_dispatch:Result=",res
            # Send the content-type
            self.send_response(200)  # Send an ok response
            if res is None:
                pass
            elif isinstance(res, (dict, list, tuple)):
                res = dumps(res)
                self.send_header('Content-type', 'text/json')
            elif isinstance(res, basestring):
                self.send_header('Content-type', 'application/octet-stream')
            else:
                # Raise an exception - will not honor the status already sent, but this shouldnt happen as coding
                # error in the dispatched function if it returns anything else
                raise ToBeImplementedException(name=self.__class__.__name__+"._dispatch for "+res.__class__.__name__)
            self.send_header('Content-Length', str(len(res)) if res else 0)
            self.end_headers()
            self.wfile.write(res)                   # Write content of result if applicable
        except Exception as e:
            httperror = e.httperror if hasattr(e, "httperror") else 500
            self.send_error(httperror, str(e))  # Send an error response

    def do_GET(self):
        self._dispatch()


    def do_POST(self):
        """
        Handle a HTTP POST - reads data in a variety of common formats and passes to _dispatch

        :return:
        """
        try:
            verbose = False
            if verbose: print self.headers
            ctype, pdict = parse_header(self.headers['content-type'])
            if verbose: print ctype, pdict
            if ctype == 'multipart/form-data':
                postvars = parse_multipart(self.rfile, pdict)
            elif ctype == 'application/x-www-form-urlencoded':
                length = int(self.headers['content-length'])
                postvars = parse_qs(
                    self.rfile.read(length),
                    keep_blank_values=1)
            elif ctype == 'application/octet-stream':  # Block sends this
                length = int(self.headers['content-length'])
                postvars = {"data": self.rfile.read(length)}
            elif ctype == 'application/json':
                raise ToBeImplementedException(name="do_POST:application/json")
            else:
                postvars = {}
            self._dispatch(**postvars)
        #except Exception as e:
        except ZeroDivisionError as e:  # Uncomment this to actually throw exception
            httperror = e.httperror if hasattr(e, "httperror") else 500
            self.send_error(httperror, str(e))  # Send an error response



class DwebDispatcher(HTTPdispatcher):
    exposed = ["block", "store", "DHT_store", "DHT_fetch"]

    @staticmethod
    def block(**kwargs):
        """
        Retrieve a block, Paired with TransportHTTP.block

        :param kwargs: { hash }
        :return: raw data from block
        """
        verbose = kwargs.get("verbose", False)
        if verbose: print "DwebDispatcher.block", kwargs
        HTTPdispatcher._checkargs("store", ("hash",), kwargs)
        b = Block.block(hash=kwargs["hash"]) # Should be raw data returned
        return b._data

    @staticmethod
    def store(**kwargs):
        verbose = kwargs.get("verbose", False)
        if verbose: print "DwebDispatcher.store", kwargs
        HTTPdispatcher._checkargs("store", ("data",), kwargs)
        hash = Block(kwargs["data"]).store()
        if verbose: print "DwebDispatcher.store returning:", hash
        return hash

    @staticmethod
    def DHT_store(**kwargs):
        """
        DHT_store has no higher level interpretation, so just pass to server's transport layer direct
        Once distributed, this will be clever, or rather ITS transport layer should be.

        :param kwargs:
        :return:
        """
        verbose = kwargs.get("verbose", False)
        if verbose: print "DwebDispatcher.DHT_store",kwargs
        HTTPdispatcher._checkargs("DHT_store", ("table", "key", "data"), kwargs)
        kwargs["value"] = kwargs["data"]
        del kwargs["data"]
        return Block.transport.DHT_store(**kwargs)  # table, key, value


    @staticmethod
    def DHT_fetch(**kwargs):
        """
        DHT_fetch has no higher level interpretation, so just pass to server's transport layer direct
        Once distributed, this will be clever, or rather ITS transport layer should be.

        :param table: table to look up value in
        :param key: key to retrieve values for
        :return:
        """
        verbose = kwargs.get("verbose", False)
        if verbose: print "DwebDispatcher.DHT_fetch", kwargs
        HTTPdispatcher._checkargs("DHT_store", ("table", "key"), kwargs)
        return Block.transport.DHT_fetch(**kwargs)  # table, key


class DwebHTTPRequestHandler(MyHTTPRequestHandler):
    """
    DWeb HTTP server
    Initiate with something like:
    DwebHTTPRequestHandler.serve_forever()
    """
    # NOTE this is adapted from sqlite_models, any changes might want to go back there
    defaultdispatchclass = DwebDispatcher
    defaultipandport = ('localhost', 4243)

    @classmethod
    def HTTPToLocalGateway(self):
        """
        Launch a gateway that answers on HTTP and forwards to Local

        :return: Never Returns
        """
        from TransportLocal import TransportLocal # Avoid circular references
        Block.setup(TransportLocal, verbose=False, dir="../cache_http")  # HTTP server is storing locally
        DwebHTTPRequestHandler.serve_forever(verbose=False)
        #TODO-HTTP its printing log, put somewhere instead

if __name__ == "__main__":
    DwebHTTPRequestHandler.HTTPToLocalGateway() # Run local gateway

