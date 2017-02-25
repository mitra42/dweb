.. _Roadmap:

******
Roamap
******

This is a (rapidly) changing outline of the intended roadmap

* [✔️] Skeleton implementation of classes based on Local Transport.
* [ ] After the Skeleton works, then parallel development can happen on the integration layer and transport layers
* [ ️] Once Integration is working, Sample Applications can be built on top.

Transport Layer roadmap
=======================
* [✔️] TransportLocal - store files in local file system - great for testing skeleton
* [ ] TransportHTTP with a HTTP client and server to store to a centralised server
* [ ] TransportIPFS to transport over IPFS
* [ ] TransportHTTP/IPFS to handle queries over HTTP on a IPFS transport

Storage Layer roadmap
=====================
* [✔️] Block / StructureBlock .... all the classes in the StorageAndRetrieval in that order
* [ ] HTTP/HTTPS hooks at each class
* [ ] Integration with own HTTP server

Integration Layer Roadmap
=========================
* [ ] Test.py a series of tests
* [ ] HTTP gateway - respond to URLs at higher levels than just Transport
* [ ] JavascriptHTTP library - simple JS library to use HTTP transport (quickly enables app dev against gateway)
* [ ] Javascript library - providing full functionality against any active transport layers
* [ ] Browser plugin -

Application Layer Roadmap
=========================
Sample applications to build and prove

* [ ] Facebook like page including a range of functionality
* [ ] Internet Archvie integration - smoothly fetch and retrieve any object