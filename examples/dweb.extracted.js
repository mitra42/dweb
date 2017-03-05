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

// ====== End of Classes ==============