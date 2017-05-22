const Dweb = require('./Dweb.js');
const StructuredBlock = require('./StructuredBlock.js');

const mbhash = "BLAKE2.dfMoOqTdXvqKhoZo7HPvD5raBXfgH7chXsN2PElizs8=";  // Hash reported out at tinymce.html
const mb2hash = "BLAKE2.nBWNoMyOJdhm-wrx0URYo7Utw3jG8J3boEBUcXvATVU="; // Hash reported for docs/_build/html
const sbhash="BLAKE2.spTuo7yuSJEQyYy3rUFV2G0SCDxhkZEHhQQttozxWtQ="; // This is teh hash field from any line of list/..mbhash..

function previouslyworking() {        // This was previously working in examples
    let verbose=false;
    console.log("StructuredBlock=======");
    let sb = new StructuredBlock(sbhash);
    sb.async_load(true,
        function(msg) { sb.async_path(["langs","readme.md"], verbose,  [ "async_elem", "myList.0", verbose, null, null ], null); },
        null);
    /*
    console.log("MutableBlock=======");
    <!-- also works with /file/mb/.....=/langs/readme.md -->
    let mb = new MutableBlock(mbhash, null, false, null, false, null, null, null, verbose, null);
    mb.async_loadandfetchlist(verbose,
        function(msg) { mb.async_path(["langs","readme.md"], verbose, ["async_elem", "myList.1", verbose, null, null], null); },
        null);
    <!-- Now test path using dwebfile -->
    Dweb.async_dwebfile("sb", sbhash, "langs/readme.md", ["async_elem", "myList.2", verbose, null, null], null);
    <!-- Now test path using dwebfile -->
    Dweb.async_dwebfile("mb", mbhash, "langs/readme.md", ["async_elem", "myList.3", verbose, null, null], null);
    console.log("XXX@31 end testing");
    */
}

previouslyworking();
