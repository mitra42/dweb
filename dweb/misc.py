# encoding: utf-8
from datetime import datetime

#TODO-BACKPORT - move exceptions to Errors.py

class MyBaseException(Exception):
    """
    Base class for Exceptions

    msgargs Arguments that slot into msg
    __str__ Returns msg expanded with msgparms
    """
    errno=0
    httperror = 500         # See BaseHTTPRequestHandler for list of errors
    msg="Generic Model Exception"   #: Parameterised string for message
    def __init__(self, **kwargs):
        self.msgargs=kwargs # Store arbitrary dict of message args (can be used ot output msg from template

    def __str__(self):
        try:
            return self.msg.format(**self.msgargs)
        except:
            return self.msg+" "+unicode(self.msgargs)


class ToBeImplementedException(MyBaseException):
    """
    Raised when some code has not been implemented yet
    """
    httperror = 501
    msg = "{name} needs implementing"


class IntentionallyUnimplementedException(MyBaseException):
    """
    Raised when some code has not been implemented yet
    """
    httperror = 501
    msg = "Intentionally not implemented: {message}"

class AssertionFail(MyBaseException):
    """
    Raised when something that should be true isn't - usually a coding failure or some change not propogated fully
    """
    httperror = 500
    msg = "{message}"

class ForbiddenException(MyBaseException):
    httperror = 403     # Forbidden (Authentication won't help)
    msg = "Not allowed: {what}"

class ObsoleteException(MyBaseException):
    httperror = 500     # Forbidden (Authentication won't help)
    msg = "Coding error: The function {function} is obsolete hint:{hint}"


def _print(*foos, **kwargs):
    import textwrap
    first = True
    width = kwargs.get("width", 120)
    for foo in foos:
        for line in textwrap.wrap(unicode(foo), width=width):
            print ("    " if not first else "") + line
            first=False

