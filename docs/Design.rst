***************
Design Thinking
***************

This page is intended to summarise key design thinkng so that if something is going to be changed the reasoniong behind
the choices made is more apparant than it might be from just reading the spec.

.. _design_url:

URL Design
----------
What should a URL look like for this.

Logic goes ...

* Browser needs to be able to distinguish between requesting JSON or requesting content.
* Need the library and/or gateway and/or server to know what the data and the hash represent. For example it needs to know whether it already is content,
  or its JSON from which can pull content, or its a MutableBlock.
* For URLs there may be no library, so the gateway has to know, and it may be accessing blocks via a decentralized transport.

For simple functions that are the minimum set of functions a transport layer has to provide I defined a simple format e.g. */rawfetch/hash -> data*
or */rawstore, data -> hash*  allowing for very minimal interfaces with a underlying transport mechanism.

For more complex functions, I defined an extensible format: */command/class/hash/path?arguments* where:
* *hash* defines the data to retrieve
* *class* is a two or three-letter code defining which class to pass the data to, e.g. "sb" for StructuredBlock
* *path* is a path within objects of some class, allowing relative URLs
* *command* is a function that can be applied to the resulting object.

E.g. */file/sb/A1B2C3/foo/index.html*  will: find object A1B2C3;
turn it into a StructuredBlock (which interprets the raw data as a JSON dictionary);
look for the "index.html" link within the "foo" link;
and apply the "file" command to it.

This allows for a more complex set of functions that can be performed on a HTTP gateway,
allowing web pages to embed quite sophisticated URLs as a common core of functions are developed.

Class Hierarchy
---------------
The class hierarchy as currently implemented is:

* Dweb - overview class, top level entry point.
* Transportable - base class for anything that can be stored and retrieved over the file system

  * Block - opaque bytes
  * SmartDict - base class for things that are stored as JSON

    * UnknownBlock - temporary object when dont know class till have parsed the JSON
    * StructuredBlock - general class for JSON object, has a few known fields (_signatures)

      * File - manage handling a file (Python only)

        * Dir - subclass of File for directories  (Python only)

    * Signature - encapsulates a signature (something signs something else)
    * KeyPair - hides the crypto library and manages a set of relate keys (e.g. public, and private)
    * CommonList - base class for any list management

      * KeyChain - manages a collection of KeyPairs that give the user access to things
      * MutableBlock - publishing, maintains a version list (May get renamed VersionList)
      * AccessControlList - manages a collection of encrypted access keys for entities who can view/modify something
      * EncryptionList - ??? (Python only)

* Signatures - list of Signature (JS only)

* Error (JS) MyBaseException (Python) - Base class for errors

  * TransportError - something went wrong sending or receiving (JS only)
  * ForbiddenError (JS) ForbiddenException (PY) - the user is not allowed to do something (usually nobody is allowed to) (JS only)
  * AuthenticationError (JS) AuthenticationException (PY) - action failed to authenticate (e.g. no keys in an ACL)
  * SignedBlockEmptyException - (Python only)
  * ToBeImplementedException - (Python only)
  * AssertionFault - (Python only)
  * ObsoleteException - (Python only)
  * PeerCommandException - error in commands in TransportPeer (Python only)
  * TransportBLockNotFound - (Python only)
  * TransportURLNotFound - (Python only)
  * TransportFileNotFound - (Python only)
  * TransportPathNotFound - (Python only)
  * TransportUnrecognizedCommand - (Python only)
  * HTTPdispatcherException - (Python only)
  * HTTPargrequiredException - (Python only)
  * DwebMalformedURLException - (Python only)
  * PrivateKeyException - (Python only)
  * DecryptionFail - (Python only)
  * SecurityWarning - (Python only)

* CryptoLib - encapsulation of Crypto functionality, hide innards of crypto libraries (libsodium)

* Transport - base class for each transport class

  * TransportHTTPBase - base class for HTTP oriented classes (methods to send and retrieve queuries)

    * TransportHTTP - transport over HTTP to our own internal spec

  * TransportIPFS - transport over IPFS and it's PubSub
  * TransportLocal - store and retrieve in local file system (Python only)
  * TransportDistPeer - experimental sandbox for peer HTTP request transport (Python only)

* MyHttpRequestHandler, ThreadedHTTPServer - generic handler for HTTP requests (python only)

  * ServerPeer - implement server side of TransportPeer

* Testing - generic test class (python only)

* Peer, PeerSet, PeerRequest, PeerResponse - parts of TransportDistPeer & ServerPeer (Python only)
* WordHashKey - internal key based on mnemonics, deprecated  (Python only)
