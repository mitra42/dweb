# encoding: utf-8
from Crypto.PublicKey import RSA
#TODO-BACKPORT - review this file

"""
A collection of top level tools for demonstrating and debugging and giving a low complexity way to interact.

DO NOT RELY on these tools at this time, - dont import them into other files etc, but feel free to extend and edit.

use in Python sell by ...
from dweb.Dweb import Dweb
mnm = menmonicgen()     # Generate a set of random mnemonic words (remember these)
keychain(mnm)          # Create a keychain from the mnemonic, add it to my keychains
"""

class Dweb(object):
    """
    Top level application class for Dweb
    """
    transport = None    # These are essential global variables inside Dweb, usually set one at starting
    keychains = []      #

    @classmethod
    def settransport(cls, transportstring=None, transportclass=None, verbose=False, **transportoptions):
        """
        Setup the Transportable class with a particular transport, has both explicit and heuristic parameter choices

        :param transportclass: Subclass of Transport
        :param transportoptions: Dictionary of options
        :param transportstring: ? to report, "local" or "cache" for file system, "http" or "localhost", 4243  for HTTP locally
        :return:
        """
        from CommonBlock import Transportable
        from TransportHTTP import TransportHTTP
        from TransportLocal import TransportLocal

        if transportclass:  # Explicitly set class and setup
            cls.transport = transportclass.setup(verbose=verbose, **transportoptions)

        elif transportstring == "?":
            print cls.transport

        else:
            if transportstring == "local":
                serv = "../cache"
                port = None
            elif transportstring == "http":
                serv = u"localhost"
                #serv = u'192.168.1.156'
                port = 4243
            else:
                serv, port = transportstring.split(':')
            if port:
                cls.transport = TransportHTTP.setup(ipandport=(serv, port), verbose=verbose)
            else:
                cls.transport = TransportLocal.setup(dir=serv, verbose=verbose)
        if verbose: print "Transport set to", cls.transport

