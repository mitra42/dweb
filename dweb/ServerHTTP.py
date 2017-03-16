# encoding: utf-8
import urllib
from misc import _print
from Block import Block
from StructuredBlock import StructuredBlock
from MutableBlock import MutableBlock
from MyHTTPServer import MyHTTPRequestHandler, exposed
from misc import ToBeImplementedException
from CommonBlock import Transportable


LetterToClass = {
    'b': Block,
    'sb': StructuredBlock,
    'mb': MutableBlock,
}

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
    def store(self, data=None, **kwargs):
        hash = Block(data=data).store()
        return { "Content-type": "appliction/octet-stream", "data": hash }
    store.arglist=["data"]

    @exposed
    def file(self, table=None, hash=None, urlargs=None, contenttype=None, verbose=False, **kwargs):
        """
        File is specific to the URL gateway, it follows a sequence of: fetching raw bytes; turning into a object based on hash; following the path; and returning content.

        :param table: table holding content
        :param hash:  hash of content
        :param urlargs: Path to object within first hash
        :param kwargs:
        :return: Dict suitable for looking for headers.
        """
        if verbose: print "file",table,hash,urlargs,contenttype,kwargs
        objcls = LetterToClass.get(table, None)
        if not objcls:
            raise ToBeImplementedException(name="file for table "+table)
        obj = objcls.block(hash=hash, verbose=verbose).fetch(verbose=verbose)   # Fetch and build obj (Block, StructuredBlock, MutableBlock)
        obj = obj.path(urlargs, verbose=verbose)
        return { "Content-type": contenttype or obj.__dict__.get("Content-type",None) or "application/octet-stream",
            "data": obj.content() }

    file.arglist=["table", "hash"]

    @exposed
    def update(self, hash=None, contenttype=None, data=None, verbose=False, **kwargs):
        """
        Update the content - this is specific to the HTTP interface so that it can be driven by editors like mce.

        :param table:   Which table to put it in, usually mb
        :param hash:    hash of public key of mb
        :param kwargs:  Normally would include authentication
        :return:
        """
        #Fetch key from hash
        if verbose: print "DwebHTTPRequestHandler.update",hash,data,type

        # Store the data
        sbhash = StructuredBlock(data=data, verbose=verbose, **{"Content-type": contenttype}).store(verbose=verbose)
        #Create Mbm from key; load with data; sign and store
        mbm = MutableBlock(master=True, hash=hash, contenthash=sbhash, verbose=verbose).signandstore(verbose=verbose)
        return {"Content-type": "text/plain",       # Always returning plain text as the URL whatever type stored
                "data": self.url(mbm, command="file", table="mb", hash=mbm._keypair.publichash)}  # Note cant use mbm.url as not valid on TransportLocal
    update.arglist=["hash","contenttype"]

    @exposed
    def add(self, data=None, **kwargs):
        """
        Add has no higher level interpretation, so just pass to server's transport layer direct as a dict.
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
        """
        list has no higher level interpretation, so just pass to server's transport layer direct
        Once distributed, this will be clever, or rather ITS transport layer should be.

        :param table: table to look up value in
        :param key: key to retrieve values for
        :return:
        """
        return { 'Content-type': 'text/json',
                 'data': Transportable.transport.list(**kwargs)
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

    def url(self, obj, command=None, hash=None, table=None, contenttype=None, **options):
        """

        :return: HTTP style URL to access this resource - not sure what this works on yet.
        """
        # Identical to ServerHTTP.url
        hash = hash or obj._hash
        if command in ["file"]:
            url = "http://%s:%s/%s/%s/%s" \
                  % (self.ipandport[0], self.ipandport[1], command or "block", table, hash)
        else:
            url =  "http://%s:%s/%s/%s"  \
                % (self.ipandport[0], self.ipandport[1], command or "block", hash)
        if contenttype:
            if command in ("update",):  # Some commands allow type as URL parameter
                url += "/" + urllib.quote(contenttype, safe='')
            else:
                url += "?contenttype=" + urllib.quote(contenttype, safe='')
        return url

if __name__ == "__main__":
    DwebHTTPRequestHandler.HTTPToLocalGateway() # Run local gateway

