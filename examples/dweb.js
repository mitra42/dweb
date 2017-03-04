// Javascript library for dweb

var dwebserver = '192.168.1.156'
var dwebport = '4243'

// ==== ALL THIS OBJECT ORIENTED JAVASCRIPT IS UNTESTED ===============


function dweburl(command, table, hash) {
    var url = "http://"+dwebserver+":"+dwebport+"/"+ command + "/" + table + "/" + hash;
    return url;
}

function dweb_return(xmlhttp) {
    // utility function, pull result and return, report on error codes
    if (xmlhttp.readyState == XMLHttpRequest.DONE ) {
       if (xmlhttp.status == 200) {
            return xmlhttp.responseText;
       } else {
           alert('Error Status code '+xmlhttp.status);
       }
    }
   return null;
}
function dwebfile(div, table, hash) {
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        var text = dweb_return(xmlhttp);
        if (text) {
            document.getElementById(div).innerHTML = text;
        }
    };
    url = dweburl("file", table, hash) // Via dweb
    xmlhttp.open("GET", url, true);
    xmlhttp.send();
}
function dwebupdate(div, table, hash, type, data) {
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        var text = dweb_return(xmlhttp);
        if (text) {
            document.getElementById(div).innerHTML = text;
        }
    };
    url = dweburl("update", table, hash) + "/" + type;
    xmlhttp.open("POST", url, true);
    xmlhttp.setRequestHeader("Content-type", 'application/octet-stream');
    xmlhttp.send(data);
}

function dweblist(div, table, hash) {
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        var text = dweb_return(xmlhttp);
        if (text) {
            console.log("dweblist Retrieved",text);
            jb = JSON.parse(text)
            signatures = [];
            //console.log("Found items ", jb.length);
            for (var i = 0; i < jb.length; i++) {
                //alert("item"+jb[i]["hash"])
                signatures[i] = new Signature(jb[i]);
            }
            console.log("Found total of signatures=",signatures.length);
            //document.getElementById(div).innerHTML = text;
        }
    };
    url = dweburl("list", table, hash) // Via dweb
    xmlhttp.open("GET", url, true);
    xmlhttp.send();
}

<!-- alert("dweb.js loaded"); -->
<!-- https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes -->
