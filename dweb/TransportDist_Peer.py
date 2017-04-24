# encoding: utf-8

import binascii # for crc32
from random import randint
import base64
import socket   # for socket.error
import threading
from requests.exceptions import ConnectionError
import Queue    #TODO-QUEUE
from Transport import TransportFileNotFound
from TransportHTTP import TransportHTTP
from MyHTTPServer import exposed
from CryptoLib import CryptoLib
from Dweb import Dweb
from Transport import TransportFileNotFound, TransportBlockNotFound
from TransportHTTP import TransportHTTPBase
from TransportLocal import TransportLocal
from ServerHTTP import DwebHTTPRequestHandler
from misc import MyBaseException, ToBeImplementedException

class PeerCommandException(MyBaseException):
        httperror = 501  # Unimplemented
        msg = "Unrecognized peer command: {command}"

class ServerPeer(DwebHTTPRequestHandler):
    # Do not define __init__ its handled in BaseHTTPRequestHandler superclass

    @classmethod
    def setupandserveforever(cls, host=None, port=None, dir=None, verbose=False, **options):
        """
        The Peer server is standard HTTP server but instead of TransportLocal, it uses TransportDistPeer
        Defined on same port by default as it is a superset of DwebHTTPRequestHandler

        :param ipandport: 
        :param dir: 
        :param verbose: 
        :param options: 
        :return: 
        """
        port = port or cls.defaultipandport[1]
        ipandport = (host or cls.defaultipandport[0], port)
        # Creates a transport used for outgoing, and then creates a server that answers queries and passes to transport
        Dweb.settransport(transportclass=TransportDistPeer, ipandport=ipandport, verbose=False,
                                  dir=dir or "../cache_peer/%s" % port)  # HTTP server is storing locally
        try:
            cls.serve_forever(ipandport=ipandport, verbose=verbose, **options)
        except socket.error as e:
            print "ServerPeer",host,port,str(e)
            # Returns to caller and presumably exits which should kill any daemon thread
        # ERR socket.error if port already in use



    # See other !ADD-TRANSPORT-COMMAND
    @exposed
    def peer(self, data=None, verbose=False, **options):    # data is string, not yet converted to json
        """
        Server command that takes a JSON packet (typically PeerRequest) on input, passes it to a dispatcher on the Transport layer, 
        and returns the JSON result (typically PeerResponse).
        """
        req = PeerRequest.loads(data)
        res =  Dweb.transport.dispatch(req=req, verbose=verbose, **options)
        Dweb.transport.learnfrom(res, verified=False)   # Learn from full set - sent and received
        return { "Content-type": "application/json", "data": res }
    peer.arglist=["data"]

    @exposed
    def info(self, data=None, **kwargs):
        """
        Handle incoming info request - returns info on this node, but also learns from the request about peers the caller knows.
        See TransportDistPeer.connect for caller
        
        :param data: 
        :param kwargs: 
        :return: 
        """
        #Subclass DwebHTTPRequestHandler.info to return info about ServerPeer
        node = Dweb.transport
        node.learnfrom(PeerSet(data["peers"], verified=False),verified=False)
        del(data["peers"])
        node.learnfrom(Peer(**data), verified=True)
        return { 'Content-type': 'text/json',
                 'data': node.infodata()
        }
    info.arglist=[]


