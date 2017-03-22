:: _API:

****************************************
Locking the Web Open - API Documentation
****************************************

This covers some very early drafts of API's required for the Locking the Web Open Project.

The project defines some modules, and the relations between them in terms of the services that modules provide.
I envision this document evolving considerably, and so it will also contain TODO's for suggested areas of expansion.
In particular I expect modules will be expanded to include sub-modules and their APIs.

See also :ref:`ScalableAPI` which may need merging with this file.

Terminology
===========
In this document, the terms Decentralized Web (dWeb) is used to refer to the Locked Open Web.

Design Criteria for API's
=========================
* Allow individual sections to evolve independently, i.e. be prescriptive about what services are provided, not about how.
* Make pointers etc self describing, so that for example different versions of transport can easily be refered to

High level overview
===================

Integration
===========
Integrating at the top level between the Decentralized Web (dWeb) and the Old Web (oWeb) e.g. browsers.
Moved to its own file :ref:`Integration`

Storage and retrieval
==========================
Storage and Retrieval breaks down into a number of topics that are mutually interdependent.


* :ref:`Raw Block storage and retrieval` - storing opaque bytes into a DHT
* :ref:`Structured data retrieval` - storing JSON as blocks in the DHT
* :ref:`Mutable data storage and retrieval` - storing objects that can change
* :ref:`File storage and retrieval` - storing files as a single block with Meta Data
* :ref:`Large File storage and retrieval` - storing large files a list of blocks
* :ref:`Signing, Encryption and Authentication` - Signing and Encrypting structured blocks
* :ref:`Addressing` - how  to refer to a object of any kind
* :ref:`Meta Data` - the descriptive elements of a file
* :ref:`Extra Security` - how to layer on extra security when needed
* :ref:`Applications` - some examples of how the parts fit together in use

#TODO Update this list from that in the top of :ref:`Storage and retrieval`
