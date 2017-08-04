const CryptoLib = require("./CryptoLib");

/* This is extracted to TransportAPI.txt
 * Transports should create a subclass e.g. TransportXyz extends Transport and implement each of the functions below
 * Note this spec may evolve over time,
 * In general, for efficiency, functions should accept either String or Buffer, and return whatever they use internally without converting.
 * The verbose parameter is always a boolean that can be used to generate debugging lines on the console.
 * hashes can be the internal format of the underlying transport BUT must be identifyable e.g. /ipfs/12345abc or BLAKE2:12345abc
 * ideally we can move to a common URL-like format as the space evolves
 * TODO: notify spec (for items added to the list after p_rawlist) needs turning into promise or event
 * TODO: stream spec (for larger items returned as they are retrieved as a stream)  - see https://nodejs.org/api/http.html for example
 */


class Transport {
    constructor(verbose, options) {}    // Doesnt do anything, its all done by SuperClasses

    p_setup(transportoptions, verbose, options) {
        /*
        Setup the resource and open any P2P connections etc required to be done just once.
        In almost all cases this will call the constructor of the subclass
        Should return a new Promise that resolves to a instance of the subclass

        :param obj transportoptions: Data structure required by underlying transport layer (format determined by that layer)
        :param boolean verbose: True for debugging output
        :param options: Data structure stored on the .options field of the instance returned.
        :resolve Transport: Instance of subclass of Transport
         */
        console.assert(false, "Intentionally undefined function Transport.p_setup should have been subclassed");
    }
    link(data) {
        /*
         Return an identifier for the data without storing

         :param string|Buffer data   arbitrary data
         :return string              valid id to retrieve data via p_rawfetch
         */
        console.assert(false, "Intentionally undefined function Transport.link should have been subclassed");
    }
    dumps(obj) {
        /*
         Encode an obj into a JSON string - this is in Transport as some systems have a canonical form of JSON they prefer to store
         */
        return JSON.stringify(obj);
    }
    loads(str) {
        /*
         Inverse of dumps - so if string encoded in transport specific way, should undo that.
         */
       return JSON.parse(str);
    };

    p_rawstore(data, verbose) {
        /*
        Store a blob of data onto the decentralised transport.
        Returns a promise that resolves to the hash of the data, but also see xxx

        :param string|Buffer data: Data to store - no assumptions made to size or content
        :param boolean verbose: True for debugging output
        :resolve string: hash of data stored
         */
        console.assert(false, "Intentionally undefined function Transport.p_rawstore should have been subclassed");
    }
    p_store() { console.assert(false, "Undefined function Transport.p_store - may define higher level semantics here (see Python)"); }
    //noinspection JSUnusedLocalSymbols

    p_rawfetch(hash, verbose) {
        /*
        Fetch some bytes based on a hash, no assumption is made about the data in terms of size or structure.
        Where required by the underlying transport it should retrieve a number if its "blocks" and concatenate them.
        Returns a new Promise that resolves currently to a string.
        There may also be need for a streaming version of this call, at this point undefined.

        :param string hash: Hash of object being retrieved
        :param boolean verbose: True for debugging output
        :resolve string: Return the object being fetched, (note currently returned as a string, may refactor to return Buffer)
         */
        console.assert(false, "Intentionally undefined  function Transport.p_rawfetch should have been subclassed");
    }
    p_fetch() { console.assert(false, "Intentionally Undefined function Transport.p_fetch - may define higher level semantics here (see Python)"); }
    p_rawadd(hash, date, signature, signedby, verbose) {
        /*
        Store a new list item, it should be stored so that it can be retrieved either by "signedby" (using p_rawlist) or
        by "hash" (with p_rawreverse). The underlying transport does not need to guarrantee the signature,
        an invalid item on a list should be rejected on higher layers.

        :param string hash: String identifying an object being added to the list.
        :param string date: Date (as returned by new Data.now() )
        :param string signature: Signature of hash+date
        :param string signedby: hash of the public key used for the signature.
        :param boolean verbose: True for debugging output
        :resolve undefined:
         */
        console.assert(false, "XXX Undefined function Transport.p_rawadd");
    }
    p_rawlist(hash, verbose) {
        /*
        Fetch all the objects in a list, these are identified by the hash of the public key used for signing.
        (Note this is the 'signedby' parameter of the p_rawadd call, not the 'hash' parameter
        Returns a promise that resolves to the list.
        Each item of the list is a dict: {"hash": hash, "date": date, "signature": signature, "signedby": signedby}
        List items may have other data (e.g. reference ids of underlying transport)

        :param string hash: String with the hash that identifies the list.
        :param boolean verbose: True for debugging output
        :resolve array: An array of objects as stored on the list.
         */
        console.assert(false, "XXX Undefined function Transport.p_rawlist");
    }
    p_list() { console.assert(false, "XXX Undefined function Transport.p_list"); }
    //noinspection JSUnusedGlobalSymbols
    p_rawreverse(hash, verbose) {
        /*
        Similar to p_rawlist, but return the list item of all the places where the object hash has been listed.
        The hash here corresponds to the "hash" parameter of p_rawadd
        Returns a promise that resolves to the list.

        :param string hash: String with the hash that identifies the object put on a list.
        :param boolean verbose: True for debugging output
        :resolve array: An array of objects as stored on the list.
         */
        console.assert(false, "XXX Undefined function Transport.p_rawreverse");
    }
    p_add(hash, date, signature, signedby, obj, verbose) {
        if (obj && !hash) hash = obj._hash;
        console.assert(signedby && signature && hash, "p_add: Meaningless request");
        return this.p_rawadd(hash, date, signature, signedby, verbose);
    }

    static _add_value(hash, date, signature, signedby, verbose) {
        let store = {"hash": hash, "date": date, "signature": signature, "signedby": signedby};
        return Dweb.transport.dumps(store);
    }
}
exports = module.exports = Transport;