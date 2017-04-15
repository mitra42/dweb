######### BELOW HERE COMES DIRECTLY FROM DHT experiemnt except that all methods renamed "OLD" till reviewed and shown needed

"""
This is a test of spanning trees - eventually to find its way into web42 or the Arduinio

Intention is that this creates a spanning tree of http connected nodes, and can ask up the tree to get to any node,
can also get the closest node to a notional node in a disconnected network, (including where the node is not connected)
"""
#TODO - make sure have at least two paths to a node
#TODO - maybe know about third or further degree connections
#TODO - send info when connect as well as retrieve (receiver then uses for own optimisation, attempt at reverse connection etc)
#TODO - try keeping a few random long-distance connections
#TODO - make this threaded - each Node is a thread

#from random import randint
#import numpy
import binascii # for crc32
from random import randint
from Transport import TransportFileNotFound
from TransportHTTP import TransportHTTP
from TransportLocal import TransportLocal
from MyHTTPServer import MyHTTPRequestHandler, exposed
from ServerHTTP import DwebHTTPRequestHandler


class ServerPeer(DwebHTTPRequestHandler):

    def __init__(self, node=None, tl=None):
            node = Node(tl=tl)

    @classmethod
    def setup(cls, nodeid=None, tl=None):
        tl = tl or TransportLocal(dir="../cache_peer")  #TODO-TX-MULTIPLE use port in dir
        node = Node(nodeid=nodeid, tl=tl)
        return cls(node=node, tl=tl)

    @classmethod
    def serve_forever(cls, node=None, **options):
        DwebHTTPRequestHandler.serve_forever(**options)
        cls.node = node # Save the node to pass queries to

    @exposed
    def reqfetch(self, data=None, **options):
        res =  self.node.rawfetch(req=data, verbose=False, **options)   # TODO-TX check if data is json or string
        return { "Content-type": "application/json", "data": res }
    reqfetch.arglist=["data"]



