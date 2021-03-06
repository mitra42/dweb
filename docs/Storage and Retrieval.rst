.. _Storage and retrieval:

*********************
Storage and retrieval
*********************

#TODO-REFACTOR need to scan and update this file

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

Note that any storage mechanism relies on one or more underlying transport mechanisms, but they should be transparant to the API.

A quick note on IPFS, it has made some smart decisions about extensible APIs,
where there is no good reason not to, this API will use the same syntax as IPFS, and comment on differences.

A note on the BNF - since much is refering to fields in dictionaries I use constructs like   xyz ::= 'XXX': 'YYY'

.. _Raw Block storage and retrieval:

Raw Block storage and retrieval
===============================
The simplist API is the retrieval of an immutable block of (opaque) data, addressed by its content.

This can be implemented on top of any of several transport layers, and - along with the ability to publish to a list,
form the core primitives on which all of the dWeb works.

It needs to be extensible / transport independent, so at this level it is as simple as storing and retrieving with no knowledge of
how it is implmented.

Functional level
----------------
.. parsed-literal::

    block(:any:`Multihash`) -> :std:token:`Block`;
    store(:std:token:`Block`) -> :any:`Multihash`

.. productionlist::
    Block: `OpaqueBlock` | `StructuredBlock`
    OpaqueBlock: `bytes`
    Multihash: `functionCode` `digesrLength` `digestBytes`
             :# Self describing hash, (copied from IPFS)
             :# TODO Find and provide example from IPFS
    functionCode: # IPFS function code used in multihash - TBD
    digestLength: integer
    digestBytes: `bytes`


Implementation on top of IPFS
-----------------------------
This is different from IPFS's interface in that dWeb intentionally doesn't distinguish between small and large chunks of data.
Ideally a chunk of data is stored at the appropriate node(s) of the DHT,
while under IPFS a larger block (>1kbytes) is stored locally and its availability advertised.
By storing locally this creates the same issues BitTorrent and presumably IPFS has with the long tail of blocks, and non-reputability.
However, dWeb could be implemented on IPFS, allowing IPFS to decide when to store locally, and when to distribute.

Implementation would look something like:

.. parsed-literal::

    def store(:std:token:`Block`):
        :std:token:`Multihash` = multihash(:std:token:`Block`)    # Get the hash of the block
        storelocal(:std:token:`Multihash`, :std:token:`Block`)    # Save it locally
        IPFS.ProvideValue(:std:token:`Multihash`)        # Tell the IPFS DHT its available.
    def block(:std:token:`Multihash`):
        peers = IPFS.ValuePeers(:std:token:`Multihash`)
        ??? then somehow fetch the data (its unclear what the IPFS API call to do this is).



Implementation on top of HTTP/HTTPS
-----------------------------------
* <these are just notes>
* Allow for distributed / non-distributed implementation
* Any dWeb server should be able to store/retrieve

.. _Structured data retrieval:

Structured data retrieval
=========================
Structured data retrieval builds on (opaque) block storage
except that structured (JSON) data is returned.
There are implicit assumptions that the data returned can be interpreted by higher levels.
This means that the data self describes in a form that allows unambiguous interpretation.

Options are to be defined at higher levels to tune this, for example they could specify to check any signatures found.

Functional level
----------------

.. parsed-literal::

    json(:std:token:`Multihash`, options) -> :std:token:`StructuredBlock`
        # Use block('Multihash') to retrieve, then parse JSON
    store(:std:token:`StructuredBlock`, options) -> :std:token:`Multihash`

It follows Python rules for data structures, esp order is significant in a list, but not in a dictionary,
and that only one instance of any field in a dictionary is allowed.

Ideally any consumer of the dictionary should allow for receiving a single value or an array e.g.::

    "title": [ "The Small Prince", "Le Petit Prince"]

In general the fields are either defined in the :any:`Meta Data` or other sections here.

.. productionlist::
    StructuredBlock : `JsonDict`
    JsonDict: `dictionary`

.. _Mutable data storage and retrieval:

Mutable data storage and retrieval
==================================
The requirement for mutable data is to cover anything that may change,
this includes files that get updated, lists that are added to etc.

