const CommonList = require("./CommonList");
// ######### Parallel development to MutableBlock.py ########


class AccessControlList extends CommonList {
    // Obviously ! This class hasnt' been implemented, currently just placeholder for notes etc

    constructor(hash, data, master, keypair, keygen, mnemonic, verbose, options) {
        super(hash, data, master, keypair, keygen, mnemonic, verbose, options);
        this.table = "acl";
    }
    _async_storepublic(verbose, success, error) { // See KeyChain for example
        console.log("XXX Undefined function AccessControlList._async_storepublic");
        //mb = new MutableBlock(keypair=this.keypair, name=this.name)
    }

}
exports = module.exports = AccessControlList;