class Node(object):
    """
    Represents our node in the peer network.
    Note that a "Peer" is the representation of another node.

    nodeid  Randomly selected nodeid. #TODO use something like IPFS rules for generating node ids
    tl      Transport object to check for local copy - usually TransportLocal
    """
    bitlength=30    # Allowsfor 2^n nodes, so 30 is ~ 1 billion.

    def __init__(self, nodeid=None, tl=None):
        self.nodeid = nodeid if nodeid else randint(1, 2 ** self.bitlength - 1) # Random id
        self.peers = PeerSet()          # Will hold list of peers we know about
        self.optimaxconnections = 10    #TODO-TX follow is this used
        self.optiminconnections = 1     #TODO-TX follow is this used
        self.tl = tl

    def __repr__(self):
        return "Node(%d)" % self.nodeid

    def __eq__(self, other):
        if not isinstance(other, int):
            other = other.nodeid
        return self.nodeid == other

    def OLDsetminmax(self, min, max):   #TODO-TX see if used anywhere
        # Set min and max connections, (None means don't set)
        if min: self.optiminconnections = min
        if max: self.optimaxconnections = max

    def OLDonconnected(self, peer):
        """
        Should be called when connect to peer.
        """
        # if debug: print "Onconnecting",self,"<",peer
        peer.connected = True
        pdiclist = peer.reqpeers()  # So we know who our peers are conencted to
        peer.setcachedpeers(self, pdiclist)

        for peerspeer in peer.cachedpeers:
            if self.closer(peer, peerspeer) and peerspeer.connected:
                # print "connected=", len(self.peers.connected()), "optimax=",self.optimaxconnections
                if len(self.peers.connected()) > self.optimaxconnections:
                    # Peer is connected to Peerspeer and is closer to us, so drop peerspeer and just connect to peer
                    peerspeer.disconnect(connecttheirpeers=False,
                                         reason="Connected via closer new peer %d and have %d/%d cconnected" %
                                                (peer.nodeid, len(self.peers.connected()), self.optimaxconnections))

    def OLDondisconnected(self, peer):
        """
        Should be called when disconnected from a peer
        Should decide which of their peers we want to connect to directly.
        """
        for peerspeer in peer.cachedpeers:
            peerspeer.connectedvia.remove(peer)  # XXXTODO not valid
        self.considerconnecting()

    def OLDconsiderconnecting(self):
        """
        Decide if want to connect to any peers that we know about that aren't connected
        XXX Think this through - want to aggressively add connections below min, prune above max,
        levels from one extreme to other ...
        prune anything can get to another way
        prune anything can get to via 1 hop
        add anything have no way to reach
        add anything cant get to via 1 hop
        add anything 1 hop away
        """
        if len(self.peers.connected()) > self.optimaxconnections:
            candidate = self.peers.connectedandviacloserpeer().furthestfrom(
                self)  # We can get to it via something else
            if candidate:
                candidate.disconnect(reason="Dist=%d and connected via %s and have too many connections %d/%d" %
                                            (self.distance(candidate),
                                             ["%d@%d" % (p.nodeid, self.distance(p)) for p in
                                              candidate.connectedvia], len(self.peers.connected()),
                                             self.optimaxconnections))


        elif len(self.peers.connected()) < self.optiminconnections:
            candidate = self.peers.notconnectedandnotviapeer().closestto(
                self) or self.peers.notconnected().closestto(
                self)  # Look for closest cant reach and if none, just closest
            if candidate:
                candidate.connect()
                # TODO should really be a bit more random else one close unconnectable peer will block everything
        else:  # Between min and max, try connecting one that can't get via peer
            candidate = self.peers.notconnectedandnotviapeer().closestto(self)
            if candidate:
                candidate.connect()
                # TODO should really be a bit more random else one close unconnectable peer will block everything

    def OLDcloser(self, peer, peerspeer):  # True if peer is closer than peerspeer
        return self.distance(peer) < self.distance(peerspeer)

    def OLDdistance(self, peer):
        offset = peer.nodeid ^ self.nodeid
        return bin(offset).count("1")

    def OLDhandlereqpeers(self):
        """
        Called when contacted (typically over network) for list of peers
        """
        return [peer.dict() for peer in self.peers.connected()]

    def OLDseedpeer(self, nodeid=None, ipaddr=None):
        if isinstance(nodeid, Node): nodeid = nodeid.nodeid
        if nodeid == self.nodeid:
            return None
        peer = self.peers.find(nodeid)
        if not peer:
            peer = Peer(node=self, nodeid=nodeid, ipaddr=ipaddr)
        self.peers.append(peer)
        return peer

    def OLDdebugprint(self, level=2):
        if level == 2:  # Print node, and each of its peers on its own line
            print "Node(%d)" % self.nodeid
            for peer in self.peers:
                print "     " + peer.debugline(level=level)
        elif level == 1:
            print self.nodeid, ":", [peer.nodeid for peer in self.peers.connected()]

    def rawfetch(self, hash=None, req=None, verbose=False, **options):
        """
        Fetch content based on a req.
        Algorithm walks a tree, trying to find the "closest" node to the hash, which is most likely to have the content.

        :param req:     PeerRequest object for partially completed request
        :param hash:    hash for new request
        :return:
        """
        if not req:
            req = PeerRequest(hash=hash, verbose=verbose)
        elif not hash:
            hash = req.hash
        savedhops = req.hops    # Changed during the loop
        # See if have a local copy
        try:
            if self.tl:
                data = self.tl.rawfetch(hash, verbose=verbose, **options)
                return PeerResponse(success=True, req=req, data=data)
        except TransportFileNotFound as e:
            pass    # Acceptable error, as is drop-thru if no tl

        req.route.append(self.nodeid)  # Append self to route before sending on, or responding
        # Try all connected nodes, in order of how close to target
        peer_intermediate = self.peers.nextnode(req.targetnodeid, exclude=req.tried)
        while peer_intermediate:
            if verbose: print self, "Sending via closest", intermediate, "for", req.targetnodeid
            req.tried.append(peer_intermediate)
            req.hops = savedhops + 1
            res = peer_intermediate.reqfetch(req)
            if res.success:
                return res
            # It failed, lets loop
            req.tried.append(res.tried)
            if verbose: print self, "Retrying from ", self.nodeid, "to destn", req.nodeid, "with excluded", req.tried
            intermediate = self.peers.nextnode(req.targetnodeid, exclude=req.tried)
        return PeerResponse(success=False, req=req, err="No response from any of %s peers" % len(self.peers))


    def OLDloop(self):
        """
        Frequently acted on
        # TODO hook this to the sim
        """
        self.considerconnecting()

