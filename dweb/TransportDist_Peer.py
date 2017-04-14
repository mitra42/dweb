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

class Node(object):
    """
    Represents our node in the peer network.
    Note that a "Peer" is the representation of another node.

    nodeid  Randomly selected nodeid. #TODO use something like IPFS rules for generating node ids
    tl      Transport object to check for local copy - usually TransportLocal
    """
    bitlength=30    # Allowsfor 2^n nodes, so 30 is ~ 1 billion.

    def __init__(self, nodeid=None, tl=None):
        self.nodeid = nodeid if nodeid else randint(1, 2 ** self.bitlength - 1) # Random 10 bit id, #TODO-TX allows only for 1000 nodes, but fine for simulation
        self.peers = PeerSet()  # Will hold list of peers we know about
        self.optimaxconnections = 10    #TODO-TX follow is this used
        self.optiminconnections = 1   #TODO-TX follow is this used
        self.tl = tl

    def __repr__(self):
        return "Node(%d)" % self.nodeid

    def __eq__(self, other):
        if not isinstance(other, int):
            other = other.nodeid
        return self.nodeid == other

    def targetnodeid(self, hash=None):
        """
        Find a destination node id based on a hash. This node may, but probably won't exist.
        :param hash:
        :return:
        """
        return binascii.crc32(hash) & 2^bitlength - 1

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

    """
        #TODO MOVE DOCS TO NODE
        #TODO MOVE DOCS TO PeerRequest
        hash        Hash of item being requested

        Xnodeid      Target node id to ask, note in a sparse space this nodeid doesnt exist and we are trying to get close to it
        Xhops        Number of hops request has been through prior to this.
        Xroute       PeerSet, list of NodeIds it has passed through to reach targer.
        Xtried       PeerSet, nodes that have been tried while trying to reach destn (superset of route, includes false branches)

        #TODO MOVE DOCS TO PeerResponse
        Xsuccess     True if succeeded
        Xmsg         Copy of request as received by final responder (#TODO check this isn't modified during passing back)
        Xerr         Error message if applicable e.g. "Loop"
        #TODO MOVE DOCS TO Peer
        Xconnected   True if node is connected to us (False means we know if it, but aren't conencted)
"""


    def rawfetch(self, hash=None, req=None):
        """
        Fetch content based on a req.
        Algorithm walks a tree, trying to find the "closest" node to the hash, which is most likely to have the content.

        :param req:     PeerRequest object for partially completed request
        :param hash:    hash for new request
        :return:
        """
        if not req:
            #TODO-TX create new request
        elif not hash:
            hash = req.hash
        if self.tl:
            try:
                self.tl.rawfetch(hash, verbose=verbose, **options)
            except: TransportFileNotFound as e:


    def sendMessage(self, msg):
        # TODO-TX .....working through this - needs a rewrite, made simpler for sparse tree.
        """
        Send a message to nodeid
        If its for us, deliver and return 0
        If its directly connected, pass to peer
        If we know how to reach it, send via that node
        If we don't know then send through the closest node we are connected to.
        Returns PeerRespones object to caller
        """
        verbose = msg.verbose
        hops = msg.hops  # Keep a local copy of msg hops at call, don't increment as keep trying to send
        # If we have seen the message before there must be a loop, reject.
        if self.nodeid in msg.route:
            return PeerResponse(success=False, msg=msg, err="Loop")

        msg.route.append(self.nodeid)  # Append self to route before sending on, or responding (except in case of loop above).

        # Check if request is for this node.
        #TODO-TX review this chunk, there is no "This" when going for sparse set of targets, should be if have in Local
        if msg.nodeid == self:
            if verbose: print "Message received at nodeid", msg.nodeid
            msg.hops += 1
            return PeerResponse(success=True, msg=msg)

        else:
            #TODO-TX this section needs rethink as there won't be a specific node.
            peer = self.peers.find(msg.nodeid)  #TODO-TX follow call
            if peer:
                if peer.connected:
                    # Can't have been "tried' since its the destination
                    if verbose: print self, "Sending to peer", msg.nodeid
                    msg.hops = hops + 1
                    msg.tried.append(peer)
                    return peer.sendMessage(msg)  # Response should reflect updated hops    #TODO-TX follow call
                else:  # Not connected, but we know of it
                    # target is not connected but we know of it, so try anything that it is connectedvia that we are connected to and haven't already tried.
                    for intermediate in peer.connectedvia.connected().notin(msg.tried):
                        msg.tried.append(intermediate)
                        if verbose: print "Sending to intermediate", intermediate, "for", msg.nodeid
                        msg.hops = hops + 1
                        msg.tried.append(intermediate)
                        res = intermediate.sendMessage(msg)
                        msg.tried.append(
                            res.tried)  # Accumulate any places it tried (should already include everything tried previously)
                        if res.success: return res  # Return if successful else will try others
                        # If none of them work, drop through and try for closest
            # Try all connected nodes, in order of how close to target
            intermediate = self.peers.connected().closestto(msg.nodeid, exclude=msg.tried)
            while intermediate:
                if verbose: print self, "Sending via closest", intermediate, "for", msg.nodeid
                msg.tried.append(intermediate)
                msg.hops = hops + 1
                res = intermediate.sendMessage(msg)
                if res.success: return res
                msg.tried.append(res.tried)
                if verbose: print self, "Retrying from ", self.nodeid, "to destn", msg.nodeid, "with excluded", msg.tried
                intermediate = self.peers.connected().closestto(msg.nodeid,
                                                                exclude=msg.tried)  # Try next closest untried
            # Tried all of them - fail
            if verbose: print self, "No next step towards", msg.nodeid
            return PeerResponse(success=False, msg=msg, err="No route to host")

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

    def OLDconnected(self):
        return PeerSet([peer for peer in self if peer.connected])

    def OLDnotconnectedandnotviapeer(self):
        return PeerSet([peer for peer in self if not peer.connected and not peer.connectedvia])

    def OLDconnectedandviapeer(self):
        return PeerSet([peer for peer in self if peer.connected and peer.connectedvia])

    def OLDconnectedandviacloserpeer(self):
        return PeerSet([peer for peer in self if
                        peer.connected and peer.connectedvia and any([p.closer(peer) for p in peer.connectedvia])])

    def OLDnotconnected(self):
        return PeerSet([peer for peer in self if not peer.connected])

    def OLDnotin(self, ps):
        ps_ids = [peer.nodeid for peer in ps]
        return PeerSet([peer for peer in self if peer not in ps_ids])

    def OLDfind(self, nodeid):
        if not isinstance(nodeid, int): nodeid = nodeid.nodeid
        peers = [peer for peer in self if peer.nodeid == nodeid]
        if peers:
            return peers[0]  # Can only be one
        else:
            return None

    def OLDappend(self, peer):
        if not isinstance(peer, (list, set)):
            peer = (peer,)
        self.update(peer)

    def OLDdebugline(self):
        return str([p.nodeid for p in self])

    def OLDclosestto(self, nodeid, exclude=None):
        dist = 99999
        closestpeer = None
        excludeids = [peer.nodeid for peer in exclude] if exclude else []
        for peer in self:
            if (peer.nodeid not in excludeids) and (peer.distanceto(nodeid) < dist):
                dist = peer.distanceto(nodeid)
                closestpeer = peer
        return closestpeer

    def OLDfurthestfrom(self, nodeid):
        dist = 0
        furthestpeer = None
        for peer in self:
            if peer.distanceto(nodeid) > dist:
                dist = peer.distanceto(nodeid)
                furthestpeer = peer
        return furthestpeer

    def __str__(self):
        return str([p.nodeid for p in self])

