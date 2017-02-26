# encoding: utf-8
#from abc import ABCMeta, abstractmethod
from json import loads
from CryptoLib import CryptoLib
from Transport import Transport

class TransportLocal(Transport):
    """
    TransportLocal is a subclasss of Transport providing local file and sqlite storage to facilitate local testing.
    """
    def __init__(self, dir=None, **options):
        #TODO check existance of dir
        #TODO check existance of expected subdirs (signature)
        self.dir = dir
        self.options = options

    @classmethod
    def setup(cls, dir=None, **options):
        return cls(dir=dir, **options)

    def store(self, data):
        """
        Store the data locally

        :param data: opaque data to store
        :return: hash of data
        """
        hash = CryptoLib.urlhash(data)
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

    def _DHT_filename(self, table, key, verbose=False, **options):
        """
        Return a Filesystem depenent location for the key, depending on self.dir

        :param table: Table name to store it in (e.g. signedby)
        :param key: Key to store (any length, any characters)
        :return: Filesystem safe name for key
        """
        filename = "%s/%s/%s" % (self.dir, table, CryptoLib.urlhash(key, verbose=verbose, **options))
        if verbose: print "DHT filename=",filename
        #TODO Check for directory existing and create if reqd
        return filename

    def DHT_store(self, table=None, key=None, value=None, verbose=False, **options):
        """
        Store in a DHT

        :param table:   Table to store in
        :param key:     Key to store under
        :param value:   Value - usually a dict - to store.
        :param verbose: Report on activity
        :param options:
        :return:
        """
        if verbose: print "TransportLocal.DHT_store",table,key,value
        if not isinstance(value, basestring):
            # Turn into a string if not already
            value = CryptoLib.dumps(value)
        filename = self._DHT_filename(table, key, verbose=verbose, **options)
        f = open(filename, 'a')
        f.write(value)
        f.write("\n")
        f.close()

    def DHT_fetch(self, table=None, key=None, verbose=False, **options):
        """
        Retrieve record(s) matching a key, in this case from a local directory

        :param table: Table to look for key in
        :param key: Key to be retrieved
        :return: list of dictionaries for each item retrieved
        """
        if verbose: print "TransportLocal.DHT_fetch",table,key
        filename = self._DHT_filename(table, key, verbose=verbose, **options)
        f = open(filename, 'r')
        s = [ loads(s) for s in f.readlines() ]
        f.close()
        return s
