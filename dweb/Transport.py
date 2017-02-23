# encoding: utf-8
import hashlib
import base64
from abc import ABCMeta, abstractmethod

from misc import ToBeImplementedException

class Transport(object):
    """
    The Transport class provides the abstract interface to different ways to implement transport.
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

    def DHT_store(self, table, key, value, **options):
        """
        :param table: Name of table to store in e.g. "signatures"
        :param key:     Key to store under
        :param value:
        :param options:
        :return:
        """
        raise ToBeImplementedException(name=cls.__name__+".DHT_store")