class PeerSet(set):
    """
    A list of peers
    """

    def connected(self):
        return PeerSet([peer for peer in self if peer.connected])

    def notin(self, exclude):
        return PeerSet([peer for peer in self if peer not in exclude])

    def OLDnotconnectedandnotviapeer(self): return PeerSet([peer for peer in self if not peer.connected and not peer.connectedvia])
    def OLDconnectedandviapeer(self):       return PeerSet([peer for peer in self if peer.connected and peer.connectedvia])
    def OLDconnectedandviacloserpeer(self): return PeerSet([peer for peer in self if peer.connected and peer.connectedvia and any([p.closer(peer) for p in peer.connectedvia])])
    def OLDnotconnected(self):        return PeerSet([peer for peer in self if not peer.connected])

    def OLDfind(self, nodeid):
        if not isinstance(nodeid, int): nodeid = nodeid.nodeid
        peers = [peer for peer in self if peer.nodeid == nodeid]
        if peers:
            return peers[0]  # Can only be one
        else:
            return None

    def append(self, peer):
        if not isinstance(peer, (list, set)):
            peer = (peer,)
        self.update(peer)

    def OLDdebugline(self):
        return str([p.nodeid for p in self])

    def closestto(self, nodeid):
        return self and min(self, key=lambda p: p.distanceto(nodeid))

    def furthestfrom(self, nodeid):
        max(self, key=lambda p: p.distanceto(nodeid))

    def __str__(self):
        return str([p.nodeid for p in self])

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


class Peer(object): #TODO-RX review this class
    """
    One for each node we know about.
    Applies to both connected and disconnected peers.

    nodeid      ID of the node (as assigned by that node)
    connected   True if currently have connection to this Peer that can request on
    ipandport   HTTP address and port to connect to
    transport   How to get to Peer if connected (usually a TransportHTTP instance but could migrate to WebRTC
    """


    def __init__(self, nodeid=None, ipandport=None): #, node=None, connectedvia=None, nodeid=None, ipaddr=None, **parms): #TODO-TX need this inc ipandport
        self.connected = False  # Start off disconnected
        self.transport = None
        self.ipandport = ipandport
        self.nodeid = nodeid
        """
        self.cachedpeers = PeerSet()
        self.connectedvia = connectedvia if connectedvia else PeerSet()  # List of peers connected via.
        self.nodeid = nodeid
        self.distance = node.distance(self)
        self.node = node  # Parent node (in non Sim there would only ever be one)
        assert node.nodeid not in [p.nodeid for p in
                                   self.connectedvia], "Shouldnt ever set connectedvia to incude Node"
        """

    def __repr__(self):
        return "Peer(%d)" % self.nodeid

    def __eq__(self, other):    # Note this facilittes "in" to work on PeerSet's
        if not isinstance(other, int):
            other = other.nodeid
        return self.nodeid == other

    def OLDreqpeers(self):  # Get a list of their peers from this peer and store in cachedpeers
        return sim.find(self).handlereqpeers()  # Returns a dicarray

    def OLDdisconnect(self, connecttheirpeers=False, verbose=False, reason=""):
        """
        Disconnect from this peer
        if connecttheirpeers then consider connecting to any of their peers
        if candidate then only disconnect if we are over limit
        """
        # if debug: print "Disconnecting",self
        # Would disconnect HTTP here
        if verbose: print "Node %d disconnecting from %d because %s" % (self.node.nodeid, self.nodeid, reason)
        self.connected = False
        # Remove any connections onwards since can no longer connect to those cachedpeers via this one we are disconnecting
        for cachedpeer in self.cachedpeers:
            cachedpeer.connectedvia.discard(self)
        if connecttheirpeers:
            print "TODO implement disconnect with connecttheirpeers"

    def connect(self):
        self.transport = TransportHTTP(ipandport=self.ipandport)
        self.connected = True
        #self.node.onconnected(self) #TODO-TX see if need this

    def OLDdict(self):
        return {'nodeid': self.nodeid, 'ipaddr': self.ipaddr}

    def OLDdebugline(self):
        return "Peer %d ip=%d distance=%d connected=%d cachedpeers=%s connectedvia=%s" \
               % (self.nodeid, self.ipaddr or 0, self.distance, self.connected, self.cachedpeers.debugline(),
                  self.connectedvia.debugline())

    def distanceto(self, peerid):
        """
        Return a distance to the peerid, based on a bitwise or of the ids

        :param peerid:
        :return: int 0..Node.bitlength-1
        """
        if isinstance(peerid, (Peer, Node)): peerid = peerid.nodeid
        offset = peerid ^ self.nodeid
        return bin(offset).count("1")

    def OLDsendMessage(self, msg):
        # In real code this would send via HTTP, instead it simulates locally by finding the Node in "sim"
        if msg.hops >= msg.maxhops:
            if msg.verbose: print "Max hops exceeded"
            print "XXX@295 max hops exceeded"
            msg.debugprint()  # XXX comment out
            return PeerResponse(success=False, err="Max hops exceeded", msg=msg)
        return sim.sendMessage(self, msg)  # Ok to simulate sending

    def OLDsetcachedpeers(self, node, pdiclist):
        self.cachedpeers = PeerSet()  # Empty list
        for p in pdiclist:
            existingpeer = node.peers.find(p["nodeid"])
            if existingpeer:
                self.cachedpeers.append(existingpeer)
                if self not in (node, existingpeer) and (node != existingpeer):
                    assert self.nodeid != node.nodeid, "Shouldnt be working on node anyway"
                    existingpeer.connectedvia.append(self)
                    existingpeer.ipaddr = p["ipaddr"]
            else:
                cv = (self,) if self not in (node, p["nodeid"]) else []
                newpeer = Peer(node=node, connectvia=PeerSet(cv), **p)
                self.cachedpeers.append(newpeer)
                node.peers.append(newpeer)

    def OLDcloser(self, other):
        """
        True if self is closer to its node than other
        """
        return self.node.closer(self, other)

    def reqfetch(self, req=None, verbose=False, **options):
        # Do a post of the JSON
        if not self.connected:
            self.connect()
        thttp = self.transport
        # Now send via the transport
        #TODO-TX - make ServerHTTP answer the reqfetch
        resp = thttp._sendGetPost(True, "reqfetch", headers={"Content-Type": "application/json"}, urlargs=[], data=CryptoLib.dumps(req))
        return resp # Return PeerResponse


