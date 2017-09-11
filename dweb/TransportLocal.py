# encoding: utf-8
#from abc import ABCMeta, abstractmethod
import os   # For isdir and exists
from json import loads, dumps
from Transport import Transport, TransportFileNotFound
from KeyPair import KeyPair
from Dweb import Dweb
from sys import version as python_version
if python_version.startswith('3'):
    from urllib.parse import urlparse
else:
    from urlparse import urlparse        # See https://docs.python.org/2/library/urlparse.html


class TransportLocal(Transport):
    """
    Subclass of Transport.
    Implements the raw primitives as reads and writes of file system.
    """

    # urlschemes = ['http'] - subclasses as can handle all


    def __init__(self, options, verbose):
        """
        Create a transport object (use "setup" instead)
        |Exceptions: TransportFileNotFound if dir invalid, IOError other OS error (e.g. cant make directory)

        :param dir:
        :param options:
        """
        subdirs = "list", "reverse", "block"
        dir = options["local"]["dir"]
        if not os.path.isdir(dir):
            os.mkdir(dir)
            #raise TransportFileNotFound(file=dir)
        self.dir = dir
        for table in subdirs:
            dirname = "%s/%s" % (self.dir, table)
            if not os.path.isdir(dirname):
                os.mkdir(dirname)
        self.options = options

    def __repr__(self):
        return self.__class__.__name__ + " " + dumps(self.options)

    @classmethod
    def setup(cls, options, verbose):
        """
        Setup local transport to use dir
        Exceptions: TransportFileNotFound if dir invalid

        :param dir:     Directory to use for storage
        :param options: Unused currently
        """
        t = cls(options, verbose)
        Dweb.transports["local"] = t
        Dweb.transportpriority.append(t)
        return t


    #see other !ADD-TRANSPORT-COMMAND - add a function copying the format below

    def supports(self, url):
        return True         # Local can handle any kind of URL, since cached.

    def info(self, **options):
        return { "type": "local", "options": self.options }

    def _filename(self, subdir, multihash=None, verbose=False, **options):
        # Utility function to get filename to use for storage
        return "%s/%s/%s" % (self.dir, subdir, multihash)

    @staticmethod
    def _multihash(data=None, url=None):
        """
        Return a multihash (string of form Q....

        :param data:    optional - data to hash
        :param url:     url to pull multihash from (last part of path)
        :return:        string of form Q.... (base58 of multihash of sha256 of data)
        """
        if data:
            return KeyPair.multihashsha256_58(data)
        if url:
            if isinstance(url,basestring):
               url = urlparse(url)
            return url.path.split('/')[-1]

    def url(self, data=None, multihash=None): #TODO-API
        """
         Return an identifier for the data without storing

         :param data        string|Buffer data   arbitrary data
         :param multihash   string of form Q...
         :return string     valid id to retrieve data via rawfetch
         """

        if data:
            multihash = TransportLocal._multihash(data=data)
        return "local:/rawfetch/"+ multihash

    def rawfetch(self, url, verbose=False, **options):
        """
        Fetch a block from the local file system
        Exception: TransportFileNotFound if file doesnt exist

        :param url:
        :param options:
        :return:
        """
        multihash=self._multihash(url=url)
        filename = self._filename("block", multihash)
        try:
            if verbose: print "Opening" + filename
            with open(filename, 'rb') as file:
                content = file.read()
            if verbose: print "success"
            return content
        except IOError as e:
            raise TransportFileNotFound(file=filename)

    def _rawlistreverse(self, subdir=None, url=None, verbose=False, **options):
        """
        Retrieve record(s) matching a url (usually the url of a key), in this case from a local directory
        Exception: IOError if file doesnt exist

        :param url: Hash in table to be retrieved
        :return: list of dictionaries for each item retrieved
        """
        multihash=self._multihash(url=url)
        filename = self._filename(subdir, multihash=multihash, verbose=verbose, **options)
        try:
            f = open(filename, 'rb')
            s = [ loads(s) for s in f.readlines() ]
            f.close()
            return s
        except IOError as e:
            return []
            #Trying commenting out error, and returning empty array
            #raise TransportFileNotFound(file=filename)

    def rawlist(self, url, verbose=False, **options):
        """
        Retrieve record(s) matching a url (usually the url of a key), in this case from a local directory
        Exception: IOError if file doesnt exist

        :param url: URL to be retrieved
        :return: list of dictionaries for each item retrieved
        """
        if verbose: print "TransportLocal:rawlist", url
        return self._rawlistreverse(subdir="list", url=url, verbose=False, **options)


    def rawreverse(self, url, verbose=False, **options):

        """
        Retrieve record(s) matching a url (usually the url of a key), in this case from a local directory
        Exception: IOError if file doesnt exist

        :param url: Hash in table to be retrieved
        :return: list of dictionaries for each item retrieved
        """
        return self._rawlistreverse(subdir="reverse", url=url, verbose=False, **options)

    def rawstore(self, data=None, verbose=False, **options):
        """
        Store the data locally
        Exception: TransportFileNotFound if file doesnt exist

        :param data: opaque data to store
        :return: url of data
        """
        assert data is not None # Its meaningless (or at least I think so) to store None (empty string is meaningful)
        multihash = self._multihash(data=data)
        filename = self._filename("block", multihash, verbose=verbose, **options)
        try:
            f = open(filename, 'wb')
            f.write(data)
            f.close()
        except IOError as e:
            raise TransportFileNotFound(file=filename)
        url = self.url(multihash=multihash)
        return url


    def rawadd(self, url=None, date=None, signature=None, signedby=None, verbose=False, subdir=None, **options):    #TODO-API
        """
        Store a signature in a pair of DHTs
        Exception: IOError if file doesnt exist

        :param url:        url to store under
        :param date:
        :param signature:
        :param signedby:
        :param subdir: Can select list or reverse to store only one or both halfs of the list. This is used in TransportDistPeer as the two halfs are stored in diffrent parts of the DHT
        :param verbose:
        :param options:
        :return:
        """
        subdir = subdir or ("list","reverse")
        if verbose: print "TransportLocal.rawadd",  url, date, signature, signedby, subdir, options
        value = self._add_value(url=url, date=date, signature=signature, signedby=signedby, verbose=verbose, **options) + "\n"
        if "list" in subdir:
            multihash = self._multihash(url=signedby)
            filenameL = self._filename("list", multihash=multihash, verbose=verbose, **options)   # List of things signedby
            try:
                with open(filenameL, 'ab') as f:
                    f.write(value)
            except IOError as e:
                raise TransportFileNotFound(file=filenameL)
        if "reverse" in subdir:
            multihash = self._multihash(url=url)
            filenameR = self._filename("reverse", multihash=multihash, verbose=verbose, **options)    # Lists that this object is on
            try:
                with open(filenameR, 'ab') as f:
                    f.write(value)
            except IOError as e:
                raise TransportFileNotFound(file=filenameR)
