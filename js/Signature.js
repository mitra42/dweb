const SmartDict = require("./SmartDict");
const Dweb = require("./Dweb");

// ######### Parallel development to SignedBlock.py which also has SignedBlocks and Signatures classes ########

class Signature extends SmartDict {
    constructor(hash, dic, verbose) {
        super(hash, dic, verbose);
        //console.log("Signature created",this.hash);
        //TODO turn s.date into java date
        //if isinstance(s.date, basestring):
        //    s.date = dateutil.parser.parse(s.date)
        this.table = "sig";
    }
    //TODO need to be able to verify signatures
    static sign(commonlist, hash, verbose) {
        /*
        :param hash: of item being signed
         */
        let date = new Date(Date.now());  //TODO-DATE //TODO-ASYNC
        let signature = Dweb.CryptoLib.signature(commonlist.keypair, date, hash);
        if (!commonlist._publichash) commonlist.p_store(verbose); // Sets _publichash sync, while storing async
        console.assert(commonlist._publichash, "Signature.sign should be a publichash by here");
        return new Signature(null, {"date": date, "signature": signature, "signedby": commonlist._publichash})
    }

    verify() { console.assert(false, "XXX Undefined function Signature.verify"); }
    /* Also undefined from Signatures class in Python
        Should be defined on CommonList
        earliest(), fetch(hash), blocks(), latest()
     */

    static filterduplicates(arr) {
        let res = {};
        // Remove duplicate signatures
        return arr.filter((x) => (!res[x.hash] && (res[x.hash] = true)))
    }


}
exports = module.exports = Signature;
