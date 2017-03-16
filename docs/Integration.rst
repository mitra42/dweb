.. _Integration:

Integration
===========

#TODO-REFACTOR need to scan and update this file

This section describes how the Decentralized Web (:any:`dWeb`) interacts with the Old Web (:any:`oWeb`).
It can be expanded to describe modules required and their API's for interacting with various :any:`oWeb` services.

.. _oWeb Browser integration:

oWeb Browser integration
------------------------
* The core issue is to allow material to be published on the dWeb confident that any oWeb user can access it.
* This does not mean that all the dWeb advantages have to be accessible to unmodified browsers, but all content should be.
* The conclusion is that there need to be dWeb URLs understandable by an unmodified browser, but that can be recognized by a dWeb browser and diverted.

So for example ``https://dweb.net/block/12345678`` could be a syntax for retrieving block 12345678.

* See :any:`Addressing` for definition of these URLs
* Completely unmodified browsers access that URL, which could be any of a number of gateways that can retrieve and return the block.
  This might involve redirections.
* Modified browsers recognize the URL and use their own dWeb clients to retrieve it.
* Any dweb URL should work at any server so ``https://dweb.archive.org/block/12345678`` would provide exactly the same contents as above.
* A gateway needs to be built that can server these URLs.  *<DEV>*

.. _Web page, Javascript integration:

Web page, Javascript integration
--------------------------------
* A web page could be defined so that the first page was supplied via the oWeb, but deeper content supplied via dWeb.
* This would involve having a Javascript library imported and working on the page
* That Javascript ideally should intercept attempts to load content *<DEV>*
* The Javascript should be callable from within the code to explicitly load dWeb content
* The Javascript should have an API that other Javascript can access to retrieve content. *<*<DEFINE>*>*
* e.g. "onclick=dweb_load(block/12345678,target)"

.. _Browser plugin:

Browser plugin
--------------
* A browser plugin would allow a browser to participate in the dWeb directly, i.e. without Javascript on a page.
* It would intercept dweb format URLs and handle directly. *<DEV>*
* It would contain ability to serve as a dWeb peer.
* It could intercept HTTP headers indicating the content can be found on the dWeb.
* For browsers such as Chrome it should provide the library to apps running as Chrome extensions.

.. _Internet Archive integration:

Internet Archive integration
----------------------------
The Internet Archive is a major supporter of this initiative. Their service should be integrated in the following way:

* By addition of a HTTP header *<DEFINE>* to each object sent by the Archive (URI might work best since already defined)
* By providing a dWeb peer, that is always attached, and can serve any of the Archive's content.
* By adding the Javascript code to their main entry pages.

.. _App platform:

App platform
------------
It should be possible to build apps in the dWeb for common platforms, iOS, Android, HTML5, Chrome (anything missed?):

* This would probably require a library for each of these platforms that could be incorporated by app developers,
* library could take different scales, from just a client, to a peer.
* This section needs someone with more experience of developing apps to make suggestions.

.. _IoT - Internet of things:

IoT - Internet of things
------------------------

As small, internet connected devices proliferate, we should consider how to incorporate devices with a wide range of available memory and processing capability.
Those devices should for example should be able to fully participate without HTTPS or other encryption.

* Requires a small C++ library, that can be scalably incorporated depending on device capabilities.
* Probably requires the HTTP interface to work fully without WebRTC or similar.
* Should allow IoT devices to retrieve mutable or immutable data
* Should allow pushing of data to the web (imagine sensor data, or camera data).
* Should allow, but not require acting as a peer (depending on memory/storage/CPU constraints)
* Should offer encryption but not require it to be compiled in.
* Needs a simple API for easy incorporation into apps. *<DEFINE>*