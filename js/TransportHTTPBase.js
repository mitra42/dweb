const Transport = require('./Transport.js');
const request = require('request');
const isNode=new Function("try {return this===global;}catch(e){return false;}");
const myrequest = request.defaults({pool: {maxSockets: 2}, forever: true});
//const myrequest = request.defaults({forever: true});

class TransportHTTPBase extends Transport {
    constructor(ipandport, verbose, options) {
        super(verbose, options);
        this.ipandport = ipandport;
        this.baseurl = "http://" + ipandport[0] + ":" + ipandport[1] + "/";
    }
    async_load(command, hash, verbose, success, error) { console.trace(); console.assert(false, "OBSOLETE"); //TODO-IPFS obsolete with p_*
        // Locate and return a block, based on its multihash
        // Call chain for list is mb.load > CL.fetchlist > THttp.rawlist > Thttp.load > CL|MB.fetchlist.success > callers.succes
        if (verbose) { console.log("TransportHTTP async_load:",command, ":hash=", hash); }
        let url = this.url(command, hash);
        if (verbose) { console.log("TransportHTTP:async_load: url=",url); }
        /*
        $.ajax({
            type: "GET",
            url: url,
            success: function(data) {
                if (verbose) { console.log("TransportHTTP:", command, hash, ": returning data len=", data.length); }
                // Dont appear to need to parse JSON data, its decoded already
                if (success) { success(data); }
            },
            error: function(xhr, status, error) {
                console.log("TransportHTTP:", command, ": error", status, "error=",error);
                alert("TODO Block failure status="+status+" "+command+" error="+error);
                if (error) { error(xhr, status, error);}
            },
        });
        */
        //See: https://github.com/request/request
        myrequest(url, function(errorres, response, data) {
                if (verbose) { console.log("TransportHTTP X:", command, hash, ": returning data len=", data && data.length ); }
            //TODO handle errors
            if (errorres) {
                console.assert(false, "TransportHTTP.async_load:", url, ": error", errorres, "response=", response, "data=", data); // Print the error if one occurred //TODO extract useful data to display
                if (error) error(undefined, undefined, undefined);
            } else {
                if (response["statusCode"] === 200) {
                    if (response["headers"]['content-type'] === "application/json") {
                        data = JSON.parse(data);
                    }
                    if (success) success(data);
                } else {
                    console.log("Error status=",response["statusCode"],response["statusMessage"])
                    if (error) error(undefined, undefined, undefined);
                }
            }

        });

    }
    async_post(command, hash, type, data, verbose, success, error) { console.trace(); console.assert(false, "OBSOLETE"); //TODO-IPFS obsolete with p_*
        // Locate and return a block, based on its multihash
        verbose=true;
        if (verbose) console.log("TransportHTTP post:", command,":hash=", hash);
        let url = this.url(command, hash);
        if (verbose) { console.log("TransportHTTP:post: url=",url); }
        if (verbose) { console.log("TransportHTTP:post: data=",typeof data, data); }
        /*
        $.ajax({
            type: "POST",
            url: url,
            data: { "data": data},
            success: function(msg) {
                if (verbose) { console.log("TransportHTTP:", command, hash, ": returning data len=", msg.length); }
                // Dont appear to need to parse JSON data, its decoded already
                if (success) { success(msg); }
            },
            error: function(xhr, status, error) {
                console.log("TransportHTTP:", command, "error", status, "error=",error, "data=", data);
                alert("TODO post "+command+" failure status="+status+" error="+error);
                if (error) { error(xhr, status, error);}
            },
        });
        */
        //https://github.com/request/request
        //console.log("async_post{"url": url, "headers": {"Content-Type": type}, "body":data}, "bodytype=",typeof data);
        myrequest.post({"url": url, "headers": {"Content-Type": type}, "body":data}, function(errorres, response, respdata) {
            if (verbose) { console.log("TransportHTTP post:", command, hash, ": returning data len=", respdata && respdata.length ); }
            //TODO handle errors
            if (errorres) {
                console.assert(false, "TransportHTTP async_post FAIL:", url, "data:",data, "error:", errorres, "response:", response, "respdata:", respdata); // Print the error if one occurred //TODO extract useful data to display
                if (error) error(undefined, undefined, undefined);
            } else {
                if (response["headers"]['content-type'] === "application/json") {
                    respdata = JSON.parse(respdata);
                }
                if (success) success(respdata);
            }

        });
    }
    info() { console.assert(false, "XXX Undefined function Transport.info"); }

    url(command, hash) {
        let url = this.baseurl + command;
        if (hash) {
            url += "/" + hash;
        }
        return url;
    }

}
exports = module.exports = TransportHTTPBase;