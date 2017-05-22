const SmartDict = require("./SmartDict");
const CryptoLib = require("./CryptoLib");
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
        let date = datetime.now();  //TODO-DATE //TODO-ASYNC
        let signature = CryptoLib.signature(commonlist.keypair, date, hash);
        console.assert(commonlist._publichash, "CL should have been stored before call to Signature.sign"); // If encounter this, make sure caller stores CL first
        //Python does: if (!commonlist._publichash) commonlist.async_store(verbose, null, null)
        // But this would require making this async.
        return new Signature(null, {"date": date, "signature": signature, "signedby": commonlist._publichash})
    }

    verify() { console.log("XXX Undefined function Signature.verify"); }
}
exports = module.exports = Signature;