class OLDPeer(object):
    """
    One for each node we know about.
    Applies to both connected and disconnected peers.
    """

    def OLD__init__(self, node=None, connectedvia=None, nodeid=None, ipaddr=None, **parms):
        self.connected = False  # Start off disconnected
        self.cachedpeers = PeerSet()
        self.connectedvia = connectedvia if connectedvia else PeerSet()  # List of peers connected via.
        self.nodeid = nodeid
        self.ipaddr = ipaddr  # Where it is on the network
        self.distance = node.distance(self)
        self.node = node  # Parent node (in non Sim there would only ever be one)
        assert node.nodeid not in [p.nodeid for p in
                                   self.connectedvia], "Shouldnt ever set connectedvia to incude Node"

    def OLD__repr__(self):
        return "Peer(%d)" % self.nodeid

    def OLD__eq__(self, other):
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

    def OLDconnect(self):
        self.connected = True
        # TODO - would connect via HTTP here
        self.node.onconnected(self)

    def OLDdict(self):
        return {'nodeid': self.nodeid, 'ipaddr': self.ipaddr}

    def OLDdebugline(self):
        return "Peer %d ip=%d distance=%d connected=%d cachedpeers=%s connectedvia=%s" \
               % (self.nodeid, self.ipaddr or 0, self.distance, self.connected, self.cachedpeers.debugline(),
                  self.connectedvia.debugline())

    def OLDdistanceto(self, peerid):
        if isinstance(peerid, (Peer, Node)): peerid = peerid.nodeid
        offset = peerid ^ self.nodeid
        return bin(offset).count("1")

    def OLDsendMessage(self, msg):
        # In real code this would send via HTTP, instead it simulates locally by finding the Node in "sim"
        if msg.hops >= msg.maxhops:
            if msg.verbose: print "Max hops exceeded"
            print "XXX@295 max hops exceeded"
            msg.debugprint()  # XXX comment out
            1 / 0
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