"""
Highly experimental distributed layer for dWeb, just a proof of concept and place for experimentation.
"""
class TransportDistPeer(TransportHTTPBase): # Uses TransportHTTPBase for some common functions esp _sendGetPost

    """
    Subclass of Transport.
    Implements the raw primitives as reads and writes of file system.
    Represents our node in the peer network.
    Note that a "Peer" is the representation of another node.

    nodeid  Randomly selected nodeid. #TODO use something like IPFS rules for generating node ids
    tl      Transport object to check for local copy - usually TransportLocal
    """
    bitlength = 30  # Allowsfor 2^n nodes, so 30 is ~ 1 billion.

    def __init__(self, tl=None, nodeid=None, verbose=False, ipandport=None, **options):
        """
        Create a distirbuted transport object (use "setup" instead)

        :param options:
        """
        super(TransportDistPeer,self).__init__(verbose=verbose, ipandport=ipandport, **options) # Takes ipandport
        assert tl is not None, "Setup must be wrong asit needs a TransportLocal"
        self.tl = tl    # Connect to TransportLocal
        self.nodeid = nodeid if nodeid else randint(1, 2 ** self.bitlength - 1)  # Random id
        self.ipandport = ipandport
        self.peers = PeerSet()  # Will hold list of peers we know about
        self.connectionqueue = Queue.PriorityQueue()    # Queue of peers to try and connect to.
        self.backgroundthread(verbose=verbose)  # Instantiate a background thread


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
        return cls(tl=tl, **options)

    def __repr__(self):
        return "TransportDistPeer(%d, %s)" % (self.nodeid, self.tl.dir)

    def __eq__(self, other):
        othernodeid = other if isinstance(other, int) else other.nodeid
        return self.nodeid == othernodeid or (isinstance(other, (Peer, TransportDistPeer)) and self.ipandport == other.ipandport)

    def __ne__(self, other):
        return not self==other

    def infodata(self):
        return {  # See other !ADD-INFO-FIELDS
            'type': 'DistPeerHTTP',
            'ipandport': self.ipandport,
            'peers': self.peers,
            'nodeid': self.nodeid,
        }

    def backgroundthread(self, verbose=False):
        """
        A background thread, should do nothing till it starts getting queued requests as dont know actual ipandport etc
        Note this is dependent on the main thread existing when the server is killed, or fails to open.

        :return: 
        """
        thread = threading.Thread(target=self.runbackground, args=(verbose,))
        thread.daemon = True  # Parent thread will exit if fails to get server port
        thread.start()

    def runbackground(self, verbose=False):
        if verbose: print "Background thread starting"
        task = self.queueprocess(True)
        if verbose: print "Background thread exiting"

    #========== Standard list of Transport layer functions that have to be provided ================
    #see other !ADD-TRANSPORT-COMMAND - add a function copying the format below

    def dispatch(self, req=None, verbose=False, **options):
        """
        Handle incoming request based on req.command

        :param req: 
        :param verbose: 
        :param options: 
        :return: 
        """
        func = getattr(self, req.command, None)
        if func and getattr(func, "exposed", None): # Cant do func.exposed as it will fail if not exposed
            if verbose: print "%s.%s %s" % (self.__class__.__name__, req.command, req)
            peerresp = func(req=req, verbose=verbose, **options)
            return peerresp
        else:
            raise PeerCommandException(command=req.command)

    def rawfetch(self, hash, verbose=False, **options):
        """
        Fetch a block from the local file system and if that fails fetch from distributed and cache
        Exception: TransportFileNotFound if file doesnt exist

        :param hash:
        :param options:
        :return:
        """
        # Note node will check locally first so dont need to save in tl first.
        req = PeerRequest(command="reqfetch", sourcenode=Peer(node=self), hash=hash, verbose=verbose)
        peerresp = self.reqfetch(req=req, verbose=verbose, **options) # Err: TransportFileNotFound
        if verbose: print "reqfetch returned:", peerresp
        if not peerresp.success:
            raise TransportBlockNotFound(hash=hash)
        data = peerresp.data
        assert data is not None, "If returns data, then should be non-None"
        return data

    @exposed
    def reqfetch(self, req=None, verbose=False, **options):
        """
        Fetch content based on a req.
        Algorithm walks a tree, trying to find the "closest" node to the hash, which is most likely to have the content.

        :param req:     PeerRequest object for partially completed request
        :return:
        """
        if verbose: print "TransportDistPeer.reqfetch",req
        # See if have a local copy
        if self.tl and not options.get("ignorecache"):  # Its possible to have a TransportDistPeer without a local cache
            try:
                data = self.tl.rawfetch(req.hash, verbose=verbose, **options)
                return PeerResponse(success=True, req=req, data=data)
            except TransportFileNotFound as e:
                pass    # Acceptable error, as is drop-thru if no tl
        res = self.forwardAlgorithmically(req=req, verbose=verbose, **options)
        if res.success and res.data:
            hash = self.tl.rawstore(res.data, verbose=verbose)
            if verbose: print "TransportDist.rawfetch: Saved as hash=", hash
        return res

    def rawlist(self, hash, verbose=False, **options):
        """
        Retrieve record(s) matching a hash (usually the hash of a key),
        Exception: IOError if file doesnt exist

        :param hash: Hash in table to be retrieved
        :return: list of dictionaries for each item retrieved
        """
        req = PeerRequest(command="reqlist", sourcenode=Peer(node=self), hash=hash, verbose=verbose)
        peerresp = self.reqlist(req=req, verbose=verbose, **options) # Err: TransportFileNotFound
        if verbose: print "reqlist returned:", peerresp
        if not peerresp.success:
            raise TransportBlockNotFound(hash=hash)
        data = peerresp.data
        assert data is not None, "If returns data, then should be non-None"
        return data

    def rawreverse(self, hash, verbose=False, **options):

        """
        Retrieve record(s) matching a hash (usually the hash of a key), in this case from a local directory
        Exception: IOError if file doesnt exist

        :param hash: Hash in table to be retrieved
        :return: list of dictionaries for each item retrieved
        """
        req = PeerRequest(command="reqreverse", hash=hash, sourcenode=Peer(node=self), verbose=verbose)
        peerresp = self.reqreverse(req=req, verbose=verbose, **options) # Err: TransportFileNotFound
        if verbose: print "reqreverse returned:", peerresp
        if not peerresp.success:
            raise TransportBlockNotFound(hash=hash)
        data = peerresp.data
        assert data is not None, "If returns data, then should be non-None"
        return data

    @exposed
    def reqlist(self, req=None, verbose=False, **options):
        return self._reqlistreverse(subdir="list", req=req, verbose=verbose, **options)

    @exposed
    def reqreverse(self, req=None, verbose=False, **options):
        return self._reqlistreverse(subdir="reverse", req=req, verbose=verbose, **options)

    def _reqlistreverse(self, subdir=None, req=None, verbose=False, **options):
        """
        Retrieve record(s) matching a hash (usually the hash of a key), in this case from a local directory
        Exception: IOError if file doesnt exist

        :param req:     PeerRequest object for partially completed request
        :return: list of dictionaries for each item retrieved
        """
        if verbose: print "TransportDistPeer._reqlistreverse",req
        # See if have a local copy #TODO-TX need to be cleverer about combining results - and local cache will be out of date
        if self.tl and not options.get("ignorecache"):  # Its possible to have a TransportDistPeer without a local cache
            try:
                data = self.tl._rawlistreverse(subdir=subdir, hash=req.hash, verbose=verbose, **options)
                return PeerResponse(success=True, req=req, data=data)
            except TransportFileNotFound as e:
                pass    # Acceptable error, as is drop-thru if no tl
        res = self.forwardAlgorithmically(req=req, verbose=verbose, **options)
        return res

    def rawstore(self, data=None, verbose=False, **options):
        """
        Store the data on dweb, keep a local copy
        Exception: TransportBlockNotFound if file doesnt exist

        :param data: opaque data to store
        :return: hash of data
        """
        req = PeerRequest(command="reqstore", data=data, sourcenode=Peer(node=self), verbose=verbose)
        peerresp = self.reqstore(req=req, verbose=verbose, **options)
        if verbose: print "TransportDistPeer.reqstore returned:", peerresp
        if not peerresp.success:
            print "XXX=> TransportDistPeer.rawstore err=",peerresp.err
            raise TransportBlockNotFound(hash=hash) #TODO-TX choose better error
        return peerresp.hash

    @exposed
    def reqstore(self, req=None, verbose=False, **options):
        """
        Store into dWeb, 

        :param verbose: 
        :param options: 
        :return: 
        """
        if verbose: print "TransportDistPeer.reqstore len=", len(req.data), req
        if self.tl and not options.get("ignorecache"):
            hash = self.tl.rawstore(req.data, verbose=verbose, **options)  # Save local copy
            if req.hash:
                assert hash == req.hash
            else:
                req.hash = hash  # Need it to find targetnodeid
        res = self.forwardClosest(req, verbose=verbose)
        if not res: # Couldnt store closer, return our hash
            res = PeerResponse(hash=hash, success=True, req=req)
        assert res.hash == hash, "Returned hash must match"
        return res

    def rawadd(self, hash=None, date=None, signature=None, signedby=None, verbose=False, subdir=None, **options):
        """
        Append to list on dweb (TODO-TX not kept locally now as cant yet combined with canonical)
        Exception: TransportBlockNotFound if file doesnt exist

        :param data: opaque data to store
        :return: hash of data
        """
        if verbose: print "TransportDistPeer.rawadd: %s,%s" % (hash,subdir)
        subdir = subdir or ("list","reverse")
        if "list" in subdir:
            reqL = PeerRequest(command="reqaddlist", hash=signedby, verbose=verbose, sourcenode=Peer(node=self),
                               data={ "hash": hash, "date": date, "signature": signature, "signedby": signedby })
            peerrespL = self.reqaddlist(req=reqL, verbose=verbose, **options)
            if verbose: print "node.reqadd returned:", peerrespL
        if "reverse" in subdir:
            reqR = PeerRequest(command="reqaddreverse", hash=hash,  verbose=verbose, sourcenode=Peer(node=self),
                               data={ "hash": hash, "date": date, "signature": signature, "signedby": signedby })
            peerrespR = self.reqaddreverse(req=reqR, verbose=verbose, **options)
            if verbose: print "node.reqadd returned:", peerrespR
        if not peerrespL.success or not peerrespR.success:
            print "XXX=> TransportDistPeer.rawadd  err=",peerrespL,peerrespR   # Debug, figure out what error it was
            raise TransportBlockNotFound(hash=hash) #TODO-TX choose better error
        return peerrespL    # No significant result in peerrespR #TODO-QUEUE maybe merge peers etc from peerrespR

    @exposed
    def reqaddlist(self, req=None, verbose=False, **options):
        """
        Store a signature in a pair of DHTs 
        Exception: IOError if file doesnt exist

        :param PeerRequest req: Signature to store contains: hash, date, signature, signedby
        :return:
        """
        if verbose: print "TransportDistPeer.reqadd len=", len(req.data), req
        if self.tl and not options.get("ignorecache"):
            # Keep a local copy, note ignored in rawlist/rawreverse
            self.tl.rawadd(subdir="list", verbose=verbose, **req.data)  # Save local copy
        res = self.forwardClosest(req)
        if not res: # Couldnt store closer, our store was sufficient
            res = PeerResponse(success=True, req=req)
        return res

    @exposed
    def reqaddreverse(self, req=None, verbose=False, **options):
        """
        Store a signature in a pair of DHTs 
        Exception: IOError if file doesnt exist

        :param PeerRequest req: Signature to store contains: hash, date, signature, signedby
        :return:
        """
        if verbose: print "TransportDistPeer.reqadd len=", len(req.data), req
        if self.tl and not options.get("ignorecache"):
            # Keep a local copy, note ignored in rawlist/rawreverse
            self.tl.rawadd(subdir="reverse", verbose=verbose, **req.data)  # Save local copy
        res = self.forwardClosest(req)
        if not res: # Couldnt store closer, our store was sufficient
            res = PeerResponse(success=True, req=req)
        return res

    #========== END OF COMMANDS ===========

    def forwardClosest(self, req=None, verbose=False):
        """
        Forward to the peer closest to the targetnode, this may need improving to store in multiple places. 
        This might need considerable tweaking for Lists, as can pick up info from list on "a" and pass to "b" 
        :param req: 
        :return: 
        """
        if req.verbose: print "TransportDistPeer.forwardClosest:",req
        savedhops = req.hops
        req.route.append(self.nodeid)  # Append self to route before sending on, or responding
        assert req.hash, "Cant forward without hash"
        peer_intermediate = self.peers.nextnode(req.targetnodeid, exclude=req.tried, verbose=req.verbose)
        if peer_intermediate:
            req.tried.append(peer_intermediate)
            req.hops = savedhops + 1
            res = peer_intermediate.reqforward(req=req, verbose=verbose)
            return res
        else:
            if verbose: print "forwardClosest: no peers"
            return None


    def forwardAlgorithmically(self, req=None, verbose=False, **options):
        savedhops = req.hops    # Changed during the loop
        req.route.append(self.nodeid)  # Append self to route before sending on, or responding
        # Try all connected nodes, in order of how close to target
        peer_intermediate = self.peers.nextnode(req.targetnodeid, exclude=req.tried)
        while peer_intermediate:
            if verbose: print self, "Sending via closest", peer_intermediate, "for", req.targetnodeid
            req.tried.append(peer_intermediate)
            req.hops = savedhops + 1
            res = peer_intermediate.reqforward(req=req, verbose=verbose)
            if res.success:
                return res
            # It failed, lets loop and try other peers
            req.tried.append(res.req.tried)
            if verbose: print self, "Retrying from ", self.nodeid, "to destn", req.targetnodeid, "with excluded", req.tried
            peer_intermediate = self.peers.nextnode(req.targetnodeid, exclude=req.tried)
        return PeerResponse(success=False, req=req, err="No response from any of %s peers" % len(self.peers))

    #======== Peer management ----------
    def learnfrom(self, learning, verified=False):
        #print "XXX@424",learning.__class__.__name__, learning
        if isinstance(learning, PeerSet):
            for peer in learning:
                self.learnfrom(peer, verified=verified)
        elif isinstance(learning, Peer):
            if (self != learning) and (learning not in self.peers):
                learning.connect = False    # We aren't connected to it yet
                self.peers.append(learning)
                self.queueconnections(learning) # Queue for connecting to #TODO-TX could maybe use a priority queue
        elif isinstance(learning, PeerResponse):
            self.learnfrom(learning.req.sourcenode, verified=False)
            self.learnfrom(learning.req.tried, verified=False)
        else: # isinstance(learning, (list, tuple, set, dict)):
            assert False, "Node.learnfrom expects PeerSet or Peer, not"+learning.__class__.__name__

    def queueconnections(self, peer):
        priority = 0    #TODO-QUEUE can use heuristic on priority
        self.connectionqueue.put((0,peer))

    def queueprocess(self, block):
        try:
            task = self.connectionqueue.get(block)
            print "XXX@439 queueprocess task=",task #TODO-QUEUE implement handling it
        except Exception as e:
            print "XXX@441 queueprocess exception needs handling:",e #TODO-QUEUE handle exceptions (empty ?)
            raise e