class OLDNodeList(list):
    """
    List of all nodes for simulation
    """

    def OLDfind(self, nodeid):
        if isinstance(nodeid, (Peer, Node)): nodeid = nodeid.nodeid
        nodes = [node for node in self if node.nodeid == nodeid]
        if nodes:
            return nodes[0]  # Can only be one
        else:
            return None

    def OLDdebugprint(self, level=2):
        for n in self:
            n.debugprint(level=level)

class OLDSim(OLDNodeList):
    def OLD__init__(self):
        super(Sim, self).__init__()

    def OLDreset(self):
        """ Reset for new simulation"""
        self.__init__()  # Empty it out

    def OLDcreatenodes(self, numnodes):
        for n in range(numnodes):
            self.append(Node())

    def OLDcreateconnections(self, numconnects):
        numnodes = len(self)
        for c in range(numconnects):
            nodefrom = self.randnode()
            connectto = self.randnode()
            if nodefrom != connectto:
                peer = nodefrom.seedpeer(nodeid=connectto)
                if peer:
                    nodefrom.onconnected(peer)

    def OLDrandnode(self):
        numnodes = len(self)
        return self[randint(0, numnodes - 1)]

    def OLDfindroute(self, source, destn, maxhops=0, verbose=False):
        # print "source",source,"destn",destn
        msg = PeerRequest(sourceid=self[source], nodeid=self[destn], hops=0, tried=None, maxhops=maxhops,
                          verbose=verbose)
        res = self[source].sendMessage(msg)
        if verbose: print "Success", res.success
        # if not res.success: print "XXX@360",res.err
        return res

    def OLDcountconnections(self, verbose=False, samples=0):
        ok = 0
        tests = 0
        distances = []
        if samples:
            for i in range(samples):
                source = randint(0, len(self) - 1)
                destn = randint(0, len(self) - 1)
                if source != destn:
                    tests += 1
                    msg = self.findroute(source, destn, maxhops=len(self), verbose=verbose)
                    if msg.success:
                        ok += 1
                        # print "XXXtried=",source,destn,msg.tried
                        distances.append(len(msg.tried))
        else:
            for source in range(0, len(self)):
                for destn in range(0, len(self)):
                    if source != destn:
                        tests += 1
                        msg = self.findroute(source, destn, maxhops=len(self), verbose=verbose)
                        if msg.success:
                            ok += 1
                            # print "XXXtried=",source,destn, msg.tried, msg.route
                            distances.append(len(msg.tried))
        if verbose: print "%d/%d" % (ok, tests)
        # print "XXX",distances
        return float(ok) * 100 / tests, median(distances)

    def OLDavgcountconnections(self, nodes, line=False, optiminconnections=None, optimaxconnections=None,
                            verbose=False, samples=0):
        self.createnodes(nodes)
        self.setminmax(optiminconnections or nodes, optimaxconnections or nodes)
        if not line:
            print "nodes,connections,percent,median"
        else:
            print "%d," % nodes,
        had100 = False  # Set to True when have first 100
        for i in range(nodes):
            self.createconnections(nodes)  # Create 1 more (average) connection per node
            self.loop(nodes * 10)  # Randomly do a bunch of optimisation etc
            percent, mediandist = sim.countconnections(verbose=verbose, samples=samples)
            if line:
                print "%d:%d," % (percent, mediandist),
            else:
                print "%d %d %d%% %f" % (nodes, i, percent, mediandist)
            if verbose:
                if percent == 100:  # and not had100:    # XXX put back the "and not had100"
                    print ">"  # End partial line
                    sim.debugprint(level=1)
                    had100 = True
                elif percent < 100 and had100:
                    print "<"  # End partial line
                    sim.debugprint(level=1)
                    1 / 0
                    return
        print "."  # End line

    def OLDloop(self, loops=1):
        for i in range(loops):
            self.randnode().loop()

    def OLDsetminmax(self, min, max):
        for node in self:
            node.setminmax(min, max)

    def OLDsendMessage(self, peer, msg):
        """ Simulate a send """
        destnode = self.find(peer)  # Find the node in the simulator
        return destnode.sendMessage(
            msg.copy())  # Will simulate HTTP call, make copy of message so don't edit in supposedly independant simulation

