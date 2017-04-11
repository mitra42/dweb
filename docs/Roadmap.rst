.. _Roadmap:

******
Roamap
******

#TODO-REFACTOR need to scan and update this file


This is a (rapidly) changing outline of the intended roadmap

* [✔] Skeleton implementation of classes based on Local Transport.
* [ ] After the Skeleton works, then parallel development can happen on the integration layer and transport layers
* [ ] Once Integration is working, Sample Applications can be built on top.

Transport Layer roadmap
=======================
* [✔] TransportLocal - store files in local file system - great for testing skeleton
* [✔] TransportHTTP with a HTTP client and server to store to a centralised server
* [ ] TransportIPFS to transport over IPFS
* [ ] TransportHTTP/IPFS to handle queries over HTTP on a IPFS transport

Storage Layer roadmap
=====================
* [✔] Block / StructureBlock .... all the classes in the StorageAndRetrieval in that order
* [ ] HTTP/HTTPS hooks at each class
* [✔] Integration with own HTTP server

Integration Layer Roadmap
=========================
* [✔] Test.py a series of tests
* [ ] HTTP gateway - respond to URLs at higher levels than just Transport
* [✔] JavascriptHTTP library - simple JS library to use HTTP transport (quickly enables app dev against gateway)
* [~] Javascript library - providing full functionality against any active transport layers
* [ ] Browser plugin -

Application Layer Roadmap
=========================
Sample applications to build and prove

* [ ] Facebook like page including a range of functionality
* [ ] Internet Archvie integration - smoothly fetch and retrieve any object

TODO LIST
=========
This list is at a much finer lever of granularity than Roadmap above.

* FUNCTIONALITY: Add authentication layer
    * See Authentication.rst
    * Do in Javascript
    * Do via gateway (and try in browser)
    * Embed on index and test pages
* REFACTOR: generic lists and reverse on any object,
    * i.e. maybe CommonList and SmartDict;
    * make MBM just signatures, not ordered into Struct Blocks, can still take -1 element for current
* REFACTOR
    * onloaded ... options = methods to call on results, each takes an options e.g. {list: {fetchlisted: true, addlistto: el}} says do a list, then pass its onlisted the fetchlisted, addlisto
* FUNCTIONALITY - add caching, so dont reload, BUT disable for testing
* FUNCTIONALITY - storing some content in lists and allowing searches of that content (listfind ? a=b c=d
* DOCS: Pass through docs, check all current  (done API-Integration)
* DOCS: Complete "To extend with ... new obj,
* FUNCTIONALITY: Work with P2P transport, probably IPFS
* DEMO: Improve visuals of MCE demo
* DEMO: Initialize content of MCE Editor to thing it is editing.
* DEMO: Add a refresh button, and attach to list.
* DOCS: Document Javascript.rst in Sphinx  (done functions, need classes)
* REFACTOR: Python Transport API to use threads and callbacks
* DEMO: Ability to upload an image (from a File selection box) and get URL
* DEMO: Ability to upload in MCE (see https://www.tinymce.com/docs/get-started/upload-images/)
    * Probably Requires Ability to upload an image and get URL
* FUNCTIONALITY: Ability to delete an element of a list (via a deleted entry), and clearing list of all earlier.
* DEMO: Test long files
* REFACTOR: Support streaming of long files across various places inc Block
* SECURITY: Add support for HTTPS
* REFACTOR: Python - move all printing to "logger"
* JAVASCRIPT: Turn incoming dates in JSON into JS date (though can compare strings)
* SECURITY: Verify signatures in JS
* APP: Browser plugin that recognizes URLs
* REFACTOR StructuredBlock has to handle different kinds of sub-pointers which means "hash" may need table and hash in .hash
* FUNCTIONALITY: JS/Browser Uploader for a directory.
* APP: Drop-to-upload an icon, that runs maybe the python library that you can drop a file or directory on
* APP: Blog like function, building on editor.
    * Including: Smarter formating of SB's (e.g. who/when/what in a blog entry)
* DOCS: Explain block, store, list, fetch in StructuredAPI.rst
* DOCS: Write README.rst
* CORE FUNCTIONALITY - Notification mechanism

Waiting on
----------

Waiting on External factors
~~~~~~~~~~~~~~~~~~~~~~~~~~~
* REFACTOR: Multihash - find spec, and replace format of hashes
    * Several broken aspects of it need fixing first - wont work with Sha3; doesnt handle >127 chars


Waiting on Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~
* APP: Forum
    * Reqs: Authentiction, Blog
* SECURITY: Add Authentication/Encryption to private key store for MBM


