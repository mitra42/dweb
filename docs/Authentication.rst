.. _Authentication:

==============
Authentication
==============

.. note::

See also the diagram "DWeb - Authentication Architecture.isf" (editable in Inspiration, port to PPT welcome)


Authentication Concepts
=======================
There are a number of key concepts in the Authentication layer that build on each other.

Encrypted Objects
-----------------
(Almost) any object can be encrypted. The object will be stored as a pair { acl, encrypted }.
ACL is the hash of a Access Control List or the Key Chain.
Encrypted holds the original json data encrypted with the key from the ACL.

Python Implementation
~~~~~~~~~~~~~~~~~~~~~
In Python this is done by adding an _acl field to it, if this field is set, the store function encrypts automatically using the key of the ACL.
On Python decryption is also automatic, if a block is retrieved containing the field "encrypted".
It will attempt to decrypt by comparing keys in KeyChain.mykeychains against the ACL.

KeyPair
-------
The KeyPair object encapsulates a public/private key pair to allow common methods across different keys.
It currently it supports RSA, and WordHash keys but any other public/private key should be implementable.
There is a concept used of "master" which means that a viewer has the applicable private key that allows it to add things
to a list, e.g. to publish or add viewers to an ACL.

ViewerKey (VK)
--------------
A ViewerKey is a KeyPair that represents a person/entity that can be given permissions.
The public key is used for adding someone to an ACL, and control of the private key is needed for access.

Access Control List (ACL)
-------------------------
To manage who can access an object, an ACL is used.
The ACL contains a KeyPair (private/public keys), an encryption (AES) key, and a list of who can access it.
Each item on the List is the AES key encrypted with the public key of the viewer; and the hash of the viewer's public key.
To find a key, the viewer can look on the list for items with the hash of its public key, and then decrypt with its private key.

Revoking Access
~~~~~~~~~~~~~~~
Because we have to assume that things are cached there is no way to be sure that enough info has not been cached to enable viewing.
To minimize the chance of this, to revoke access requires changing the AES key and updating list items to use that key.

Key Chain (KC)
--------------
Key Chain's represent things you own.
A Key Chain is a list of "master" items.
These items are typically MutableBlock Masters, or ViewerKeys.
These items are enrypted with KeyChains key before adding to the list.
The old way of implementing this was the the KeyChain used a "WordHashKey" from which a symetric key was derived.
New way of implementing this will be (or is already) that object is encrypted with public key of KeyChain.

WordHash Keys
~~~~~~~~~~~~~
The Key Chain uses a WordHash key, it's private key is built from a list of Mnemonic Words (using BIP39 standard from BitCoin).
Its public key is just a hash of the encrypted KeyPair object.

There may be a better key to use based on a public/private key system with shorter keys so that (unlike RSA) they can reasonably
be rebuilt with mnemonic words.

Initialization of KeyChain
~~~~~~~~~~~~~~~~~~~~~~~~~~
At initialization a user would be asked for their Mnemonic words.
These words are used to generate a WordHash key and then searching for the list of items on that WordHash pulls back the
items stored on the KeyChain (MB's and KP's mostly)
Those items are encrypted with the private key from the WordHash so can be safely stored on the dWeb.
Once initialized, any object the user has access to (via an ACL) should be successfully decrypted.

Python implementation
~~~~~~~~~~~~~~~~~~~~~
The Python implementation depends on a class field KeyChain.mykeychains which has one or more KeyChains stored in it.

AutoProtection (Python only)
----------------------------
There is a test which SHOULD protect against inadvertantly storing unencrypted private keys.
This test currently is implemented on MB's and KP's.
It can be overridden by setting the _allowunsafestore=True on the object.

How to Use
==========
To setup
--------
* Create an ACL with a new key.
* Add the ACL to your KeyChain (so you can keep control of it), and set its _acl field to the KC
* If using an MB for publishing, store the ACL in its contenthash field.
* Add the MB to your KeyChain (so you can keep control of it), and set its _acl field to the KC

To publish enrypted
-------------------
Create an item as usual, then set its _acl field to the ACL, (note this will be done automatically if using the MB)

To give someone access
----------------------

* Ask them for the public key of one of their ViewerKeys.
* Add this public key to the ACL. Will add { encrypt(ACL.symkey, VK-public), VK-public-hash)} to the list.

To view an item
---------------

* Retrieve the encrypted item { acl, encrypted }
* Retrieve the list of items on the acl.
* Look for any of your ViewerKeys's hash on the ACL,
* Decrypt what is found with the VK's private key to get symetric keys.
* Try the symetric keys to decrypt the encrypted data. If it works then you have the data.


.. productionlist::
    ACL: ACL_private ACL_public ACL_accesskey ACL_hash [ ACL_item* ]
    ViewerKey: Viewer_private Viewer_public Viewer_hash
    ACL_item: encrypt(ACL_accesskey, Viewer_public) Viewer_hash
    EncryptedSB: encrypt(StructuredBlock, ACL_accesskey) ACL_hash
    ACL_AccessKey: AES or similar symetric key
    KeyChain: KC_keypair [ KC_item* ]
    KC_item: encrypr(ViewerKey | MBM, KC_keypair)

Notes from Javascropt implementation
------------------------------------
https://download.libsodium.org/doc/public-key_cryptography/authenticated_encryption.html

