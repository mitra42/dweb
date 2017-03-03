.. _Transport:

*********
Transport
*********

The Transport for DWeb is intended to be fully pluggable.
This means that the functionality can be implemented in multiple ways and communicate with the Storage layer via a narrow API.

Transport API
=============

The Transport API is implemented via a few simple primitives.

Conceptually it is implemented on a DistributedDatabase consisting of a set of Distributed Hash Tables (DHT).

setup(**args)
    Instantiate a transport object, parameters to this are transport specific.

block(table, hash, options)
    Fetch an opaque block from a table, whose content corresponds to the hash.

store(table, data) -> hash
    Store a block of opaque data in a table, and return its hash.

add(table, hash, value)
    Add a value to a table under a hash. Logically this is an append.

list(table, hash) -> [ value ] *
    Return a list of values corresponding to those added to the hash.
    Order preservation is not guarranteed.

url(obj, command, hash, table, contenttype=None) -> url string
    A transport dependent function that returns a URL that a browser could use to access the Transport.
    Most relevant to the HTTP transport.