class PeerRequest(object):  #TODO-TX review this class
    """
    Overloaded dictionary sent to Peers

    verbose     True if should gather debugging info - note this is on a per-message rather than per-node or per-routine basis
    hash        Hash of item being requested
    hops        Number of hops request has been through prior to this.
    route       PeerSet, list of NodeIds it has passed through to reach targer.
    tried       PeerSet, nodes that have been tried while trying to reach destn (superset of route, includes false branches)

    Properties
    targetnodeid Target node id to ask, note in a sparse space this nodeid doesnt exist and we are trying to get close to it
    #!SEE-OTHER-PEERREQUEST-ADD-FIELDS
    """

    def __init__(self, route=None, hash=None, hops=0, tried=None, verbose=False):
        self.hops = hops
        self.route = route or []
        self.tried = tried or PeerSet()  # Initialize if unset
        self.verbose = verbose
        self.hash = hash
        #!SEE-OTHER-PEERREQUEST-ADD-FIELDS
        """
        See how/if these ued
        self.sourceid = sourceid.nodeid if isinstance(sourceid, (Node, Peer)) else sourceid
        self.payload = payload
        self.maxhops = maxhops
        """

    def copy(self):
        return PeerRequest( hash=self.hash, hops=self.hops, route=self.route, tried=self.tried.copy(),
                            verbose=self.verbose)
        #!SEE-OTHER-PEERREQUEST-ADD-FIELDS


    def OLDdebugprint(self, level=2):
        print "To: %d Hops=%d maxhops=%d Route=%s Tried=%s" % (
        self.nodeid, self.hops, self.maxhops, self.route, self.tried,)

    @property
    def targetnodeid(self):
        """
        Find a destination node id based on this request's hash. This node may, but probably won't exist.

        :param hash:
        :return:
        """
        return binascii.crc32(self.hash) & 2^Node.bitlength - 1


class PeerResponse(object):
    """
    Overloaded dictionary returned from Peers with answer, note many fields are in the PeerRequest at .req

    err     Error message if applicable
    data    data to return in response (opaque bytes or json array)
    success True if succeeded, False if failed
    req     Request as present at node which answered it.
    """


    def __init__(self, err=None, data=None, req=None, success=False):
        self.err = err
        self.data = data
        self.success = success
        self.req = req

    def __str__(self):
        return "PeerResponse("+(len(self.data)+"bytes" if self.success else "Fail:"+self.err) +")"

if __name__ == "__main__":
    ServerPeer.setup().serve_forever(ipandport=('localhost',4250), verbose=True)  # TODO-TX-MULTIPLE pass ipandport else uses defaultipandport
    # This (should) never return

