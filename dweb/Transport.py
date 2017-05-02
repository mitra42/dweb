# encoding: utf-8
from abc import ABCMeta, abstractmethod

from misc import ToBeImplementedException, MyBaseException

class TransportBlockNotFound(MyBaseException):
    httperror = 404
    msg = "{hash} not found"

class TransportURLNotFound(MyBaseException):
    httperror = 404
    msg = "{url}, {options} not found"

class TransportFileNotFound(MyBaseException):
    httperror = 404
    msg = "{file} not found"

class TransportPathNotFound(MyBaseException):
    httperror = 404
    msg = "{path} not found for obj {hash}"

class TransportUnrecognizedCommand(MyBaseException):
    httperror = 500
    msg = "Class {classname} doesnt have a command {command}"


class Transport(object):
    """
    The minimal transport layer implements 5 primitives:
    rawfetch(hash) -> bytes: To retrieve data
    rawlist(keyhash) -> [ (datahash, date, keyhash)* ]
    rawreverse(datahash) -> [ (datahash, date, keyhash)* ]
    rawstore(data) -> hash: Store data
    rawadd(datahash, date, keyhash) -> Raw add to list(keyhash) and reverse(datahash)

    These are expanded here to:
    fetch(command, cls, hash, path)
    list(command, cls, hash, path) = list.command([cls(l).path for l in rawlist(hash)])
    store(command, cls, hash, path, data) = fetch(cls, hash, path).command(data) || rawstore(data)  #TODO unsure of this
    add(obj, date, signature, signedby) = rawadd(obj._hash, date, signature, signedby ) #TODO could take "key" 

    Either the raw, or cooked functions can be subclassed
    """
    def __init__(self, **options):
        """
        :param options:
        """
        raise ToBeImplementedException(name=cls.__name__+".__init__")

    @classmethod
    def setup(cls, **options):
        """
        Called to deliver a transport instance of a particular class

        :param options: Options to subclasses init method
        :return: None
        """
        raise ToBeImplementedException(name=cls.__name__+".setup")

    def _lettertoclass(self, abbrev):
        from ServerHTTP import LetterToClass
        return LetterToClass.get(abbrev, None)

    def info(self, **options):
        raise ToBeImplementedException(name=cls.__name__+".info")

    def rawfetch(self, hash=None, verbose=False, **options):
        """
        Fetch data from a hash and return as a (binary) string

        :param hash:
        :return: str
        """
        raise ToBeImplementedException(name=cls.__name__+".rawfetch")

    def fetch(self, command=None, cls=None, hash=None, path=None, verbose=False, **options):
        """
        More comprehensive fetch function, can be sublassed either by the objects being fetched or the transport.
        Exceptions: TransportPathNotFound, TransportUnrecognizedCommand

        :param command: Command to be performed on the retrieved data (e.g. content, or size)
        :param cls:     Class of object being returned, if None will return a str
        :param hash:    Hash of object to retrieve
        :param path:    Path within object represented by hash
        :param verbose:
        :param options: Passed to command, NOT passed to subcalls as for example mucks up sb.__init__ by dirtying - this might be reconsidered
        :return:
        """
        if verbose: print "Transport.fetch command=%s cls=%s hash=%s path=%s options=%s" % (command, cls, hash, path, options)
        if cls:
            if isinstance(cls, basestring):  # Handle abbreviations for cls
                cls = self._lettertoclass(cls)
            obj = cls(hash=hash, verbose=verbose).fetch(verbose=verbose)
            # Can't pass **options to cls as disrupt sb.__init__ by causing dirty
            # Not passing **options to fetch, but probably could
        else:
            obj = self.rawfetch(hash, verbose=verbose)   # Not passing **options, probably could but not used
        #if verbose: print "Transport.fetch obj=",obj
        if path:
            obj = obj.path(path, verbose=verbose)   # Not passing **options as ignored, but probably could
            #TODO handle not found exception
            if not obj:
                raise TransportPathNotFound(path=path, hash=hash)
        if not command:
            return obj
        else:
            if not cls:
                raise TransportUnrecognizedCommand(command=command, classname="None")
            func = getattr(obj, command, None)
            if not func:
                raise TransportUnrecognizedCommand(command=command, classname=cls.__name__)
            return func(verbose=verbose, **options)

    def rawlist(self, hash=None, verbose=False, **options):
        raise ToBeImplementedException(name=cls.__name__+".rawlist")

    def list(self, command=None, cls=None, hash=None, path=None, verbose=False, **options):
        """

        :param command: if found:  list.commnd(list(cls, hash, path)
        :param cls: if found (cls(l) for l in list(hash)
        :param hash:    Hash of list to look up - usually hash of private key of signer
        :param path:    Ignored for now, unclear how applies
        :param verbose:
        :param options:
        :return:
        """

        res = rawlist(hash, verbose=verbose, **options)
        if cls:
            if isinstance(cls, basestring): # Handle abbreviations for cls
                cls = self._lettertoclass(cls)
            res = [ cls(l) for l in res ]
        if command:
            func = getattr(CommonList, command, None)   #TODO May not work, might have to turn res into CommonList first
            if not func:
                raise TransportUnrecognizedCommand(command=command, classname=cls.__name__)
            res = func(res, verbose=verbose, **options)
        return res

    def rawreverse(self, hash=None, verbose=False, **options):
        raise ToBeImplementedException(name=cls.__name__+".rawreverse")


    def reverse(self, command=None, cls=None, hash=None, path=None, verbose=False, **options):
        """

        :param command: if found:  reverse.commnd(list(cls, hash, path)
        :param cls: if found (cls(l) for l in reverse(hash)
        :param hash:    Hash of reverse to look up - usually hash of data signed
        :param path:    Ignored for now, unclear how applies
        :param verbose:
        :param options:
        :return:
        """

        res = rawreverse(hash, verbose=verbose, **options)
        if cls:
            if isinstance(cls, basestring): # Handle abbreviations for cls
                cls = self._lettertoclass(cls)
            res = [ cls(l) for l in res ]
        if command:
            func = getattr(self, command, None)
            if not func:
                raise TransportUnrecognizedCommand(command=command, classname=cls.__name__)
            res = func(res, verbose=verbose, **options)
        return res

    def rawstore(self, data=None, verbose=False, **options):
        raise ToBeImplementedException(name=cls.__name__+".rawstore")

    def store(self, command=None, cls=None, hash=None, path=None, data=None, verbose=False, **options):
        #store(command, cls, hash, path, data, options) = fetch(cls, hash, path, options).command(data|data._data, options)
        #store(hash, data)
        if not isinstance(data, basestring):
            data = data._data
        if command:
            # TODO not so sure about this production, document any uses here if there are any
            obj = self.fetch(command=None, cls=None, hash=hash, path=path, verbose=verbose, **options)
            return obj.command(data=data, verbose=False, **options)
        else:
            return self.rawstore(data=data, verbose=verbose, **options)

    def rawadd(self, hash=None, date=None, signature=None, signedby=None, verbose=False, **options):
        raise ToBeImplementedException(name=cls.__name__+".rawadd")

    def add(self, hash=None, date=None, signature=None, signedby=None, verbose=False, obj=None, **options ):
        #add(datahash, sig, date, keyhash)
        if (obj and not hash):
            hash = obj._hash
        return self.rawadd(hash=hash, date=date, signature=signature, signedby=signedby, verbose=verbose, **options)

    def _add_value(self, hash=None, date=None, signature=None, signedby=None, verbose=False, **options ):
        from CryptoLib import CryptoLib
        store = {"hash": hash, "date": date, "signature": signature, "signedby": signedby}
        return CryptoLib.dumps(store)
