# encoding: utf-8
from Block import Block
from StructuredBlock import StructuredBlock
from MutableBlock import MutableBlock
from MyHTTPServer import MyHTTPRequestHandler, exposed

class DwebHTTPRequestHandler(MyHTTPRequestHandler):
    defaultipandport = ('localhost', 4243)
    #TODO get rid of exposed1, make @exposed set it
    #exposed1 = ["block", "store", "file", "add", "list"]

    @exposed
    def block(self, table=None, hash=None, contenttype="application/octet-stream", **kwargs):
        """
        Retrieve a block, Paired with TransportHTTP.block
        Exceptions: TransportBlockNotFound if hash invalid

        :param kwargs: { hash }
        :return: raw data from block
        """
        return { "Content-type": contenttype,
                 "data": Block.block(hash=hash, table=table )._data} # Should be raw data returned
    block.arglist=["table", "hash"]

    @exposed
    def sblock(self, table=None, hash=None, **kwargs):
        """
        Retrieve a block, Paired with TransportHTTP.block

        :param kwargs: { hash }
        :return: raw data from block
        """
        sb = StructuredBlock.sblock(table=table, hash=hash)
        return { "Content-type": 'text/json', "data": sb._data }
    sblock.arglist=["table", "hash"]

    @exposed
    def store(self, table=None, **kwargs):
        hash = Block(kwargs["data"]).store(table=table)
        return { "Content-type": "appliction/octet-stream", "data": hash }
    store.arglist=["table", "data"]

    @exposed
    def file(self, table=None, hash=None, **kwargs):
        """
        file is specific to the URL gateway, knows about various kinds of directories, what stored there, and how to return to browser

        :param table: table holding content
        :param hash:  hash of content
        :param kwargs:
        :return: Dict suitable for looking for headers.
        """
        if table == "sb":
            b = StructuredBlock.sblock(table=table, hash=hash, **kwargs)
            return b.__dict__
        elif table == "mb": # Its a Mutable Block, fetch the sigs, then get latest, then fetch its content.
            mb = MutableBlock(hash=hash)
            mb.fetch()  # Get the sigs
            return mb._current._sb().__dict__  # Pass teh StructuredBlock which should have the Content-type field etc.
        else:
            raise ToBeImplementedException(name="file for table "+table)
    file.arglist=["table", "hash"]

    @exposed
    def add(self, **kwargs):
        """
        add has no higher level interpretation, so just pass to server's transport layer direct
        Once distributed, this will be clever, or rather ITS transport layer should be.

        :param kwargs: required: { table, key, value }
        :return:
        """
        kwargs["value"] = kwargs["data"]
        del kwargs["data"]
        return  { "Content-type": "appliction/octet-stream",
                  "data":  Block.transport.add(**kwargs)
                }
    add.arglist=["table", "key", "data"]

    @exposed
    def list(self, **kwargs):
        """
        list has no higher level interpretation, so just pass to server's transport layer direct
        Once distributed, this will be clever, or rather ITS transport layer should be.

        :param table: table to look up value in
        :param key: key to retrieve values for
        :return:
        """
        return { 'Content-type': 'text/json',
                 'data': Block.transport.list(**kwargs)
               }
    list.arglist=["table", "hash"]

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