class PeerSet(set):
    """
    A list of peers
    """
    def __init__(self,args=None, verified=False):
        args = args or []
        super(PeerSet,self).__init__((a if isinstance(a,Peer) else Peer(verified=verified, **a)) for a in args)

    def connected(self):
        return PeerSet([peer for peer in self if peer.connected])

    def notin(self, exclude):
        return PeerSet([peer for peer in self if peer not in exclude])

    def find(self, nodeid=None, ipandport=None):
        print "XXX@478",self
        peers = [peer for peer in self if (nodeid and (nodeid == peer.nodeid)) or (ipandport and (ipandport == peer.ipandport))]
        print "XXX@480", peers
        assert len(peers) < 2, "There should be only one or zero peers"
        if peers:
            return peers[0]  # Can only be one
        else:
            return None

    def append(self, peer):
        if isinstance(peer, (list, set)):
            for p in peer: self.append(p)
        else:
            poss = self.find(nodeid=peer.nodeid, ipandport=peer.ipandport)  # Returns one or none
            if poss:
                poss.merge(peer)
            else:
                self.update((peer,))   # Adds to list

    def closestto(self, nodeid):
        return self and min(self, key=lambda p: p.distanceto(nodeid))

    def furthestfrom(self, nodeid):
        max(self, key=lambda p: p.distanceto(nodeid))

    def __str__(self):
        return str([(p.nodeid, p.ipandport) for p in self])

    def nextnode(self, targetnodeid=None, exclude=None, verbose=False):
        """
        Algorithm to pick next node to tackle.
        This is heuristic, i.e. can be improved based on e.g. ping time to node, responsiveness,

        :param targetnodeid:
        :param exclude:
        :param verbose:
        :return:
        """
        return self.connected().notin(exclude).closestto(targetnodeid)

    def dumps(self):
        return list(self)

