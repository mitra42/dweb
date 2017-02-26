# encoding: utf-8
from Block import Block
from StructuredBlock import StructuredBlock
from MyHTTPServer import MyHTTPRequestHandler, exposed

class DwebHTTPRequestHandler(MyHTTPRequestHandler):
    defaultipandport = ('localhost', 4243)
    #TODO get rid of exposed1, make @exposed set it
    #exposed1 = ["block", "store", "file", "DHT_store", "DHT_fetch"]

    @exposed
    def block(self, **kwargs):
        """
        Retrieve a block, Paired with TransportHTTP.block

        :param kwargs: { hash }
        :return: raw data from block
        """
        return { "Content-type": "appliction/octet-stream",
                 "data": Block.block(hash=kwargs["hash"])._data } # Should be raw data returned
    block.arglist=["hash"]

    @exposed
    def sblock(self, **kwargs):
        """
        Retrieve a block, Paired with TransportHTTP.block

        :param kwargs: { hash }
        :return: raw data from block
        """
        b = Block.block(hash=kwargs["hash"]) # Should be raw data returned
        return { "Content-type": 'text/json', "data": b._data }
    sblock.arglist=["hash"]

    @exposed
    def store(self, **kwargs):
        self._checkargs("store", ("data",), kwargs)
        hash = Block(kwargs["data"]).store()
        return { "Content-type": "appliction/octet-stream", "data": hash }
    store.arglist=["data"]

    @exposed
    def file(self, **kwargs):
        b = StructuredBlock.sblock(hash=kwargs["hash"])
        return b.__dict__
    file.arglist=["hash"]

    @exposed
    def DHT_store(self, **kwargs):
        """
        DHT_store has no higher level interpretation, so just pass to server's transport layer direct
        Once distributed, this will be clever, or rather ITS transport layer should be.

        :param kwargs: required: { table, key, value }
        :return:
        """
        kwargs["value"] = kwargs["data"]
        del kwargs["data"]
        return  { "Content-type": "appliction/octet-stream",
                  "data":  Block.transport.DHT_store(**kwargs)
                }
    DHT_store.arglist=["table", "key", "data"]

    @exposed
    def DHT_fetch(self, **kwargs):
        """
        DHT_fetch has no higher level interpretation, so just pass to server's transport layer direct
        Once distributed, this will be clever, or rather ITS transport layer should be.

        :param table: table to look up value in
        :param key: key to retrieve values for
        :return:
        """
        return { 'Content-type': 'text/json',
                 'data': Block.transport.DHT_fetch(**kwargs)
               }
    DHT_fetch.arglist=["table", "key"]

    @classmethod
    def HTTPToLocalGateway(cls):
        """
        DWeb HTTP server, all this one does is gateway from HTTP Transport to Local Transport, allowing calls to happen over net.
        One instance of this will be created for each request, so don't override __init__()
        Initiate with something like: DwebHTTPRequestHandler.serve_forever()

        :return: Never Returns
        """
        from TransportLocal import TransportLocal # Avoid circular references
        Block.setup(TransportLocal, verbose=False, dir="../cache_http")  # HTTP server is storing locally
        cls.serve_forever(verbose=False)    # Uses defaultipandport
        #TODO-HTTP its printing log, put somewhere instead

if __name__ == "__main__":
    DwebHTTPRequestHandler.HTTPToLocalGateway() # Run local gateway

