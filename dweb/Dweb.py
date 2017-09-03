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