class Peer(object):
    """
    One for each node we know about.
    Applies to both connected and disconnected peers.

    nodeid      ID of the node (as assigned by that node)
    connected   True if currently have connection to this Peer that can request on
    ipandport   HTTP address and port to connect to
    transport   How to get to Peer if connected (usually a TransportHTTP instance but could migrate to WebRTC
    info        Info packet as returned by connected peer
    verified    True if got this info direct from peer #TODO-AUTHENTICAITON want encrypted 

    See other !ADD-PEER-FIELDS
    """

    def __init__(self, node=None, nodeid=None, ipandport=None, type=None, verified=False, verbose=False):
        if verbose: print "Peer.__init__",nodeid,ipandport
        if node:
            self.nodeid=node.nodeid
            self.ipandport = node.ipandport
        else:
            self.ipandport = ipandport
            self.nodeid = nodeid
        self.type = type
        self.connected = False  # Start off disconnected
        self.transport = None
        self.verified = verified
        self.info = None
        #See other !ADD-PEER-FIELDS

    def __repr__(self):
        #See other !ADD-PEER -FIELDS
        return "Peer(%s, %s, %s)" % (self.nodeid, self.ipandport,self.connected)

    def __hash__(self): # For the set function to know what is equal - not quite same as the __eq__ but generally wont see case of matching ipandport nad not nodeid
        return self.nodeid or hash(tuple(self.ipandport))

    def __eq__(self, other):    # Note this facilittes "in" to work on PeerSet's
        nodeid = other if isinstance(other, int) else other.nodeid
        return (nodeid and (self.nodeid == nodeid)) or (isinstance(other,(Peer,TransportDistPeer)) and (self.ipandport == other.ipandport) )

    def __ne__(self, other):
        return not (self == other)

    @property
    def node(self):
        """
        May at some point want to store this on the Peer, but for now use Dweb.transport 
        
        :return: 
        """
        return Dweb.transport

    def dumps(self):
        #See other !ADD-PEER-FIELDS
        return {"nodeid": self.nodeid, "ipandport": self.ipandport}

    def connect(self, verbose=False):
        if not self.connected:
            if verbose: print "Connecting to peer", self
            self.transport = TransportHTTP(ipandport=self.ipandport)
            try:
                self.info = self.transport.info(data=Dweb.transport.infodata())
                if verbose: print self.info
            except ConnectionError as e:
                pass
                #raise e
            else:
                # See other !ADD-INFO-FIELDS
                # This info is straight from the host, so verified, but the peerlist is indirect
                self.nodeid = self.info["nodeid"]
                self.peers = PeerSet(self.info["peers"], verified=False)    # This bit is verified, i.e. we know this Peer thinks these are its peers.
                self.type = self.info["type"]
                if verbose: print "nodeid=", self.nodeid
                self.connected = True
                self.verified = True
                print "XXX@597",self.peers
                self.node.learnfrom(self.peers, verified=False)
        return self # For chaining

    def merge(self, peer):
        """
        Merge another peer into self, assumes latter more accurate for any info it contains.
        Note usage applies to updating ipandport on known nodeid, or updating nodeid on known ipandport
        
        :param peer: 
        :return: 
        """
        #See other !ADD-PEER-FIELDS
        for field in ("nodeid", "ipandport", "type", "transport", "info"):
            old = getattr(self, field, None)
            new = getattr(peer, field, None)
            res = (peer.verified and new) or (self.verified and old) or new or old  # Order of preference for result
            setattr(self, field, res)
        if peer.connected: self.connected = True            # Logical or of self and peer's connected status
        if peer.verified: self.verified = True

    def distanceto(self, peerid):
        """
        Return a distance to the peerid, based on a bitwise or of the ids

        :param peerid:
        :return: int 0..TransportDistPeer.bitlength-1
        """
        if isinstance(peerid, (Peer, TransportDistPeer)): peerid = peerid.nodeid
        offset = peerid ^ self.nodeid
        return bin(offset).count("1")

    def reqforward(self, req=None, verbose=False, **options):
        """
        Forward a request to a peer, and get a PeerResponse in return

        :param req:     PeerRequest
        :param verbose: 
        :param options: 
        :return:        PeerResponse (including final PeerRequest)
        """
        if verbose: print "Peer.reqforward to",self
        assert isinstance(req, PeerRequest),"Making assumption its forwarding a PeerRequest"
        if not self.connected:
            self.connect()
        thttp = self.transport
        # Now send via the transport
        resp = thttp._sendGetPost(True, "peer", headers={"Content-Type": "application/json"}, urlargs=[], data=CryptoLib.dumps(req))
        return PeerResponse.loads(resp.json()) # Return PeerResponse