A mutable object can't use Content Addressability since the content changes,
so it draws on private key/public key pairs.
Possession of the Private Key provides the ability to publish to the address which is the Public Key

Mutable Objects are implemented as Lists where each item is dated and signed.

This allows a range of applications all based on the ability to retrieve a list or its most recent element.

* A simple, changing object such as a home page, or a weather report,
  is retrieved by requesting the most recent item published to a list.
* Feeds, such as news feeds, blogs, or for example my Facebook home
  are requested by asking for the most recent nn items of a list.
* Previous versions can be requested by requesting all the items of a list.
* TODO add functionality for deleting specific items (via a "deleted" entry), and Clearing a list of all earlier.

.. parsed-literal::

    MutableBlock { _key: :std:token:`KeyPair`, _current: :std:token:`SignedBlock`,
                   _list: [ :std:token:`SignedBlock` ]* }

Chain linking
-------------
An additional layer of security can be added via a chain, where a recent item refers to previous ones.
When the full list is retrieved the chain can be checked to make sure all items have been retrieved.
Chains could also be used without dates, but this would slow down retrieval, and lead to errors if an intermediate item disappears.

Functional level
----------------
.. parsed-literal::
    mutableoject(:std:token:`MutableReference`) -> :std:token:`MutableBlock`
    store(:std:token:`MutableReferenceMaster`, :std:token:`MutableListEntry`) -> :std:token:`Multihash`

.. productionlist::
    MutableBlock: [PrivateKey] PublicKey `MutableOptions` `SignedBlock` [ `SignedBlock` ]*
    MutableOptions: "options": "LAST" | "ALL"  [ int ]

Comparisom to IPFS/IPNS
-----------------------
This is very different from IPFS's implementation - "IPNS". The core differences are:

* IPNS stores at a single hash value, which I think is on the owning node (single point of failure).
* In IPNS a completely new object is published each time making list addition expensive.
* TODO talk to Juan @ IPFS/IPNS before discarding

.. _File storage and retrieval:

File storage and retrieval
==========================
Files are stored via the Structured data retrieval, i.e. as JSON for example:

.. parsed-literal::

    "name": "Foo Bar", # Name of file
    "date": "2014-09-20 12:44:06Z"  # Date TODO convert to ISO
    "size": 123455,
    "data": "<html><head>..... </html>"

The fields are :any:`Meta Data`, as defined below.

The content can alternatively be included as a reference:

.. parsed-literal::

    "hash": :any:`Multihash`

.. productionlist::
    File: `StructuredBlock`
        : `MetaData` `Content`
    Content: `ContentInline` | `ContentReference` | `ContentLinks`
    ContentInline: "data": `bytes`
    ContentReference: "hash": `Multihash`

.. _Large File storage and retrieval:

Large File storage and retrieval
================================
Large files are stored as a list of blocks, each of which can optionally have metadata. For example:

.. parsed-literal::

    {
        "name": "My big file",
        "size": 123456,
        "links": [
            { "data": "<header data>...", "size": 56 }
            { "hash": "xxx:16:A1B2C3", "size": 120000 },
            { "hash": "xxx:16:X1Y2Z3", "size": 3400 }
        ]
    }


.. productionlist::
   ContentLinks: "links": `ContentLink`*
   ContentLink: `ContentReference` `MetaData`


At this point this is slightly different from other similar formats (IPFS, Git)
and presumably (needs research) different from Bittorrent's Magnet links.

There is no system-defined size at which files need splitting up into smaller blocks, it will be determined in practice,
but there needs to be a balance between speed of opening new connections, and parrallelism.
In practice with web downloads around 1-5ms/kB Currently I'm thinking optimal is probably around 500kbytes as a size for
recommended in single block, with larger files split into a max of say 10-100 segments,
but the right answer could be orders of magnitude out from this guess.

Comparisom to IPFS
------------------
This section has similar needs to that in IPFS (as defined in Draft 3), but not exactly the same, it would be good to combine them. Specifically:

