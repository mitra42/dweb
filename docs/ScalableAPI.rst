.. _ScalableAPI:

************
Scalable API
************

The concept of a Scalable API (or UI) is that simple things are easy to do, and ever more complex things are incrementally more complex.

So a higher level API for applications is desirable, which utilizes the lower level layers.

Starting with the simplest level of complexity.

TODO THIS SECTION STILL NEEDS HEADERS


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

======      ======================   =================
Object      URL                      Stored as
======      ======================   =================
Mutable     mb/SHA3256.111222       mb/...
Signed      signed/SHA3256.111222   signed/...
Structured  sb/SHA3256.111222       sb/...

If want to access some part then need to pass further args e.g.

sb/SHA3256.111222/html  to get the html version