class OLDSim(NodeList):
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

    verbose True if should gather debugging info - note this is on a per-message rather than per-node or per-routine basis
    """
    # TODO-TX document these fields above

    def __init__(self, sourceid=None, route=None, nodeid=None, hops=0, tried=None, verbose=False, maxhops=100,
                 payload=None):
        self.sourceid = sourceid.nodeid if isinstance(sourceid, (Node, Peer)) else sourceid
        self.nodeid = nodeid.nodeid if isinstance(sourceid, (Node, Peer)) else nodeid
        self.hops = hops
        self.tried = tried or PeerSet()  # Initialize if unset
        self.verbose = verbose
        self.payload = payload
        self.maxhops = maxhops
        self.route = route or []

    def copy(self):
        return PeerRequest(sourceid=self.sourceid, route=self.route, nodeid=self.nodeid, hops=self.hops,
                           tried=self.tried.copy(),
                           verbose=self.verbose, maxhops=self.maxhops, payload=self.payload)

    def OLDdebugprint(self, level=2):
        print "To: %d Hops=%d maxhops=%d Route=%s Tried=%s" % (
        self.nodeid, self.hops, self.maxhops, self.route, self.tried,)

class PeerResponse(object):
    """
    Overloaded dictionary returned from Peers with answer
    """
    # TODO-TX document these fields above

    def OLD__init__(self, err=None, payload=None, msg=None, success=False):
        self.hops = msg.hops
        self.err = err
        self.payload = payload
        self.tried = msg.tried
        self.success = success
        self.route = msg.route

OLDsim = Sim()

def OLDmedian(lst):
    return numpy.median(numpy.array(lst))

def OLDtest_generic():
    """
    Workout some of the functionality
    """
    sim.append(Node())  # Create one Node
    sim.append(Node())  # Create second Node
    sim.append(Node())  # Create third Node
    assert sim[0].handlereqpeers() == [], "Should be empty"
    peer01 = sim[0].seedpeer(nodeid=sim[1].nodeid)
    peer20 = sim[2].seedpeer(nodeid=sim[0].nodeid)
    peer21 = sim[2].seedpeer(nodeid=sim[1].nodeid)
    # sim.debugprint(level=2)
    # print "---"
    sim[0].onconnected(peer01)
    # sim.debugprint(level=2)
    # print "---"
    sim[2].onconnected(peer21)
    sim[2].onconnected(peer20)
    sim.debugprint(level=2)
    print "---"

def OLDtest_sim3():
    sim.avgcountconnections(2000, samples=10)

def OLDtest_sim2():
    nodes = 200
    connections = nodes * 10
    loops = nodes * 10
    sim.createnodes(nodes)
    sim.setminmax(int(nodes / 10), int(nodes / 5))
    sim.createconnections(connections)
    sim.loop(loops)
    percent = sim.countconnections()
    print "nodes=%d connections=%d loops=%d percent=%d" % (nodes, connections, loops, percent)

def OLDtest_sim30():
    """
    Simulate a series of nets, each with larger numbers of nodes.
    For each net, incrementally add connections (1 per node on average, but added randomly so some nodes have more than others),
    And report the percentage of connections that are possible
    """
    inc = 2  # How
    nodes = 1000
    for i in range(1, int(nodes / inc)):
        sim.reset()  # Clear Sim back to zero
        sim.avgcountconnections(i * inc, line=True, verbose=False, samples=10)