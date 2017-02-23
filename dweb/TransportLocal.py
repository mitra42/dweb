# encoding: utf-8
import hashlib
import base64
from json import loads, dumps
from misc import json_default
#from abc import ABCMeta, abstractmethod

from Transport import Transport

class TransportLocal(Transport):
    """
    TransportLocal is a subclasss of Transport providing local file and sqlite storage to facilitate local testing.
    """
    def __init__(self, dir, options):
        #TODO check existance of dir
        #TODO check existance of expected subdirs (signature)
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
        hash = "SHA1B64URL:" + base64.urlsafe_b64encode(hashlib.sha1(data).digest())  # TODO-CRYPTO maybe not right hash function to use
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

    def DHT_store(self, table, key, value, verbose=False, **options):
        if verbose: print "TransportLocal.DHT_store",table,key,value
        if not isinstance(value, basestring):
            # Turn into a string if not already
            value = dumps(value, sort_keys=True, separators=(',', ':'), default=json_default)
        filepart = "SHA1B64URL:" + base64.urlsafe_b64encode(hashlib.sha1(key).digest())
        filename = "%s/%s/%s" % (self.dir, table, filepart)
        if verbose: print "DHT_store filename=",filename
        #TODO Check for directory existing and create if reqd
        f = open(filename, 'a')
        f.write(value)
        f.write("\n")
        f.close()

    def DHT_fetch(self, table, key, verbose=False, **options):
        if verbose: print "TransportLocal.DHT_fetch",table,key
        filepart = "SHA1B64URL:" + base64.urlsafe_b64encode(hashlib.sha1(key).digest())
        filename = "%s/%s/%s" % (self.dir, table, filepart)
        if verbose: print "DHT_store filename=",filename
        #TODO Check for directory existing and create if reqd
        f = open(filename, 'r')
        s = f.readlines()
        print "XXX@70",s
        f.close()
        return s
