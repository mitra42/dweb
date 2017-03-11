:: _Javascript:

==================
Javascript Library
==================

A Javscript library, dweb.js is provided to allow browsers to access the Dweb functionality at the Object level.

Note that browsers can more simply access Dweb resources via URLs.

.. js:function:: dwebfile(table, hash, path, options)

    :param string table:    The table the hash is stored in
    :param string hash:     The hash of the file being retrieved
    :param string path:     A "/" delimited path below the hash e.g. foo/bar
    :param object options:  Dictionary of options to be passed with the data to storeto
    :throws ??:    Probably throws an error if the fetch fails, needs testing

Retrieve the content of an object - typically for display.
It will attempt to do the right thing to make it easy to write lightweight code.
This is asynchronous and should return immediately.

.. js:function:: dwebupdate(table, hash, type, data, options)

    :param string table:    The table the hash is stored in
    :param string hash:     The hash of the file being retrieved
    :param string path:     A "/" delimited path below the hash e.g. foo/bar
    :param bytes data:      Data to be stored in the hash table.
    :param object options:  Dictionary of options to be passed with the URL returned to storeto
    :throws ??:    Probably throws an error if the fetch fails, needs testing

Update the data at a hash in a table. The lower level functions return a URL which is stored via the "options".
This is asynchronous and should return immediately.

.. js:function:: dweblist(div, hash)

    :param div: the id of a UL or OL that can have LI elements addded to hold each element of the list at hash

dweblist reads a list and updates a UL or OL, the signature of this function will probably change to use options, and add table, path etc.

.. js:function:: storeto(data, options)

    :param bytes data:  Data to be stored
    :param object options:  Options on where to store the data
    :param string options.dom_id: The id of a object that can have text stored in its .innerHTML
    :param string options.elem: An element that can have its .innerHTML stored to

This is a utility function used by dwebfile etc to control where to store any results.

