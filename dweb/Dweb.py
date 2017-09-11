# encoding: utf-8
from Crypto.PublicKey import RSA
from sys import version as python_version
import itertools
if python_version.startswith('3'):
    from urllib.parse import urlparse
else:
    from urlparse import urlparse        # See https://docs.python.org/2/library/urlparse.html

#TODO-BACKPORT - review this file

"""
A collection of top level tools for demonstrating and debugging and giving a low complexity way to interact.
"""

class Dweb(object):
    """
    Top level application class for Dweb
    """
    transport = None    # These are essential global variables inside Dweb, usually set one at starting #TODO-BACKPORT obsolete, replaced by transportpriority and mapping url->transport
    keychains = []      #
    transports = {}
    transportpriority = []

    @classmethod
    def transport(cls, url=None): #TODO-REL4-API
        """
        Pick between associated transports based on URL

        url     URL or string that can be parsed into a URL
        returns subclass of Transport that can support this kind of URL or undefined if none.
        """
        #TODO-efficiency, could parse URL once at higher level and pass URL down
        if isinstance(url, basestring ):
            url = urlparse(url);    # For efficiency, only parse once.
        # Construct: next(itertools.ifilter(lambda..., arr),None)   returns the first element in arr that passes lambda without testing rest
        return next(itertools.ifilter(lambda t: t.supports(url), cls.transportpriority),None) #First transport that can support this URL


# Some utilities
"""
# Not used, could delete, but might be useful in testing
def _print(*foos, **kwargs):
    import textwrap
    first = True
    width = kwargs.get("width", 120)
    for foo in foos:
        for line in textwrap.wrap(unicode(foo), width=width):
            print ("    " if not first else "") + line
            first=False
"""
def consolearr(arr):
    if arr and len(arr) > 0:
        return str(len(arr)) + " items inc:" + str(arr[-1])
    else:
        return arr

#TODO-BACKPORT probably need table2class, mergeTypedArraysUnsafe