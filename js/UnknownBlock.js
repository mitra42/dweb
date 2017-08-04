const SmartDict = require("./SmartDict");
const StructuredBlock = require("./StructuredBlock");
const MutableBlock = require("./MutableBlock");
const KeyChain = require("./KeyChain");
const KeyPair = require("./KeyPair");
const AccessControlList = require("./AccessControlList");
const Dweb = require("./Dweb");

//TODO-SEPERATE - move these to Dweb
const LetterToClass = { // Each of these needs a constructor that takes hash, data and is ok with no other parameters, (otherwise define a set of these methods as factories)
    "sb": StructuredBlock,
    "kc": KeyChain,
    "kp": KeyPair,
    "mb": MutableBlock,
    "acl": AccessControlList,
    //"accesscontrollistentry", AccessControlListEntry - not listed as AccessControlListEntry is not exposed
};

class UnknownBlock extends SmartDict {
    /*
     A class for when we don't know if its a StructuredBlock, or MutableBlock or something else

     You could use this by: (OBSOLETED) foo = new UnknownBlock(hash, verbose); foo.p_load(verbose, ["addtoparent",parent])
     */

    constructor(hash, verbose) {
        // Note Python has options field that overrides data but triggers error as unimplemented as of 2017-05-27
        super(hash, null, verbose, null);
    }
    p_fetch(verbose, successmethod) {
        /*
            Fetch a block which initially we don't know which type
            :return: New object - e.g. StructuredBlock or MutableBlock
         */
        if (verbose) console.log("Unknownblock loading", this._hash);
        let self = this;
        let cls;
        return Dweb.transport.p_rawfetch(this._hash, verbose)
            .then((data) => {
                data = Dweb.transport.loads(data);    // Parse JSON
                let table = data["table"];
                cls = LetterToClass[table];
                console.assert(cls, "UnknownBlock.p_fetch:",table,"isnt implemented in LetterToClass");
                return data;
            })
            .then((data) => Dweb.CryptoLib.p_decryptdata(data, verbose))    // decrypt - may return string or obj
            .then((data) => {
                let newobj = new cls(self._hash, data);
                if (successmethod) {
                    let methodname = successmethod.shift();
                    //if (verbose) console.log("p_elem",methodname, successmethod);
                    newobj[methodname](...successmethod); // Spreads successmethod into args, like *args in python
                }
                return newobj;    // For chaining
            })
            .catch((err) => {console.log("cant fetch and decrypt",this); throw(err)});
    }
}


exports = module.exports = UnknownBlock;
