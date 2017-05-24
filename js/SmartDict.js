const Transportable = require("./Transportable");
const CryptoLib = require("./CryptoLib");


// See CommonBlock.py for Python version

class SmartDict extends Transportable {
    constructor(hash, data, verbose, options) {
        // data = json string or dict
        super(hash, data); // _hash is _hash of SB, not of data - will call _setdata (which usually set fields), -note does not fetch the has, but sets _needsfetch
        this._setproperties(options);   // Note this will override any properties set with data
    }
    __setattr__(name, value) { // Call chain is ... success or constructor > _setdata > _setproperties > __setattr__
        // Subclass this to catch any field (other than _data) which has its own setter
        //TODO Need a javascript equivalent way of transforming date
        // if (name[0] != "_") {
        //    if "date" in name and isinstance(value,basestring):
        //        value = dateutil.parser.parse(value)
        //}
        //TODO - instead of calling "setter" automatically, assuming that __setattr__ in each class does so.
        this[name] = value; //TODO: Python-Javascript: In Python can assume will get methods of property e.g. _data, in javascript need to be explicit here, or in caller.
    }
    _setproperties(dict) { // Call chain is ... onloaded or constructor > _setdata > _setproperties > __setattr__
        if (dict) { // Ignore dict if null
            for (let prop in dict) {
                //noinspection JSUnfilteredForInLoop
                this.__setattr__(prop, dict[prop]);
            }
        }
    }
    preflight(dd) { // Called on outgoing dictionary of outgoing data prior to sending - note order of subclassing can be significant
        let res = {};
        for (let i in dd) {
            if (i.indexOf('_') !== 0) { // Ignore any attributes starting _
                if (dd[i] instanceof Transportable) {
                    res[i] = dd[i].async_store(false, null, null)._hash  // store(verbose, success, error) - will set hash, then store obj in background
                } else {
                    res[i] = dd[i];
                }
            }
        }
        // Note table is a object attribute in JS, so copied above (in Python its a class attribute that needs copying
        return res
    }

    _getdata() {
        let dd = {};
        for (let i in this) {
            //noinspection JSUnfilteredForInLoop
            dd[i] = this[i];    // This just copies the attributes not functions
        }
        let res = CryptoLib.dumps(this.preflight(dd));
        if (this._acl) { //Need to encrypt
            let encdata = this._acl.encrypt(res, true);  // data, b64
            let dic = { "encrypted": encdata, "acl": this._acl._publichash, "table": this.table};
            res = CryptoLib.dumps(dic);
        }
        return res
    }    // Should be being called on outgoing _data includes dumps and encoding etc

    _setdata(value) {
        // Note SmartDict expects value to be a dictionary, which should be the case since the HTTP requester interprets as JSON
        // Call chain is ...  or constructor > _setdata > _setproperties > __setattr__
        if (value) {    // Skip if no data
            if (typeof value === 'string') {    // Assume it must be JSON
                value = JSON.parse(value);
            }
            // value should be a dict by now, not still json as it is in Python
            //TODO-AUTHENTICTION - decrypt here
            this._setproperties(value); // Note value should not contain a "_data" field, so wont recurse even if catch "_data" at __setattr__()
        }
    }

