From TransportHTTP
    static list(table, hash, verbose) {    // python version can also take key as variable
                // Adapted from python TransportHttp.list
                //param table: Table to look for key in
                //param key: Key to be retrieved (embedded in options for easier pass through)
                //return: list of dictionaries for each item retrieved
                if (verbose) { console.log("list",table, hash); }
                //hash = hash or CryptoLib.urlhash(options["key"], verbose=verbose, **options)
                //del(options["key"])
                res = TransportHttp._sendGetPost(False, "list", table, hash );   // Maybe stuff in options
                return JSON.parse(res);
            }

// ====== Signature, based on SignedBlock.py ==============
class Signature {
    constructor(dic) {
        this.date = dic["date"];
        this.hash = dic["hash"];
        this.publickey = dic["publickey"];
        this.signature = dic["signature"]
        console.log("Signature created",this.hash);
    }
    //TODO need to verify signatures
}


// ====== Signed Block, based on SignedBlock.py ==============
class SignedBlock {
   constructor(hash) { // Python also handles, structuredblock=None, signatures=None, verbose=False, **options):
        // Adapted from Python SignedBlock
        // if structuredblock and not isinstance(structuredblock, StructuredBlock):
        //     structuredblock = StructuredBlock(structuredblock) # Handles dict or json of dict
        self._structuredblock = null; // WOuld be from structuredblock if passed
        self._hash = hash;
        //self._signatures = Signatures(signatures or [])
    }
}

// ====== Signed Blocks, based on SignedBlock.py ==============
class SignedBlocks extends Array {


    //    static fetch_publickey(publickey, verbose) - not used yet
    static fetch_hash(hash, verbose) {
        //Find all the related Signatures.
        lines = transportcls.list("signedby", hash, verbose);
        if (verbose) { console.log("SignedBlock.fetch found ", lines.length); }
        results = {};
        for (let i = 0; i < lines.length; i++) {
            let block = lines[i];
            s = new Signature(block);
            if (! results[s.hash]) {
                results[s.hash] = new SignedBlock(s.hash);
            }
            //TODO turn s.date into java date
            //if isinstance(s.date, basestring):
            //    s.date = dateutil.parser.parse(s.date)
            //TODO verify signature
            //if CryptoLib.verify(s):
                results[key]._signatures += s;
        }
        //Turn it into a list of SignedBlock - stores the hashes but doesnt fetch the data
        sbs = new SignedBlocks();
        for (var k in results) {
            sbs += results[k];
        }
        return sbs;
    }
}

// ====== Mutable Block, based on MutableBlock.py ==============
class MutableBlock {
    constructor(hash) {
        // Note python __init__ also allows constructing with key, or with neither key nor hash
        // see commented out code
        this._hash = hash;       // Could be None
        //if key:
        //    if isinstance(key, basestring):
        //    # Its an exported key string, import it (note could be public or private)
        //        key = CryptoLib.importpublic(key)  # Works on public or private
        //       self._key = key
        //else: // key not defined
        this._key = null;
        //   if not hash:    # Dont generate key if have a hash
        //       self._key = CryptoLib.keygen()
        this._current = None
        this._prev = new Array()
    }

    fetch() {
        var signedblocks;
        //if this._key:
        //    signedblocks = SignedBlocks.fetch_publickey(this._key.publickey(), verbose);    // Not passed options
        //else:
            signedblocks = SignedBlocks.fetch_hash(this.hash, verbose);    // Not passed options
        this.curr = signedblocks.latest();
        this.prev = signedblocks.sorteddeduplicatedrest();
    }
}
// ====== End of Classes ==============