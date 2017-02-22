# encoding: utf-8
import hashlib
import base64
from abc import ABCMeta, abstractmethod

from misc import ToBeImplementedException

"""
The Transport class provides the abstract interface to different ways to implement transport.
"""

class Transport(object):
    """
    Test to make sure this gets to docs
    """
    __metaclass__ = ABCMeta

    def __init__(self, blah):
        """
        Use blah
        :param blah:
        """

    #@abstractclassmethod   # Only works in Python 3.3
    @classmethod
    def block(self, hash, **options):
        """
        Fetch a block
        :param hash: multihash of block to return
        :return:
        """
        raise ToBeImplementedException(name=cls.__name__+".block")

    # @abstractclassmethod   # Only works in Python 3.3
    @classmethod
    def setup(cls, **options):
        """
        :param options: Options to subclasses init method
        :return: None
        """
        raise ToBeImplementedException(name=cls.__name__+".setup")

class TransportLocal(Transport):
    """
    TransportLocal is a subclasss of Transport providing local file and sqlite storage to facilitate local testing.
    """
    def __init__(self, dir, options):
        #TODO check existance of dir
        self.dir = dir
        self.options = options

    @classmethod
    def setup(cls, **options):
        return cls(options["dir"], options)

    def store(self, data):
        """
        Store the data locally
        :param data: opaque data to store
        :return: hash of data
        """
        hash = "SHA1B64URL:" + base64.urlsafe_b64encode(hashlib.sha1(data).digest())  # TODO maybe not right hash function to use
        filename = "%s/%s" % (self.dir, hash)
        f = open(filename, 'w')
        f.write(data)
        f.close()
        return hash

    def block(self, hash, verbose=False, **options):
        """
        Fetch a block from the local file system
        :param hash:
        :param options:
        :return:
        """
        file = "%s/%s" % (self.dir, hash)
        if verbose: print "Opening" + file
        return open(file).read()
