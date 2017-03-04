# encoding: utf-8
import urllib
from Block import Block
from StructuredBlock import StructuredBlock
from MutableBlock import MutableBlock, MutableBlockMaster
from MyHTTPServer import MyHTTPRequestHandler, exposed
from misc import ToBeImplementedException


class DwebHTTPRequestHandler(MyHTTPRequestHandler):

    defaultipandport = ('192.168.1.156', 4243)

    @exposed
    def block(self, table=None, hash=None, contenttype="application/octet-stream", **kwargs):
        """
        Retrieve a block, Paired with TransportHTTP.block
        Exceptions: TransportBlockNotFound if hash invalid

        :param table: Which table to store data in
        :param kwargs: { hash }
        :return: raw data from block
        """
        return {"Content-type": contenttype,
                "data": Block.block(hash=hash, table=table )._data} # Should be raw data returned
    block.arglist=["table", "hash"]

    @exposed
    def sblock(self, table=None, hash=None, **kwargs):
        """
        Retrieve a block, Paired with TransportHTTP.block

        :param table: Which table to use
        :param kwargs: { hash }
        :return: raw data from block
        """
        sb = StructuredBlock.sblock(table=table, hash=hash)
        return { "Content-type": 'text/json', "data": sb._data }
    sblock.arglist=["table", "hash"]

    @exposed
    def store(self, table=None, data=None, **kwargs):
        hash = Block(data).store(table=table)
        return { "Content-type": "appliction/octet-stream", "data": hash }
    store.arglist=["table", "data"]

    @exposed
    def file(self, table=None, hash=None, contenttype=None, verbose=False, **kwargs):
        """
        file is specific to the URL gateway, knows about various kinds of directories, what stored there, and how to return to browser

        :param table: table holding content
        :param hash:  hash of content
        :param kwargs:
        :return: Dict suitable for looking for headers.
        """
        if verbose: print "file",table,hash,contenttype,kwargs
        if table == "sb":
            b = StructuredBlock.sblock(table=table, hash=hash, **kwargs)
            return b.__dict__
        elif table == "mb": # Its a Mutable Block, fetch the sigs, then get latest, then fetch its content.
            mb = MutableBlock(hash=hash, verbose=verbose)
            print "XXX@63",mb
            mb.fetch(verbose=verbose)  # Get the sigs
            print "XXX@65",mb
            return mb._current._sb(verbose=verbose).__dict__  # Pass teh StructuredBlock which should have the Content-type field etc.
        elif table == "b":
            return {"Content-type": contenttype,
                "data": Block.block(hash=hash, table=table, **kwargs )._data} # Should be raw data returned
        else:
            raise ToBeImplementedException(name="file for table "+table)
    file.arglist=["table", "hash"]

    @exposed
    def update(self, table=None, hash=None, contenttype=None, data=None, **kwargs):
        """
        Update the content

        :param table:   Which table to put it in, usually mb
        :param hash:    hash of public key of mb
        :param kwargs:  Normally would include authentication
        :return:
        """
        #Fetch key from hash
        verbose=True
        if verbose: print "DwebHTTPRequestHandler.update",table,hash,data,type
        privkey = Block.block(table="mbm", hash=hash, verbose=verbose)._data #TODO what happens if cant find
        # Store the data
        sbhash = StructuredBlock(data=data, verbose=verbose, **{"Content-type": contenttype}).store()
        #Create Mbm from key; load with data; sign and store
        mbm = MutableBlockMaster(key=privkey, hash=sbhash, verbose=verbose).signandstore(verbose=verbose)
        return {"Content-type": "text/plain",       # Always returning plain text as the URL whatever type stored
                "data": self.url(mbm, command="file", table="mb")}  # Note cant use mbm.url as not valid on TransportLocal
    update.arglist=["table","hash","contenttype"]

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

    def url(self, obj, command=None, hash=None, contenttype=None, table=None, **options):
        # Identical to TransportHTTP.url
        url =  "http://%s:%s/%s/%s/%s"  \
               % (self.ipandport[0], self.ipandport[1], command or obj.transportcommand, table or obj.table, hash or obj.hash)
        if contenttype:
            url += "/" + urllib.quote(contenttype,safe='')
        return url

if __name__ == "__main__":
    DwebHTTPRequestHandler.HTTPToLocalGateway() # Run local gateway

