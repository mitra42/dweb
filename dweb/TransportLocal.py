# encoding: utf-8
#from abc import ABCMeta, abstractmethod
import os   # For isdir and exists
from json import loads
from CryptoLib import CryptoLib
from Transport import Transport, TransportBlockNotFound

class TransportLocal(Transport):
    """
    TransportLocal is a subclasss of Transport providing local file and sqlite storage to facilitate local testing.
    """

    tables = "mb", "signed", "b", "sb", "signedby", "mbm"

    def __init__(self, dir=None, **options):
        """
        Create a transport object (use "setup" instead)
        |Exceptions: TransportBlockNotFound if dir invalid, IOError other OS error (e.g. cant make directory)

        :param dir:
        :param options:
        """
        if not os.path.isdir(dir):
            raise TransportBlockNotFound(hash=dir)
        self.dir = dir
        for table in self.tables:
            dirname = "%s/%s" % (self.dir, table)
            if not os.path.isdir(dirname):
                os.mkdir(dirname)
        self.options = options

    def _filename(self, table, hash=None, key=None, verbose=False, **options):
        file = hash or CryptoLib.urlhash(key, verbose=verbose, **options)
        return "%s/%s/%s" % (self.dir, table, file)

    @classmethod
    def setup(cls, dir=None, **options):
        """
        Setup local transport to use dir
        Exceptions: TransportBlockNotFound if dir invalid

        :param dir:     Directory to use for storage
        :param options: Unused currently
        """
        return cls(dir=dir, **options)

    def store(self, table=None, data=None, verbose=False, **options):
        """
        Store the data locally
        Exception: TransportBlockNotFound if file doesnt exist

        :param data: opaque data to store
        :return: hash of data
        """
        hash = CryptoLib.urlhash(data)
        filename = self._filename(table, hash, verbose=verbose, **options)
        try:
            f = open(filename, 'wb')
            f.write(data)
            f.close()
        except IOError as e:
            raise TransportBlockNotFound(hash=hash)
        return hash

    def block(self, table, hash, verbose=False, **options):
        """
        Fetch a block from the local file system
        Exception: IOError if file doesnt exist

        :param hash:
        :param options:
        :return:
        """
        try:
            filename = self._filename(table, hash)
            if verbose: print "Opening" + filename
            with open(filename, 'rb') as file:
                content = file.read()
            return content
        except IOError as e:
            raise TransportBlockNotFound(hash=hash)

    def add(self, table=None, key=None, value=None, verbose=False, **options):
        """
        Store in a DHT
        Exception: IOError if file doesnt exist

        :param table:   Table to store in
        :param key:     Key to store under
        :param value:   Value - usually a dict - to store.
        :param verbose: Report on activity
        :param options:
        :return:
        """
        if verbose: print "TransportLocal.add", table, key, value
        filename = self._filename(table, key=key, verbose=verbose, **options)
        try:
            if not isinstance(value, basestring):
                # Turn into a string if not already
                value = CryptoLib.dumps(value)
            with open(filename, 'ab') as f:
                f.write(value)
                f.write("\n")
        except IOError as e:
            raise TransportBlockNotFound(hash=filename)

    def list(self, table=None, key=None, hash=None, verbose=False, **options):
        """
        Retrieve record(s) matching a key, in this case from a local directory
        Exception: IOError if file doesnt exist

        :param table: Table to look for key in
        :param key: Key to be retrieved
        :return: list of dictionaries for each item retrieved
        """
        if verbose: print "TransportLocal.list", table, key
        if table in ("mb", "mbm"): table = "signedby"            # Look for Signatures for mb table in signedby table
        filename = self._filename(table, key=key, hash=hash, verbose=verbose, **options)
        try:
            f = open(filename, 'rb')
            s = [ loads(s) for s in f.readlines() ]
            f.close()
            return s
        except IOError as e:
            raise TransportBlockNotFound(hash=filename)
