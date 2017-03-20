# encoding: utf-8
import urllib
from misc import _print
from Block import Block
from StructuredBlock import StructuredBlock
from MutableBlock import MutableBlock
from MyHTTPServer import MyHTTPRequestHandler, exposed
from misc import ToBeImplementedException
from CommonBlock import Transportable
import CryptoLib


LetterToClass = {
    Block._table: Block,
    StructuredBlock._table: StructuredBlock,
    MutableBlock._table: MutableBlock,
}

class DwebHTTPRequestHandler(MyHTTPRequestHandler):

    #defaultipandport = ('192.168.1.156', 4243)
    defaultipandport = ('localhost', 4243)


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

    @exposed
    def rawfetch(self, hash=None, contenttype="application/octet-stream", **kwargs):
        """
        Retrieve a block, Paired with TransportHTTP.fetch
        Exceptions: TransportBlockNotFound if hash invalid

        :param hash: block to retrieve
        :return: { Content-Type, data: raw data from block
        """
        return {"Content-type": contenttype,
                "data": Transportable.transport.rawfetch(hash=hash)} # Should be raw data returned
    rawfetch.arglist=["hash"]

    @exposed
    def rawlist(self, hash=hash, **kwargs):
        """
        Retrieve a list of objects - Paired with TransportHTTP.list

        :param hash: key to retrieve values for
        :return:
        """
        return { 'Content-type': 'text/json',
                 'data': Transportable.transport.rawlist(hash=hash, **kwargs)
               }
    rawlist.arglist=["hash"]

    @exposed
    def rawreverse(self, hash=hash, **kwargs):
        """
        Retrieve a list of objects - Paired with TransportHTTP.list

        :param hash: key to retrieve values for
        :return:
        """
        return {'Content-type': 'text/json',
                'data': Transportable.transport.rawreverse(hash=hash, **kwargs)
                }
    rawreverse.arglist = ["hash"]

    @exposed
    def rawstore(self, data=None, **kwargs):
        hash = Transportable.transport.rawstore(data=data, **kwargs)
        return { "Content-type": "appliction/octet-stream", "data": hash }
    rawstore.arglist=["data"]

    @exposed
    def rawadd(self, data=None, **ignored):
        """
        Pass raw data on to transport layer,

        :param data: Dictionary to add {hash, signature, date, signedby} or json string of it.
        """
        if isinstance(data, basestring): # Assume its JSON
            data = CryptoLib.loads(data)    # HTTP just delivers bytes
        return  { "Content-type": "appliction/octet-stream",
                  "data":  Transportable.transport.rawadd(**data)
                  }
        #hash=None, date=None, signature=None, signedby=None, verbose=False, **options):
    rawadd.arglist=["data"]

    @exposed
    def content(self, table=None, hash=None, urlargs=None, contenttype=None, verbose=False, **kwargs):
        return Transportable.transport.fetch("content", cls=table, hash=hash,path=urlargs, verbose=verbose, contenttype=contenttype, **kwargs  )
    content.arglist=["table", "hash"]

    @exposed
    def file(self, table=None, hash=None, urlargs=None, contenttype=None, verbose=False, **kwargs):
        return Transportable.transport.fetch(command="file", cls=table, hash=hash,path=urlargs, verbose=verbose, contenttype=contenttype, **kwargs  )
    file.arglist=["table", "hash"]


    @exposed
    def update(self, hash=None, contenttype=None, data=None, verbose=False, **kwargs):
        """
        Update the content - this is specific to the HTTP interface so that it can be driven by editors like mce.
        #Exception PrivateKeyException if passed public key and master=True

        :param table:   Which table to put it in, usually mb
        :param hash:    hash of public key of mb
        :param kwargs:  Normally would include authentication
        :return:
        """
        #Fetch key from hash
        if verbose: print "DwebHTTPRequestHandler.update",hash,data,type

        # Store the data
        sb = StructuredBlock(verbose=verbose, **{"Content-type": contenttype})
        sb.data = data
        sbhash = sb.store(verbose=verbose)
        #Create Mbm from key; load with data; sign and store
        mbm = MutableBlock(master=True, hash=hash, contenthash=sbhash, verbose=verbose).signandstore(verbose=verbose)
        #Exception PrivateKeyException if passed public key and master=True
        return {"Content-type": "text/plain",       # Always returning plain text as the URL whatever type stored
                "data": self.url(mbm, command="file", table="mb", hash=mbm._keypair.publichash)}
    update.arglist=["hash","contenttype"]



    def url(self, obj, command=None, hash=None, table=None, contenttype=None, url_output=None, **options):
        """

        :return: HTTP style URL to access this resource - not sure what this works on yet.
        """
        # Identical code in TransportHTTP and ServerHTTP.url
        hash = hash or obj._hash
        if command in ["file"]:
            if url_output=="getpost":
                return [False, command, [table or obj._table, hash]]
            else:
                url = "http://%s:%s/%s/%s/%s" \
                    % (self.ipandport[0], self.ipandport[1], command, table or obj._table, hash)
        else:
            if url_output=="getpost":
                raise ToBeImplementedException(name="TransportHTTP.url:command="+command+",url_output="+url_output)
            else:
                url =  "http://%s:%s/%s/%s"  \
                    % (self.ipandport[0], self.ipandport[1], command or "rawfetch", hash)
        if contenttype:
            if command in ("update",):  # Some commands allow type as URL parameter
                url += "/" + urllib.quote(contenttype, safe='')
            else:
                url += "?contenttype=" + urllib.quote(contenttype, safe='')
        return url

if __name__ == "__main__":
    DwebHTTPRequestHandler.HTTPToLocalGateway() # Run local gateway

