# encoding: utf-8
import urllib
from misc import _print
from Block import Block
from StructuredBlock import StructuredBlock
from MutableBlock import MutableBlock
from MyHTTPServer import MyHTTPRequestHandler, exposed
from misc import ToBeImplementedException
from CommonBlock import Transportable


class DwebHTTPRequestHandler(MyHTTPRequestHandler):

    #defaultipandport = ('192.168.1.156', 4243)
    defaultipandport = ('localhost', 4243)

    @exposed
    def block(self, hash=None, contenttype="application/octet-stream", **kwargs):
        """
        Retrieve a block, Paired with TransportHTTP.block
        Exceptions: TransportBlockNotFound if hash invalid

        :param hash: block to retrieve
        :return: raw data from block
        """
        return {"Content-type": contenttype,
                "data": Block.block(hash=hash)._data} # Should be raw data returned
    block.arglist=["hash"]

    @exposed
    def OBSsblock(self, table=None, hash=None, **kwargs):  #TODO-REFACTOR pobably delete
        """
        Retrieve a block, Paired with TransportHTTP.block

        :param table: Which table to use
        :param kwargs: { hash }
        :return: raw data from block
        """
        sb = StructuredBlock.sblock(table=table, hash=hash)
        return { "Content-type": 'text/json', "data": sb._data }    #TODO-REFACTOR, probably not _data, maybe export
    OBSsblock.arglist=["table", "hash"]

    @exposed
    def store(self, data=None, **kwargs):
        hash = Block(data=data).store()
        return { "Content-type": "appliction/octet-stream", "data": hash }
    store.arglist=["data"]

    @exposed
    def file(self, table=None, hash=None, urlargs=None, contenttype=None, verbose=False, **kwargs):
        """
        file is specific to the URL gateway, knows about various kinds of directories, what stored there, and how to return to browser

        :param table: table holding content
        :param hash:  hash of content
        :param kwargs:
        :return: Dict suitable for looking for headers.
        """
        if verbose: print "file",table,hash,contenttype,kwargs
        #TODO-REFACTOR so not block dependent
        if table in ("sb", "mb"):
            if table == "mb":
                mb = MutableBlock(hash=hash, verbose=verbose)
                mb.fetch(verbose=verbose)  # Get the sigs
                sb = mb._current._sb(verbose=verbose)
            else: #table == "sb"
                sb = StructuredBlock.sblock(table=table, hash=hash, **kwargs) #TODO-REFACTOR so sblock not being used

            while urlargs:
                p1 = urlargs.pop(0)
                sb = sb.link(p1)
            if isinstance(sb, basestring):
                return { "data": sb }
            elif isinstance(sb, StructuredBlock):
                if not sb.data and sb.hash:
                    sb.data = sb.content(verbose=verbose, **kwargs)
                return sb.__dict__
            else:
                ToBeImplementedException(name="file for table sb and content=" + sb.__class__.__name__)

        elif table == "b":
            return {"Content-type": contenttype,
                "data": Block.block(hash=hash, table=table, **kwargs )._data} # Should be raw data returned
        else:
            raise ToBeImplementedException(name="file for table "+table)
    file.arglist=["table", "hash"]

    @exposed
    def update(self, table=None, hash=None, contenttype=None, data=None, verbose=False, **kwargs):
        """
        Update the content

        :param table:   Which table to put it in, usually mb
        :param hash:    hash of public key of mb
        :param kwargs:  Normally would include authentication
        :return:
        """
        #TODO-REFACTOR to use new lists
        #Fetch key from hash
        if verbose: print "DwebHTTPRequestHandler.update",table,hash,data,type

        # Store the data
        sbhash = StructuredBlock(data=data, verbose=verbose, **{"Content-type": contenttype}).store(verbose=verbose)
        #Create Mbm from key; load with data; sign and store
        mbm = MutableBlock(master=True, hash=hash, contenthash=sbhash, verbose=verbose).signandstore(verbose=verbose)
        return {"Content-type": "text/plain",       # Always returning plain text as the URL whatever type stored
                "data": self.url(mbm, command="file", table="mb", hash=mbm._keypair.publichash)}  # Note cant use mbm.url as not valid on TransportLocal
    update.arglist=["table", "hash","contenttype"]

    @exposed
    def add(self, data=None, **kwargs):
        #TODO-REFACTOR to use new lists
        """
        add has no higher level interpretation, so just pass to server's transport layer direct
        Once distributed, this will be clever, or rather ITS transport layer should be.

        :param kwargs: required: {key, value }
        :return:
        """
        return  { "Content-type": "appliction/octet-stream",
                  "data":  Transportable.transport.add(**data)
                  }
        #hash=None, date=None, signature=None, signedby=None, verbose=False, **options):
    add.arglist=["data"]

    @exposed
    def list(self, **kwargs):
        #TODO-REFACTOR to use new lists
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
    list.arglist=["hash"]

    @classmethod
    def HTTPToLocalGateway(cls):
        """
        DWeb HTTP server, all this one does is gateway from HTTP Transport to Local Transport, allowing calls to happen over net.
        One instance of this will be created for each request, so don't override __init__()
        Initiate with something like: DwebHTTPRequestHandler.serve_forever()

        :return: Never Returns
        """
        from TransportLocal import TransportLocal # Avoid circular references
        Transportable.setup(TransportLocal, verbose=False, dir="../cache_http")  # HTTP server is storing locally
        cls.serve_forever(verbose=False)    # Uses defaultipandport
        #TODO-HTTP its printing log, put somewhere instead

    def url(self, obj, command=None, hash=None, contenttype=None, table=None, **options):
        # Identical to TransportHTTP.url
        #TODO-REFACTOR-URL
        url =  "http://%s:%s/%s/%s/%s"  \
               % (self.ipandport[0], self.ipandport[1], command or obj.transportcommand, table or obj.table, hash or obj._hash)
        # TODO-REFACTOR probably remove transportcommand in all places
        if contenttype:
            url += "/" + urllib.quote(contenttype,safe='')
        return url

if __name__ == "__main__":
    DwebHTTPRequestHandler.HTTPToLocalGateway() # Run local gateway

