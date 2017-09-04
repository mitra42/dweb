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
    transport = None    # These are essential global variables inside Dweb, usually set one at starting #TODO-BACKPORT obsolete, replaced by transportpriority and mapping url->transport
    keychains = []      #
    transports = {}
    transportpriority = []

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

#TODO-BACKPORT probably need table2class, mergeTypedArraysUnsafe