class PeerRequest(object):
    """
    Overloaded dictionary sent to Peers

    verbose     True if should gather debugging info - note this is on a per-message rather than per-node or per-routine basis
    command     function being requested e.g. "rawfetch", "rawstore"
    hash        Hash of item being requested
    hops        Number of hops request has been through prior to this.
    route       PeerSet, list of NodeIds it has passed through to reach targer.
    tried       PeerSet, nodes that have been tried while trying to reach destn (superset of route, includes false branches)

    Properties
    targetnodeid Target node id to ask, note in a sparse space this nodeid doesnt exist and we are trying to get close to it
    #!SEE-OTHER-PEERREQUEST-ADD-FIELDS
    """

    def __init__(self, sourcenode=None, command=None, data=None, route=None, hash=None, hops=0, tried=None, verbose=False, **kwargs):
        self.sourcenode = Peer(sourcenode) if isinstance(sourcenode, Peer) else Peer(**sourcenode)
        self.command = command
        self.hops = hops
        self.data = data
        self.route = route or []
        self.tried = tried if isinstance(tried, PeerSet) else ( PeerSet(tried, verified=False) if tried else PeerSet())   # Initialize if unset
        self.verbose = verbose
        self.hash = hash
        self.__dict__.update(kwargs)    # Store any parameters we don't use, will pass on with dumps
        #see other !PEERREQUEST-ADD-FIELDS
        """
        See how/if these ued
        self.sourceid = sourceid.nodeid if isinstance(sourceid, (TransportDistPeer, Peer)) else sourceid
        self.payload = payload
        self.maxhops = maxhops
        """

    def __str__(self):
        return "PeerRequest(%s,%s,%s bytes)" % (self.command, self.hash, None if not self.data else len(self.data))

    def dumps(self):
        #see other !PEERREQUEST-ADD-FIELDS
        # Make sure next line matches the parameters to init
        serialisable = self.__dict__
        serialisable.update({ "command": self.command, "sourcenode": self.sourcenode, "hops": self.hops, "route": self.route, "tried": self.tried, "hash": self.hash,
                 "data": CryptoLib.b64enc(self.data)})
        return serialisable

    @classmethod
    def loads(cls, dic):
        """
        Pair of PeerRequest.dumps - turns a json compatible dic back into a PeerRequest
        
        :param dic: 
        :return: 
        """
        #TODO-TX get cleverer about reencoding subfields like route
        dic["data"] = CryptoLib.b64dec(dic["data"])
        return PeerRequest(**dic)

    def copy(self):
        return PeerRequest( command=self.command,  sourcenode=self.sourcenode, hash=self.hash, hops=self.hops, route=self.route, tried=self.tried.copy(),
                            data=self.data, verbose=self.verbose)
        #!SEE-OTHER-PEERREQUEST-ADD-FIELDS

    @property
    def targetnodeid(self):
        """
        Find a destination node id based on this request's hash. This node may, but probably won't exist.

        :param hash:
        :return:
        """
        return binascii.crc32(self.hash) & (2**TransportDistPeer.bitlength - 1)



