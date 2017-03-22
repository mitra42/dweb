********
Glossary
********

#TODO scan all docs looking for abbreviations that might confuse.

.. glossary::

    ACL - Access Control List
        Some kind of data structure that lists who, has access to what resource. (See :ref:`Authentication`

    CAFS - Content Addressable File System
        Often but not always a `DHT`. A system in which a file or data `Block` can be addressed by a hash of its contents.

    DHT - Distributed Hash Table
        A distributed database that can map hash's to one or more values.
        Sometimes will also be a CAFS i.e. sometimes the hash refers to a unique set of bytes.

    DSHT: Distributed Sloppy Hash Table
        TODO Needs definition  - I think its defined in IPFS.

    dWeb - Decentralized Web
        A web that is not subject to any single points of failure

    IPFS - Inter Planetary File Systems
        A distributed file system, open-source, has many features that can be built on here,
        though made some different optimisations.
        Documented in ipfs-p2p-file-system.pdf (TODO need link)

    IPNS - Inter Planetary Name System
        A distributed naming system, it doesnt appear to have what is needed for the Mutable Object requirements of a distributed web.
        Though it might be a good way to to top-level naming.
        Documented in ipfs-p2p-file-system.pdf (TODO need link)

    JSON
        Common simple format for representing data structures (especially dictionaries, and lists) in text.

    Merkle DAG: Distributed Acyclic Graph
        A graph that assumes nothing refers to anything higher up the graph.
        Note that the hashes used in IPNS are acyclic, as cannot put a link to the top in a node.

    oWeb: Old Web
        A shorthand for how things are done now, existing browsers and servers etc.

    SCTP: Stream Control Transmission Protocol
        TODO I believe this is a reference in IPFS - review if useful

    uTP: Utorrent Transport Protocol
        Built on UDP, restricts size of in-flight queue (packets sent but not ack-ed)

    WebRTP: Real time protocol over web
        A protocol suiotable, after NAT traversal for Peer-to-Peer communication.
        Typically requires centralized rendezvous points, but maybe able to solve that.