* IPFS has blob, list, tree, commit. These dont appear to be self-describing, only way to tell is retrieve and check type of data field
* The format proposed above is self-describing,
* Blob, List, Tree, Commit have sizes for sub-objects, but not for the aggregate.
* References are done via hash, not Multihash.
* In IPFS "data" field can be either bytes, or array of types or a dictionary, which seems strange overload,
  would prefer to have data always be opaque bytes, and links be an array of self-describing sub-sections.
* For a IPFS "list" it requires a data field to describe the types of the data, then a links field for the hashs,
  why not make the elements of the links field self-describe.
* Need to be able to include links to mutable inside immutable, (which is why need something multihash as destination of hash).
* Meta-data is needed outside the file, so that the contents can be interpreted appropriately, this is required even for the small file.


.. _Signing, Encryption and Authentication:

Signing, Encryption and Authentication
======================================
Encryption
----------
An encrypted object is just transformed bytes, along with information to help identify what key to use to decrypt them.

.. productionlist::
    EncryptedObject: `EncryptedContent` `EncryptionTag`
    EncryptedContent: `StructuredObject`
    EncryptionTag: "tag": `EncryptionTagBody`
    EncryptionTagBody: bytes

: #TODO decide how to make this self-describing

* Based to a certain extend on IPFS Draft 3.5.4, which has unclarity about field names in the object.
* Its unclear to me if we need meta-data outside the encrypted object to know how to interpret the bytes.
  I think this is optional, and in its abscence the bytes are assumed to be a Strucuture Object (i.e. JSON dict) and interpreted accordingly.
* Unclear if we need more definition on the "tag" I think this, like :any:`Multihash`, should be a self describing indication
  eg. of the key's name or the Public Key used or a hash of it.
* TODO - make retrieval decrypt

Signing
-------

A signed object contains untransformed bytes, along with a Public Key of the signer, and a date
all a signature says is that the owner of the Public Key (i.e. possessor of the Private Key) confirms the content.

A signed block may contain multiple, independent signatures.

Signed = { StructuredBlock|Hash, signatures: { date: ISO, signature: hex  publickey: hex }

.. productionlist::
    SignedBlock: `StructuredBlock`|`Hash` `SignatureDict`*
    SignatureDict: Date Signature PublicKey Hash?
    Signature: bytes # PrivateKey.decrypt(Date Hash)
    KeyPair: PublicKey PrivateKey
    PublicKey: "publickey": `Multihash`
    PrivateKey: "privatekey": `Multihash`
    Date: bytes   # iso formated or datetime

* Based to a certain extend on IPFS Draft 3.5.4, which has unclarity about field names in the object.
* Dating is added to facilitate Mutable Objects.
* Signatures are automatically verified wherever appropriate

Delegation
----------
* <these are just notes>
* Add te concept of signature delegation. Where A signs a block that includes a signed statement by B authorising A to sign.

Authentication
--------------
* <these are just notes>
* Authentication describes who can access an object, it needs to build on Encryption and signing.

Comparisom to IPFS (Draft 3, 3.5.4)
-----------------------------------
* IPFS defines the type, not the representation in a "EncryptedObject" or :std:token:`SignedBlock` so a little hard to interpret
* I'm assuming it is represented as a dictionary but it would be good to get exact syntax
* IPFS allows a single signature on content, we use an array to allow multiple signatures of the same data.

.. _Addressing:

Addressing
==========
* <these are just notes>
* This is about how various kinds of pointers can be made e.g. to a immutable object etc
* And about both internal pointers and the external URLs for :any:`oWeb Browser integration`

.. _Meta Data:

Meta Data
=========
<these are just notes>

.. _Extra Security:

Extra Security
==============
There needs to be a balance between usability and security,
many "secure" services become unusable through too much complexity, latency / bandwidth / CPU.
However an system that reaches that optimal balance may not provide sufficient security for certain actions.
For this reason an extra set of security services will be added that build on other services such as bitcoin or other blockchains.

* Signing via a clock service.
* Bitcoin
* Namecoin or other name spaces


TODO
====
.. todo::

    * Look up protobufs as referenced in IPFS

