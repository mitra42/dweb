.. _Roadmap:

******
Roamap
******

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

* REFACTOR: Multihash - find spec, and replace format of hashes
* DOCS: cover principles like _hash v hash
* DOCS: Pass through docs, check all current
* DOCS: Find out how to document Javascript in Sphinx / .rst
* CORE: Directories and relative links
    * Upload directory
        * Python routine (start in test.py) that can accept dir
        * API or class for that routine
        * Build into TransportHTTP, TransportLocal, ServerHTTP
        * Javascript version of above - library based
        * Javascript version URL based
    * Retrieve relative URLs
        * Requires URL handler on HTTPServer to recognize relative URLs e.g. hash/relative
    * Demo
        * Demo on index.html with a relative image
    * Cleanup
        * Then See section below waiting on this
* FUNCTIONALITY: Work with P2P transport, probably IPFS
* FUNCTIONALITY: Add authentication layer
* DEMO: Improve visuals of MCE demo
* DEMO: Initialize content of MCE Editor to thing it is editing.
* DEMO: Add a refresh button, and attach to list.
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

Waiting on
----------
Waiting on directories and relative links
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* FUNCTIONALITY: MCE running in the Dweb
    * Reqs: Directories+Relative
* FUNCTIONALITY: Uploader for a directory.
    * Reqs: Directories+Relative
* APP: Drop-to-upload an icon, that runs maybe the python library that you can drop a file or directory on
    * Reqs: Directories & relative links; Uploader for a directory
* APP: Blog like function, building on editor.
    * Reqs: Smarter formating of SB's (e.g. who/when/what in a blog entry)

Waiting on Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~
* APP: Forum
    * Reqs: Authentiction, Blog
* SECURITY: Add Authentication/Encryption to private key store for MBM


