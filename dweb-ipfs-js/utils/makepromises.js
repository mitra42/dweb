const promisify = require('promisify-es6');

function makepromises(path, p, pn) {
    if (typeof pn === "string") {
        p[pn] = promisify(path[pn]);
    } else if (pn instanceof Array) {
        for (let i in pn) {
            let n = pn[i]
            makepromises(path, p, n)
        }
    } else { // Dict
        for (let k in pn) {
            if (!p[k]) p[k] = {}
            makepromises(path[k], p[k], pn[k])
        }

    }
}

exports = module.exports = makepromises