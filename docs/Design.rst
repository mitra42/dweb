***************
Design Thinking
***************

#TODO-REFACTOR need to scan and update this file

This page is intended to summarise key design thinkng so that if something is going to be changed the reasoniong behind
the choices made is more apparant than it might be from just reading the spec.

.. _design_url:

URL Design
----------
What should a URL look like for this.

Logic goes ...

* Browser needs to be able to distinguish between requesting JSON or requesting content.
* Need the library and/or gateway and/or server to know what the hash is, if its going to know whether it already is content,
  or its JSON from which can pull content, or its a MutableBlock.
* For URLs there may be no library, so the gateway has to know, and it may be accessing blocks via a decentralized transport.
