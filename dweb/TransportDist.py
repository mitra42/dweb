# encoding: utf-8

from Transport import Transport, TransportFileNotFound
from TransportLocal import TransportLocal
from TransportDist_Peer import Node

"""
Highly experimental distributed layer for dWeb, just a proof of concept and place for experimentation.
"""
class TransportDist(Transport):
    """
    Subclass of Transport.
    Implements the raw primitives as reads and writes of file system.
    """

    def __init__(self, tl=None, **options):
        """
        Create a distirbuted transport object (use "setup" instead)

        :param options:
        """
        self.node = Node()
        self.tl = tl    # Connect to TransportLocal

    @classmethod
    def setup(cls, dir=None, **options):
        """
        Setup local transport to use dir
        Exceptions: TransportBlockNotFound if dir invalid

        :param dir:     Directory to use for storage
        :param options: Unused currently
        """
        if dir:
            tl = TransportLocal.setup(dir=dir, **options)   #TransportBlockNotFound if dir invalid
        else:
            tl = None
        #TODO-TX should probably create TransportLocal and pass to init
        return cls(tl=tl, **options)

    def rawfetch(self, hash, verbose=False, **options):
        """
        Fetch a block from the local file system and if that fails fetch from distributed and cache
        Exception: TransportFileNotFound if file doesnt exist

        :param hash:
        :param options:
        :return:
        """
        try:
            if self.tl.rawfetch(hash, verbose=verbose, **options)
        except TransportFileNotFound as e:
            #TODO-TX Fetch from remote
            XXX
            #Save locally
            self.tl.rawstore(data, verbose=verbose)
            return data

    def _rawlistreverse(self, subdir=None, hash=None, verbose=False, **options):
        """
        Retrieve record(s) matching a hash (usually the hash of a key), in this case from a local directory
        Exception: IOError if file doesnt exist

        :param hash: Hash in table to be retrieved
        :return: list of dictionaries for each item retrieved
        """
        #TODO look local, ask remote
        pass

    def rawlist(self, hash, verbose=False, **options):
        """
        Retrieve record(s) matching a hash (usually the hash of a key), in this case from a local directory
        Exception: IOError if file doesnt exist

        :param hash: Hash in table to be retrieved
        :return: list of dictionaries for each item retrieved
        """
        #TODO - via _rawlistreverse
        pass

    def rawreverse(self, hash, verbose=False, **options):

        """
        Retrieve record(s) matching a hash (usually the hash of a key), in this case from a local directory
        Exception: IOError if file doesnt exist

        :param hash: Hash in table to be retrieved
        :return: list of dictionaries for each item retrieved
        """
        #TODO - via _rawlistreverse
        pass

    def rawstore(self, data=None, verbose=False, **options):
        """
        Store the data locally
        Exception: TransportBlockNotFound if file doesnt exist

        :param data: opaque data to store
        :return: hash of data
        """
        #TODO - store local and pass to remote(s) based on algorithm
        pass

    if __name__ == '__main__':
        def rawadd(self, hash=None, date=None, signature=None, signedby=None, verbose=False, **options):
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
            #TODO - store local and pass to remote(s) based on algorithm
            pass

