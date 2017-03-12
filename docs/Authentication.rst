.. _Authentication:

==============
Authentication
==============

Authentication is implemented vi Access Control Lists (ACL)

A specific ACL (X) is represented by a Private/Public key paid X' X" and the hash of the Public key X°.
It is represented as a list in the "ach" table under X°.

A viewer of a list (V) also has a public/private key pair and hash of public key. V', V" V°.

Permission for viewer V to access X. Is given by adding (encrypt(X', V"), V°) to X.
To do so requires signing this with X'.

To publish an item:

* create a Structured Block (SB) or Block (B).
* Create a Encrypted-SB (ESB), by encrypting this with X", and adding X°
This ESB can be stored as for any other SB, (or MB?).

For V (in posession of V') to access an item encrypt(SB, X")

* Retrieve the item encrypt(SB, X"), X°
* Retrieve the list X° and look for own item V°
* Obtain encrypt(X',V") and decrypt with V' to get X'
* Take item: encrypt(SB, X") and decrypt with X' to get SB


.. productionlist::
    ACL: ACL_private ACL_public ACL_hash
    Viewer: Viewer_private Viewer_public Viewer_hash
    ACL_list: "acl" ACL_hash [ ACL_item* ]
    ACL_item: encrypt(ACL_private, Viewer_public) Viewer_hash
    EncryptedSB: encrypt(StructuredBlock, ACL_public) ACL_hash