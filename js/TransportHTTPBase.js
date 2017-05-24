const Transport = require('./Transport.js');

var request = require('request');

var isNode=new Function("try {return this===global;}catch(e){return false;}");

class TransportHTTPBase extends Transport {
    constructor(ipandport, verbose, options) {
        super(verbose, options);
        this.ipandport = ipandport;
        this.baseurl = "http://" + ipandport[0] + ":" + ipandport[1] + "/";
    }
    async_load(command, hash, verbose, success, error) {
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
        request(url, function(errorres, response, data) {
            if (verbose) { console.log("TransportHTTP X:", command, hash, ": returning data len=", data && data.length ); }
            //TODO handle errors
            if (errorres) {
                console.log("TransportHTTP:", command, ": error", status, "error=",error);
                console.log('fullerror:', errorres); // Print the error if one occurred //TODO extract useful data to display
                if (error) error(undefined, undefined, undefined);
            } else {
                if (response["headers"]['content-type'] === "text/json") {
                    data = JSON.parse(data);
                }
                if (success) success(data);
            }

        });

    }
    async_post(command, hash, type, data, verbose, success, error) {
        // Locate and return a block, based on its multihash
        if (verbose) { console.log("TransportHTTP post:", command,":hash=", hash); }
        let url = this.url(command, hash);
        if (type) {
            url += "/" + type;
        }
        if (verbose) { console.log("TransportHTTP:post: url=",url); }
        if (verbose) { console.log("TransportHTTP:post: data=",data); }
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
        request.post({"url": url, "headers": {"Content-Type": "application/octet-stream"}, "body":data}, function(errorres, response, data) {
            if (verbose) { console.log("TransportHTTP post:", command, hash, ": returning data len=", data && data.length ); }
            //TODO handle errors
            if (errorres) {
                console.log("TransportHTTP:", command, ": error", errorres, "error=",error);
                console.log('fullerror:', errorres); // Print the error if one occurred //TODO extract useful data to display
                if (error) error(undefined, undefined, undefined);
            } else {
                if (response["headers"]['content-type'] === "text/json") {
                    data = JSON.parse(data);
                }
                if (success) success(data);
            }

        });
    }
    info() { console.log("XXX Undefined function Transport.info"); }

    url(command, hash) {
        let url = this.baseurl + command;
        if (hash) {
            url += "/" + hash;
        }
        return url;
    }

}
exports = module.exports = TransportHTTPBase;