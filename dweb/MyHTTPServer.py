# encoding: utf-8
from json import dumps
from sys import version as python_version
from cgi import parse_header, parse_multipart
import BaseHTTPServer       # See https://docs.python.org/2/library/basehttpserver.html for docs on how servers work
                            # also /System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/BaseHTTPServer.py for good error code list
from misc import MyBaseException, ToBeImplementedException

if python_version.startswith('3'):
    from urllib.parse import parse_qs, parse_qs, urlparse
    from http.server import BaseHTTPRequestHandler
else:
    from urlparse import parse_qs, parse_qsl, urlparse        # See https://docs.python.org/2/library/urlparse.html
    from BaseHTTPServer import BaseHTTPRequestHandler

import traceback

#TODO-HTTP add support for HTTPS

class HTTPdispatcherException(MyBaseException):
    httperror = 501     # Unimplemented
    msg = "HTTP request {req} not recognized"

class HTTPargrequiredException(MyBaseException):
    httperror = 400     # Unimplemented
    msg = "HTTP request {req} requires {arg}"

class MyHTTPdispatcher():
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

#TODO - merge MyHTTPRequestHandler and MyHTTPdispatcher

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
            o = urlparse(self.path)
            print "XXX@98",o
            argvars =  dict(parse_qsl(o.query))     # Look for arguments in URL
            if verbose: print "Handler._dispatch", o.path[1:], vars, argvars
            argvars.update(vars)                    # URL args are updated by any from postparms
            res = self.dispatchclass.dispatch(o.path[1:], **argvars)    # The main part - call a dispatchable staticmethod
            if verbose: print "_dispatch:Result=",res
            # Send the content-type
            self.send_response(200)  # Send an ok response
            self.send_header('Content-type', res["Content-type"])
            data = res["data"]
            if isinstance(data, (dict, list, tuple)):    # Turn it into JSON
                data = dumps(data)
            elif hasattr(data, "dumps"):
                data = dumps(data)
            if not isinstance(data, basestring):
                # Raise an exception - will not honor the status already sent, but this shouldnt happen as coding
                # error in the dispatched function if it returns anything else
                raise ToBeImplementedException(name=self.__class__.__name__+"._dispatch for "+data.__class__.__name__)
            self.send_header('Content-Length', str(len(data)) if data else 0)
            self.end_headers()
            self.wfile.write(data)                   # Write content of result if applicable
        except Exception as e:
            traceback.print_exc(limit=None)  # unfortunately only prints to try above so need to raise
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

