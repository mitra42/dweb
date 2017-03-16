# encoding: utf-8
from abc import ABCMeta, abstractmethod

from misc import ToBeImplementedException, MyBaseException

class TransportBlockNotFound(MyBaseException):
    httperror = 404
    msg = "{table} {hash} not found"

class TransportURLNotFound(MyBaseException):
    httperror = 404
    msg = "{url}, {options} not found"

class TransportFileNotFound(MyBaseException):
    httperror = 404
    msg = "{file} not found"

class Transport(object):
    """
    The Transport class provides the abstract interface to different ways to implement transport.
    """
    #__metaclass__ = ABCMeta

    def __init__(self, **options):
        """
        :param options:
        """
        pass

    # @abstractclassmethod   # Only works in Python 3.3
    @classmethod
    def setup(cls, **options):
        """
        Called to deliver a transport instance of a particular class

        :param options: Options to subclasses init method
        :return: None
        """
        raise ToBeImplementedException(name=cls.__name__+".setup")

    #@abstractmethod
    def store(self, data=None):
        """
        Store the data locally

        :param data: opaque data to store
        :return: hash of data
        """
        #TODO-RELATIVE may need to add relative paths, but haven't found a use case yet
        raise ToBeImplementedException(name=cls.__name__+".store")

    #@abstractclassmethod   # Only works in Python 3.3
    def block(self, hash, **options):
        """
        Fetch a block

        :param hash: multihash of block to return
        :return:
        """
        #TODO-RELATIVE may need to add relative paths, but haven't found a use case yet
        raise ToBeImplementedException(name=cls.__name__+".block")

    def add(self, key=None, value=None, **options):
        """
        Store in a DHT

        :param table:   Table to store in
        :param key:     Key to store under
        :param value:   Value - usually a dict - to store.
        :param verbose: Report on activity
        :param options:
        :return:
        """
        #TODO-RELATIVE may need to add relative paths, but haven't found a use case yet
        raise ToBeImplementedException(name=cls.__name__+".add")

    def list(self, hash=None, verbose=False, **options):
        """
        Method that should always be subclassed to retrieve record(s) matching a key

        :param table: Table to look for key in
        :param key: Key to be retrieved
        :return: list of dictionaries for each item retrieved
        """
        raise ToBeImplementedException(name=self.__class__.__name__+".list")
        #TODO-RELATIVE may need to add relative paths, but haven't found a use case yet

    # ===== Utility functions for use by any subclass =======

    def _add_value(self, hash=None, date=None, signature=None, signedby=None, verbose=False, **options ):
        from CryptoLib import CryptoLib
        store = {"hash": hash, "date": date, "signature": signature, "signedby": signedby}
        return CryptoLib.dumps(store)


