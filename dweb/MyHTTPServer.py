# encoding: utf-8
from json import dumps, loads
from sys import version as python_version
from cgi import parse_header, parse_multipart
import urllib
import BaseHTTPServer       # See https://docs.python.org/2/library/basehttpserver.html for docs on how servers work
                            # also /System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/BaseHTTPServer.py for good error code list

"""
This file is intended to be Application independent , i.e. not dependent on Dweb.
"""

if python_version.startswith('3'):
    from urllib.parse import parse_qs, parse_qs, urlparse
    from http.server import BaseHTTPRequestHandler
else:
    from urlparse import parse_qs, parse_qsl, urlparse        # See https://docs.python.org/2/library/urlparse.html
    from BaseHTTPServer import BaseHTTPRequestHandler

import traceback

from misc import MyBaseException, ToBeImplementedException
from Transport import TransportBlockNotFound,TransportFileNotFound

#TODO-HTTP add support for HTTPS

class HTTPdispatcherException(MyBaseException):
    httperror = 501     # Unimplemented
    msg = "HTTP request {req} not recognized"

class HTTPargrequiredException(MyBaseException):
    httperror = 400     # Unimplemented
    msg = "HTTP request {req} requires {arg}"

class DWEBMalformedURLException(MyBaseException):
    httperror = 400
    msg = "Malformed URL {path}"

class MyHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    Generic HTTPRequestHandler, extends BaseHTTPRequestHandler, to make it easier to use
    """
    # Carefull - do not define __init__ as it is run for each incoming request.
    # TODO-HTTP add support for longer (streamed) files on both upload and download

    """
    Simple (standard) HTTPdispatcher,
    Subclasses should define "exposed" as a list of exposed methods
    """
    exposed = []

    @classmethod
    def serve_forever(cls, ipandport=None, verbose=False, **options):
        """
        Start a server,

        :param ipandport: Ip and port to listen on, else use defaultipandport
        :param verbose: If want debugging
        :param options: Stored on class for access by handlers
        :return: Never returns
        """
        cls.ipandport = ipandport or cls.defaultipandport
        cls.verbose = verbose
        cls.options = options
        if verbose: print "Setup server at",cls.ipandport
        BaseHTTPServer.HTTPServer( cls.ipandport, cls).serve_forever() # Start http server
        print "Server exited" # It never should

    def _dispatch(self, **vars):
        """
        Support function - dispatch the function found with postparams &/or URL arguments (former take precedence)
        Special argument vars["data"] has posted data or JSON
        Exception: DWEBMalformedURLException if URL bad

        :param vars: dictionary of vars - typically from post, but also data="..."
        :return:
        """
        try:
            verbose=False   # Cant pass through vars as they are postvariables
            o = urlparse(self.path)
            argvars =  dict(parse_qsl(o.query))     # Look for arguments in URL
            verbose = argvars.get("verbose", verbose)
            if verbose: print "Handler._dispatch", o.path[1:], vars, argvars
            argvars.update(vars)                    # URL args are updated by any from postparms
            req = o.path[1:]
            #TODO - split req if has / and use parms from exposed.
            if '/' in req:
                urlargs = [ urllib.unquote(u) for u in req.split('/') ]
                req = urlargs.pop(0)    # urlargs will be the rest of the args
            else:
                urlargs = []
            # Dispatch a request - drawn from the URL, to a function with the same name, pass any args,
            if verbose: print "HTTPdispatcher.dispatch", req, urlargs, argvars
            func = getattr(self, req, None)
            if func and func.exposed:
                if func.arglist:
                    # Override any of the args specified in arglist by the fields of the URL in order
                    for i in range(len(urlargs)):
                        if i >= len(func.arglist):
                            break
                        argname = func.arglist[i]
                        argvars[argname]=urlargs.pop(0)
                    # urlargs contain any beyond the
                    for arg in func.arglist:
                        if arg not in argvars:
                            raise HTTPargrequiredException(req=req, arg=arg)  # Will be caught in MyHTTPRequestHandler._dispatch
                if verbose: print "%s.%s %s" % (self.__class__.__name__, req, argvars)
                res = func(urlargs=urlargs, **argvars)          # MAIN PART - run method and collect result
            else:
                if verbose: print "%s.dispatch unimplemented: %s" % (self.__class__.__name__, req)
                raise HTTPdispatcherException(req=req)  # Will be caught in MyHTTPRequestHandler._dispatch
            if verbose: print "_dispatch:Result=",res
            # Send the content-type
            self.send_response(200)  # Send an ok response
            self.send_header('Content-type', res.get("Content-type","application/octet-stream"))
            data = res.get("data","")
            if data:
                if isinstance(data, (dict, list, tuple)):    # Turn it into JSON
                    data = dumps(data)
                elif hasattr(data, "dumps"):
                    data = dumps(data)
                if not isinstance(data, basestring):
                    print data
                    # Raise an exception - will not honor the status already sent, but this shouldnt happen as coding
                    # error in the dispatched function if it returns anything else
                    raise ToBeImplementedException(name=self.__class__.__name__+"._dispatch for return data "+data.__class__.__name__)
                self.send_header('Content-Length', str(len(data)) if data else 0)
            self.end_headers()
            if data:
                if isinstance(data, unicode):
                    data = data.encode("utf-8") # Needed to make sure any unicode in data converted to utf8 BUT wont work for intended binary
                self.wfile.write(data)                   # Write content of result if applicable
        except (TransportBlockNotFound, TransportFileNotFound, DWEBMalformedURLException) as e:         # Gentle errors, entry in log is sufficient (note line is app specific)
            self.send_error(e.httperror, str(e))    # Send an error response
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
                # This route is taken by browsers using jquery as no easy wayto uploadwith octet-stream
                # If its just singular like data="foo" then return single values else (unusual) lists
                length = int(self.headers['content-length'])
                postvars = { p: (q[0] if (isinstance(q, list) and len(q)==1) else q) for p,q in parse_qs(
                    self.rfile.read(length),
                    keep_blank_values=1).iteritems() }
            elif ctype == 'application/octet-stream':  # Block sends this
                length = int(self.headers['content-length'])
                postvars = {"data": self.rfile.read(length)}
            elif ctype == 'application/json':
                length = int(self.headers['content-length'])
                postvars = {"data": loads(self.rfile.read(length))}
                #raise ToBeImplementedException(name="do_POST:application/json")
            else:
                postvars = {}
            self._dispatch(**postvars)
        #except Exception as e:
        except ZeroDivisionError as e:  # Uncomment this to actually throw exception
            httperror = e.httperror if hasattr(e, "httperror") else 500
            self.send_error(httperror, str(e))  # Send an error response


def exposed(func):
    def wrapped(*args, **kwargs):
        result = func(*args, **kwargs)
        return result

    wrapped.exposed = True
    return wrapped