    objbrowser(hash, path, ul, verbose) {
        let hashpath = path ? [hash, path].join("/") : hash;
        //OBSdwebobj(ul, hashpath) {    //TODO - note this is under dev works on SB and MB, needs to work on KeyChain, AccessControlList etc
        // ul is either the id of the element, or the element itself.
        //TODO-follow link arrow
        //console.log("dwebobj",ul)
        if (typeof ul === 'string') {
            ul = document.getElementById(ul);
        }
        let li = document.createElement("li");
        li.source = this;
        li.className = "propobj";
        ul.appendChild(li);
        //li.innerHTML = "<B>StructuredBlock:</B>" + hashpath;
        let t1 = document.createTextNode(this.constructor.name+": "+hashpath);
        let sp1 = document.createElement('span');
        sp1.className = "classname"; // Confusing!, sets the className of the span to "classname" as it holds a className
        sp1.appendChild(t1);
        li.appendChild(sp1);

        //Loop over dict fields
        let ul2 = document.createElement("ul");
        ul2.className="props";
        li.appendChild(ul2);
        //noinspection JSUnfilteredForInLoop
        for (let prop in this) {
            //noinspection JSUnfilteredForInLoop
            if (this[prop]) {
                //noinspection JSUnfilteredForInLoop
                let text = this[prop].toString();
                if (text !== "" && prop !== "_hash") {    // Skip empty values; _hash (as shown above);
                    let li2 = document.createElement("li");
                    li2.className='prop';
                    ul2.appendChild(li2);
                    //li2.innerHTML = "Field1"+prop;
                    //noinspection JSUnfilteredForInLoop
                    let fieldname = document.createTextNode(prop);
                    let spanname = document.createElement('span');
                    spanname.appendChild(fieldname);
                    spanname.className='propname';
                    //TODO - handle Links by nested list
                    li2.appendChild(spanname);
                    //if ((prop == "links") || (prop == "_list")) {  //StructuredBlock
                    //noinspection JSUnfilteredForInLoop
                    if ( ["links", "_list", "_signatures", "_current"].includes(prop) ) { //<span>...</span><ul proplinks>**</ul>
                        let spanval;
                        spanval = document.createElement('span');
                        spanval.appendChild(document.createTextNode("..."));
                        li2.appendChild(spanval);
                        let ul3 = document.createElement("ul");
                        ul3.className = "proplinks";
                        ul3.style.display = 'none';
                        spanname.setAttribute('onclick',"Dweb.utils.togglevisnext(this);");
                        //spanname.setAttribute('onclick',"console.log(this.nextSibling)");

                        li2.appendChild(ul3);
                        //TODO make this a loop
                        //noinspection JSUnfilteredForInLoop
                        if (Array.isArray(this[prop])) {
                            //noinspection JSUnfilteredForInLoop
                            for (let l1 in this[prop]) {
                                //noinspection JSUnfilteredForInLoop,JSUnfilteredForInLoop,JSUnfilteredForInLoop,JSUnfilteredForInLoop
                                this[prop][l1].objbrowser(hash, (path ? path + "/":"")+this[prop][l1].name, ul3, verbose);
                            }
                        } else {
                            //noinspection JSUnfilteredForInLoop
                            if (this[prop]._hash) {
                                //noinspection JSUnfilteredForInLoop,JSUnfilteredForInLoop
                                this[prop].objbrowser(this[prop]._hash, null, ul3, verbose)
                            } else {
                                //noinspection JSUnfilteredForInLoop
                                this[prop].objbrowser(hash, path, ul3, verbose);
                            }
                        }
                    } else {    // Any other field
                        let spanval;
                        if (prop === "hash") {
                            //noinspection ES6ConvertVarToLetConst
                            spanval = document.createElement('a');
                            //noinspection JSUnfilteredForInLoop
                            spanval.setAttribute('href','/file/b/'+this[prop]+"?contenttype="+this["Content-type"]);
                        } else {
                            // Group of fields where display then add behavior or something
                            //noinspection ES6ConvertVarToLetConst
                            spanval = document.createElement('span');
                            if (prop === "_needsfetch") {
                                li2.setAttribute('onclick','Dweb.utils.async_objbrowserfetch(this.parentNode.parentNode);');
                            }
                        }
                        //noinspection JSUnfilteredForInLoop
                        spanval.appendChild(document.createTextNode(this[prop]));
                        spanval.className='propval';
                        li2.appendChild(spanval);
                    }
                    //this.__setattr__(prop, dict[prop]);
                }
            }
        }

    }
}
exports = module.exports = SmartDict;
