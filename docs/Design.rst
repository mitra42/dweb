***************
Design Thinking
***************

This page is intended to summarise key design thinkng so that if something is going to be changed the reasoniong behind
the choices made is more apparant than it might be from just reading the spec.

.. _design_url:

URL Design
----------
What should a URL look like for this.

Logic goes ...

* Browser needs to be able to distinguish between requesting JSON or requesting content.
* Need the library and/or gateway and/or server to know what the data and the hash represent. For example it needs to know whether it already is content,
  or its JSON from which can pull content, or its a MutableBlock.
* For URLs there may be no library, so the gateway has to know, and it may be accessing blocks via a decentralized transport.

For simple functions that are the minimum set of functions a transport layer has to provide I defined a simple format e.g. */rawfetch/hash -> data*
or */rawstore, data -> hash*  allowing for very minimal interfaces with a underlying transport mechanism.

For more complex functions, I defined an extensible format: */command/class/hash/path?arguments* where:
* *hash* defines the data to retrieve
* *class* is a two or three-letter code defining which class to pass the data to, e.g. "sb" for StructuredBlock
* *path* is a path within objects of some class, allowing relative URLs
* *command* is a function that can be applied to the resulting object.

E.g. */file/sb/A1B2C3/foo/index.html*  will: find object A1B2C3;
turn it into a StructuredBlock (which interprets the raw data as a JSON dictionary);
look for the "index.html" link within the "foo" link;
and apply the "file" command to it.

This allows for a more complex set of functions that can be performed on a HTTP gateway,
allowing web pages to embed quite sophisticated URLs as a common core of functions are developed.

