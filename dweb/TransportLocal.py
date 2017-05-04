# encoding: utf-8
#from abc import ABCMeta, abstractmethod
import os   # For isdir and exists
from json import loads
from CryptoLib import CryptoLib
from Transport import Transport, TransportFileNotFound

class TransportLocal(Transport):
    """
    Subclass of Transport.
    Implements the raw primitives as reads and writes of file system.
    """

    def __init__(self, dir=None, **options):
        """
        Create a transport object (use "setup" instead)
        |Exceptions: TransportFileNotFound if dir invalid, IOError other OS error (e.g. cant make directory)

        :param dir:
        :param options:
        """
        subdirs = "list", "reverse", "block"

        if not os.path.isdir(dir):
            os.mkdir(dir)
            #raise TransportFileNotFound(file=dir)
        self.dir = dir
        for table in subdirs:
            dirname = "%s/%s" % (self.dir, table)
            if not os.path.isdir(dirname):
                os.mkdir(dirname)
        self.options = options

    @classmethod
    def setup(cls, dir=None, **options):
        """
        Setup local transport to use dir
        Exceptions: TransportFileNotFound if dir invalid

        :param dir:     Directory to use for storage
        :param options: Unused currently
        """
        return cls(dir=dir, **options)

    #see other !ADD-TRANSPORT-COMMAND - add a function copying the format below

    def info(self, **options):
        return { "type": "local", "dir": self.dir }

    def _filename(self, subdir, hash=None, key=None, verbose=False, **options):
        # key now obsoleted
        file = hash or CryptoLib.Curlhash(key, verbose=verbose, **options)
        return "%s/%s/%s" % (self.dir, subdir, file)

    def rawfetch(self, hash, verbose=False, **options):
        """
        Fetch a block from the local file system
        Exception: TransportFileNotFound if file doesnt exist

        :param hash:
        :param options:
        :return:
        """
        filename=None
        filename = self._filename("block", hash)
        try:
            if verbose: print "Opening" + filename
            with open(filename, 'rb') as file:
                content = file.read()
            if verbose: print "success"
            return content
        except IOError as e:
            raise TransportFileNotFound(file=filename)

    def _rawlistreverse(self, subdir=None, hash=None, verbose=False, **options):
        """
        Retrieve record(s) matching a hash (usually the hash of a key), in this case from a local directory
        Exception: IOError if file doesnt exist

        :param hash: Hash in table to be retrieved
        :return: list of dictionaries for each item retrieved
        """
        filename = self._filename(subdir, hash=hash, verbose=verbose, **options)
        try:
            f = open(filename, 'rb')
            s = [ loads(s) for s in f.readlines() ]
            f.close()
            return s
        except IOError as e:
            raise TransportFileNotFound(file=filename)

    def rawlist(self, hash, verbose=False, **options):
        """
        Retrieve record(s) matching a hash (usually the hash of a key), in this case from a local directory
        Exception: IOError if file doesnt exist

        :param hash: Hash in table to be retrieved
        :return: list of dictionaries for each item retrieved
        """
        if verbose: print "TransportLocal:rawlist", hash
        return self._rawlistreverse(subdir="list", hash=hash, verbose=False, **options)


    def rawreverse(self, hash, verbose=False, **options):

        """
        Retrieve record(s) matching a hash (usually the hash of a key), in this case from a local directory
        Exception: IOError if file doesnt exist

        :param hash: Hash in table to be retrieved
        :return: list of dictionaries for each item retrieved
        """
        return self._rawlistreverse(subdir="reverse", hash=hash, verbose=False, **options)

    def rawstore(self, data=None, verbose=False, **options):
        """
        Store the data locally
        Exception: TransportFileNotFound if file doesnt exist

        :param data: opaque data to store
        :return: hash of data
        """
        assert data is not None # Its meaningless (or at least I think so) to store None (empty string is meaningful)
        hash = CryptoLib.Curlhash(data)
        filename = self._filename("block", hash, verbose=verbose, **options)
        try:
            f = open(filename, 'wb')
            f.write(data)
            f.close()
        except IOError as e:
            raise TransportFileNotFound(file=filename)
        return hash


    def rawadd(self, hash=None, date=None, signature=None, signedby=None, verbose=False, subdir=None, **options):
        """
        Store a signature in a pair of DHTs
        Exception: IOError if file doesnt exist

        :param hash:        hash to store under
        :param date:
        :param signature:
        :param signedby:
        :param verbose:
        :param options:
        :return:
        """
        subdir = subdir or ("list","reverse")
        if verbose: print "TransportLocal.rawadd",  hash, date, signature, signedby, subdir, options
        value = self._add_value(hash=hash, date=date, signature=signature, signedby=signedby, verbose=verbose, **options) + "\n"
        if "list" in subdir:
            filenameL = self._filename("list", hash=signedby, verbose=verbose, **options)   # List of things signedby
            try:
                with open(filenameL, 'ab') as f:
                    f.write(value)
            except IOError as e:
                raise TransportFileNotFound(file=filenameL)
        if "reverse" in subdir:
            filenameR = self._filename("reverse", hash=hash, verbose=verbose, **options)    # Lists that this object is on
            try:
                with open(filenameR, 'ab') as f:
                    f.write(value)
            except IOError as e:
                raise TransportFileNotFound(file=filenameR)