class PeerResponse(object):
    """
    Overloaded dictionary returned from Peers with answer, note many fields are in the PeerRequest at .req

    err     Error message if applicable
    data    data to return in response (opaque bytes or json array)
    success True if succeeded, False if failed
    req     Request as present at node which answered it.
    #See other !ADD-PEERRESPONSE-FIELDS
    """


    def __init__(self, err=None, data=None, hash=None, req=None, success=False):
        self.err = err
        self.data = data
        self.hash = hash
        self.success = success
        self.req = req if isinstance(req, PeerRequest) else PeerRequest.loads(req)
        #See other !ADD-PEERRESPONSE-FIELDS

    def __str__(self):
        # See other !ADD-PEERRESPONSE-FIELDS
        return "PeerResponse(%s, %s, %s, %s)" % (self.success, self.err, self.hash, None if not self.data else len(self.data))

    def dumps(self):
        # See other !ADD-PEERRESPONSE-FIELDS
        return { "err": self.err, "hash": self.hash, "success": self.success,
                 "data": CryptoLib.b64enc(self.data),  "req": self.req}


    @classmethod
    def loads(cls,dic): # Pair of dumps
        # See other !ADD-PEERRESPONSE-FIELDS - only need to add here if field cant be conveyed in ascii
        dic["data"] = CryptoLib.b64dec(dic["data"])
        return cls(**dic)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print sys.argv
        sys.argv.append(None)   # Host
        sys.argv.append(0)   # Port
    ServerPeer.setupandserveforever(verbose=True, host=sys.argv[1], port=int(sys.argv[2]))
    # This only returns if the setup fails, in which cases it exists causing background daemon threads to be killed

