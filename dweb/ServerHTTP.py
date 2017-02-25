# encoding: utf-8
from Block import Block
from StructuredBlock import StructuredBlock
from MyHTTPServer import MyHTTPdispatcher, MyHTTPRequestHandler

class DwebDispatcher(MyHTTPdispatcher):
    exposed = ["block", "store", "file", "DHT_store", "DHT_fetch"]

    @staticmethod
    def block(**kwargs):
        """
        Retrieve a block, Paired with TransportHTTP.block

        :param kwargs: { hash }
        :return: raw data from block
        """
        verbose = kwargs.get("verbose", False)
        if verbose: print "DwebDispatcher.block", kwargs
        MyHTTPdispatcher._checkargs("store", ("hash",), kwargs)
        b = Block.block(hash=kwargs["hash"]) # Should be raw data returned #TODO-BLOCK will return as block, maybe not what wanted
        return { "Content-type": "appliction/octet-stream", "data": b._data }

    @staticmethod
    def sblock(**kwargs):
        """
        Retrieve a block, Paired with TransportHTTP.block

        :param kwargs: { hash }
        :return: raw data from block
        """
        verbose = kwargs.get("verbose", False)
        if verbose: print "DwebDispatcher.block", kwargs
        MyHTTPdispatcher._checkargs("store", ("hash",), kwargs)
        b = Block.block(hash=kwargs["hash"]) # Should be raw data returned #TODO-BLOCK will return as block, maybe not what wanted
        return { "Content-type": 'text/json', "data": b._data }

    @staticmethod
    def store(**kwargs):
        verbose = kwargs.get("verbose", False)
        if verbose: print "DwebDispatcher.store", kwargs
        MyHTTPdispatcher._checkargs("store", ("data",), kwargs)
        hash = Block(kwargs["data"]).store()
        if verbose: print "DwebDispatcher.store returning:", hash
        return { "Content-type": "appliction/octet-stream", "data": hash }

    @staticmethod
    def file(**kwargs):
        verbose = kwargs.get("verbose", False)
        verbose=True
        if verbose: print "DwebDispatcher.file", kwargs
        MyHTTPdispatcher._checkargs("file", ("hash",), kwargs)
        b = StructuredBlock.sblock(hash=kwargs["hash"])
        if verbose: print "DwebDispatcher.file returning:", b
        return b.__dict__     # TODO - make it read headers from b._data

    @staticmethod
    def DHT_store(**kwargs):
        """
        DHT_store has no higher level interpretation, so just pass to server's transport layer direct
        Once distributed, this will be clever, or rather ITS transport layer should be.

        :param kwargs: required: { table, key, value }
        :return:
        """
        verbose = kwargs.get("verbose", False)
        if verbose: print "DwebDispatcher.DHT_store",kwargs
        MyHTTPdispatcher._checkargs("DHT_store", ("table", "key", "data"), kwargs)
        kwargs["value"] = kwargs["data"]
        del kwargs["data"]
        return  { "Content-type": "appliction/octet-stream",
                  "data":  Block.transport.DHT_store(**kwargs)
                }



    @staticmethod
    def DHT_fetch(**kwargs):
        """
        DHT_fetch has no higher level interpretation, so just pass to server's transport layer direct
        Once distributed, this will be clever, or rather ITS transport layer should be.

        :param table: table to look up value in
        :param key: key to retrieve values for
        :return:
        """
        verbose = kwargs.get("verbose", False)
        if verbose: print "DwebDispatcher.DHT_fetch", kwargs
        MyHTTPdispatcher._checkargs("DHT_store", ("table", "key"), kwargs)
        return { 'Content-type': 'text/json',
                 'data': Block.transport.DHT_fetch(**kwargs)
               }



class DwebHTTPRequestHandler(MyHTTPRequestHandler):
    """
    DWeb HTTP server, all this one does is gateway from HTTP Transport to Local Transport, allowing calls to happen over net.
    One instance of this will be created for each request, so don't override __init__()

    Initiate with something like: DwebHTTPRequestHandler.serve_forever()
    """
    defaultdispatchclass = DwebDispatcher
    defaultipandport = ('localhost', 4243)

    @classmethod
    def HTTPToLocalGateway(cls):
        """
        Launch a gateway that answers on HTTP and forwards to Local

        :return: Never Returns
        """
        from TransportLocal import TransportLocal # Avoid circular references
        Block.setup(TransportLocal, verbose=False, dir="../cache_http")  # HTTP server is storing locally
        cls.serve_forever(verbose=False)    # Uses defaultipandport and defaultdispatchclass
        #TODO-HTTP its printing log, put somewhere instead

if __name__ == "__main__":
    DwebHTTPRequestHandler.HTTPToLocalGateway() # Run local gateway

