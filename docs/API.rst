****************************************
Locking the Web Open - API Documentation
****************************************

This covers some very early drafts of API's required for the Locking the Web Open Project.

The project defines some modules, and the relations between them in terms of the services that modules provide.
I envision this document evolving considerably, and so it will also contain TODO's for suggested areas of expansion.
In particular I expect modules will be expanded to include sub-modules and their APIs.

Terminology
===========
In this document, the terms Decentralized Web (dWeb) is used to refer to the Locked Open Web.

Design Criteria for API's
=========================
* Allow individual sections to evolve independently, i.e. be prescriptive about what services are provided, not about how.
* Make pointers etc self describing, so that for example different versions of transport can easily be refered to

Integration
===========
Integrating at the top level between the Decentralized Web (dWeb) and the Old Web (oWeb) e.g. browsers.
Moved to its own file *<Insert link>*


Storage and retrieval
==========================
Storage and Retrieval breaks down into a number of topics that are mutually interdependent.

#TODO Update this list from that in the top of :ref:`Storage and retrieval`


* Storage and retrieval of immutable blocks. Those blocks could be opaque, or have a defined structure (e.g. JSON meta-data)
* Structured data and retrieval
* Extension of that to retrieve mutable data e.g. a "Home page" or "News feed" or just a document that changes
* Extension to include large "files" that extend across multiple blocks.
* Signing and Authentication
* Addressing
* Meta-Data



