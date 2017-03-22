.. _Authentication:

==============
Authentication
==============

.. note::
The Authentication system is under development, these docs might not match what gets built.
#TODO review this doc after complete implementation of first-pass

See also the diagram "DWeb - Authentication Architecture.isf" (editable in Inspiration, port to PPT welcome)

Authentication is implemented vi Access Control Lists (ACL)

A specific ACL is represented by a Private/Public key pair X' X and the hash of the Public key X°.
It is stored in the DHT as a list under X°.

A viewer of a list (V) also has a Keys: Private V', Public V, and Hash of Public V°

Material is published by Encrypting the content with an Access Key A, and publishing on a list Y.

Permission for viewer V to access X, Is given by adding (encrypt(A, V), V°) to X, which is done by signing with X'

To publish an item:

* create a Structured Block (SB) or Block (B).
* Create a Encrypted-SB (ESB), by encrypting this with X, and adding X°
This ESB can be stored as for any other SB, (or MB?).

For V (in posession of V') to access an item encrypt(SB, X)

* Retrieve the item encrypt(SB, X), X°
* Retrieve the list X° and look for own item V°
* Obtain encrypt(A,V) and decrypt with V' to get A
* Take item: encrypt(SB, A) and decrypt with A to get SB


.. productionlist::
    ACL: ACL_private ACL_public ACL_hash
    Viewer: Viewer_private Viewer_public Viewer_hash
    ACL_list: ACL_hash [ ACL_item* ]
    ACL_item: encrypt(AccessKey, Viewer_public) Viewer_hash
    EncryptedSB: encrypt(StructuredBlock, AccessKey) ACL_hash
    AccessKey: AES or similar symetric key

