const Transportable = require("./Transportable");

// ######### Parallel development to Block.py ########

class Block extends Transportable {
    constructor(hash, data) {
        super(hash, data);
        this.table = 'b';
    }
    size() { console.assert(false, "XXX Undefined function Block.size"); }
    content() {
        console.assert(!this._needsfetch,"Block should be loaded first as content is sync");
        return this._data;
    }

}
exports = module.exports = Block;

