.. _ScalableAPI:

************
Scalable API
************

#TODO-REFACTOR need to scan and update this file

The concept of a Scalable API (or UI) is that simple things are easy to do, and ever more complex things are incrementally more complex.

So a higher level API for applications is desirable, which utilizes the lower level layers.

Starting with the simplest level of complexity.

See also :ref:`API` which may need merging with this file.


From Simple to Complex
======================
Fetch a file - uses the browsers own URL fetcher
    fetches "content" of URL (HTML, PNG etc) via MB, SB, SigB, B
    URL specifies for MB what kind of data wanted. (Content of SB, last or all etc)

Ajax query for JSON - uses browsers own URL fetcher
    fetches Json of URL from from MB or SB.
    URL specifies for MB what kind of data wanted. (Content of SB, last or all etc)

Either File or Ajax via a library call
    All fetches for "Fetch a file' or "Ajax query" possible.

URL format
==========

See :ref:design_url: for logic behind this.

Suggest ...
Feature

==========  ======================  =================
Object      URL                     Stored as
==========  ======================  =================
Mutable     mb/SHA3256.111222       mb/...
Signed      signed/SHA3256.111222   signed/...
Structured  sb/SHA3256.111222       sb/...
==========  ======================  =================

If want to access some part then need to pass further args e.g.

sb/SHA3256.111222/html  to get the html version

Concepts
========

_hash v hash, _data v data
~~~~~~~~~~~~~~~~~~~~~~~~~~
In the various APIs and data stroage you will see data/_data, hash/_hash.
The difference is that data is the data that an object carries e.g. the data portion of a file represented by a StructuredBlock.
_data is the data representation of the object e.g. a JSON of the StructuredBlock's fields.
Similarly, hash is the hash of the data field, while the _hash is the hash of the _data.
The importantance of this is that apart from Block, the _hash can be used as a way to refer to the object.

For the lowest level :ref:`Block` which represents a opaque collection of data, these are the same thing.

block, store, list, fetch
~~~~~~~~~~~~~~~~~~~~~~~~~
#TODO exapand this section: block, store, list, fetch

Layering
========
This section describes how the layers build on each other (since refactor 15 March 2017)

#TODO-REFACTOR - complete this and use to replace other parts of docs

The layers in hte API allow increased levels of abstraction.

* Raw Transport: Transports opaque bytes for blocks, and signature triplets for lists.
    * A raw block is always stored and retrieved by its multihash, there is no knowledge at this level of what it contains (and it may be encrypted)
    * A signature is: hash-obj, date, signature(hash-obj + date), hash-publickey. It is stored in list under both the multihash-obj, and hash-publickey
    * lists can only be appended to, or retrieved.
* Object layer: Specifies what object we have retrieved and want returned.
    * e.g. "SB" would specify wanting the opaque data interpreted as a StructuredBlock
    * This applies to lists as well e.g. retrieving a list of StructuredBlocks
* Function layer: Specifies what we want done with the data returned

Examples
~~~~~~~~
* data/sb/b/123ABC45 says retrieve the bytes at 123ABC45, interpret as JSON into a StructuredBlock, and return the data from the SB
* size/zb/l/123ABC45 says retrieve the list from 123ABC45, interpret the objects as Signed Blocks, and calculate the size.

Scalable implementation
-----------------------
Each layer is (or should be) independantly extendable.

For example to add a new type of object requires
implementing methods for the operations (like data, size) that it supports
and writing new and _data property functions to raw blocks.

Adding a new transport layer requires supporting block, list, store, and add.

Refector Two
============
Unified Transport architecture

fetch(command, cls, hash, path, options) = fetch(-,cls, hash, path, options).command

fetch(-, cls, hash, path, options) = cls(fetch(hash, path, options)

fetch(hash, path, options) = fetch(hash, [], options) -> path

list(command, cls, hash, path, options)  = list.command([list]) where list = list(cls, hash, path, options)
list(cls, hash, path, options) = [ cls(l).path for l in list(-, hash, options) ]
list(hash, options) is primitive

store(command, cls, hash, path, data, options) = fetch(cls, hash, path, options).command(data, options)
store(hash, data)

add(obj, date, key) = add(obj.hash, sig(obj+date, key), date, key.hash)
add(datahash, sig, date, keyhash)

Common API methods (Python)
===========================
The methods lifted here may not be defined on all objects,
but when defined should have the functionality specified to make it easier to read and modify the code,
and to support ducktyping.

content
    Return the "content" of the object, following links and pointers etc. Typically this will be text or binary.

file
    Return the content, but in a dict with meta-data (typically from a top-level StructuredBlock) and especially the "Content-type"

path(urlargs)
    Follow a path represented by the urlargs array and return the node at the end of the path.

size
    Return the size of the content, this may or may not result in the content being retrieved.
    #TODO will probably be made a property.

Common API parameters and Fields (Python)
=========================================

verbose
    If true give debugging output, propogate down to calls.

_data
    The string (or dict or object) representing this object,
    when set it should be interpreted into other parameters e.g. setting args in __dict__, decoding dates etc

data
    The content of the object, distinct from _data which represents the object.

_hash
    The hash of the _data, indicates where the _data can be retrieved.

hash
    Pointer to the content of the object

keypair
    A KeyPair object (might be just the public key)

Extending
=========
To extend
Adding a new Object
-------------------
On top of Structured Block, Smart Dict, Transportable
Adding a new List
-----------------
On top of MB, CommonList

Adding functionality on a list - e.g. Search or Earliest
Adding functionality on a objects e.g. searchable
