.. _Extending

==================
Extending the code
==================

Extending the code, either to improve the dWeb functionality, or to add an application *should* be simple.
This document is intended to help the process.
It is quite likely that the document is out of date compared to the code, or that some of the code has not been brought up
to the structures proposed here.

Corrections and Edits are welcome!

Adding a Block Class
====================

A "Block" Class is something intended to be stored as a object in the CAFS/dWeb/DHT and refered to by its content.

A new class will typically be built on top of `SmartDict`, which itself is a subclass of Transportable.

Adding a Field
--------------
Fields of most types representable in the language used (e.g. Python and Javasctipt) can be added to an object,
and stored in the dWeb objects as JSON.

Choice of names
~~~~~~~~~~~~~~~
Check the list of common field names, if your field has the same meaning as something used elsewhere use the same name,
otherwise try and avoid name clashes.

Fields with names starting with _ are usually unstored, while other fields are usually stored. This behavior can be modified.

The main thing to get right with a new field is storing and retrieving.
Simple fields (strings and numbers) will survive the round-trip through dWeb with the default behavior, as will dict's or arrays.

Using
~~~~~
The field can be used as an attribute e.g. foo.name,
A "getter" can be written if the stored format, and used format is different, e.g. if it is stored as a hash.
Note that a getter is required to define a setter.

Storing
~~~~~~~
Fields are stored via the following chain
* store() writes the object to the dWeb if it has been edited. By default it checks if the hash is set, and only writes if not.
* dirty() flags the object as needing storage - by default by clearing the hash, it can be subclassed to clear other things like signatures.
* _data.getter converts the internal fields into a JSON string for storage
* preflight is called by the default _data.getter and returns a dict suitable for storing
* dumps converts a dictionary for storing

Implementation
* Any fields with names starting with _ are stripped by Transportable.preflight, or deeper in dictionaries or lists are stripped by Transportable.dumps.
* For simple fields, the default should work - json's dumps will catch it.
* For fields that are Transportable (includes CommonList and SmartDict), then Transportable.preflight will store and return the hash instead.
* For date fields (type is datetime) the json_default function will turn into isoformat dates
* For other fields, or objects embedded in arrays or dicts, they will need handling beforehand - the best place is by subclassing preflight

Fetching
~~~~~~~~
Fields are fetched via ...
* fetch() - gets the block from the dweb
* __init__(data=json-string) is called to create the new object
* _data.setter is called to convert the json string to fields, the default SmartDict._data sets fields in the __dict__
* foo.setter is called to set that field.

Implementation
* For simple fields, the path above should just work.
* If the field name includes "date" then it will be assumed the json string is an isoformated date which SmartDict.__setattr__ be parsed into a datetime.
* Objects need to be handled by writing a setter (and its partner getter), the default just stores the hash.

Adding a List Class
===================
*TODO* complete this, its just notes
A new class will typically be built on top of `CommonList`, which itself is a subclass of SmartDict which is a subclass of Transportable.


To Be Documented
================

* Add a List class
* Add a Transport layer
* Add a function across classes
* Each of the above in Javascript

Snippets to include or delete
=============================

Adding a new Object
-------------------
On top of Structured Block, Smart Dict, Transportable
Adding a new List
-----------------
On top of MB, CommonList

Adding functionality on a list - e.g. Search or Earliest
Adding functionality on a objects e.g. searchable
