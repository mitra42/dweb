// Javascript library for dweb
//TODO very much at experimental stage expect it all to change
//TODO rename this to just ajax OR make it specific

var dwebserver = 'localhost'
var dwebport = '4243'

function dweburl(command, table, hash) {
    var url = "http://"+dwebserver+":"+dwebport+"/"+ command + "/" + table + "/" + hash;
    return url;
}

function dwebget(div, table, hash) {
    var xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function() {
        if (xmlhttp.readyState == XMLHttpRequest.DONE ) {
           if (xmlhttp.status == 200) {
               document.getElementById(div).innerHTML = xmlhttp.responseText; //TODO parameterise destination
           }
           else if (xmlhttp.status == 400) {
              alert('There was an error 400');
           }
           else {
               alert('Status code '+xmlhttp.status);
           }
        }
    };
    //url = "/dweb/examples/snippet.html" // Fixed example
    //url = dweburl("file", "mb", "SHA3256B64URL.CLw7p4lteb5oxmXBkuk9lDqM89hRic7RPITGWg1AAD4=") // Via dweb
    url = dweburl("file", table, hash) // Via dweb
    xmlhttp.open("GET", url, true);
    xmlhttp.send();
}
function dwebupdate(div, table, hash, data) {
    var xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function() {
        if (xmlhttp.readyState == XMLHttpRequest.DONE ) {
           if (xmlhttp.status == 200) {
               document.getElementById(div).innerHTML = xmlhttp.responseText; //TODO parameterise destination
           }
           else if (xmlhttp.status == 400) {
              alert('There was an error 400');
           }
           else {
               alert('Status code '+xmlhttp.status);
           }
        }
    };
    url = dweburl("update", table, hash) + "/" + "text%2Fhtml"  //TODO parameterise type
    xmlhttp.open("POST", url, true);    //TODO how to send data
    //Send the proper header information along with the request
    xmlhttp.setRequestHeader("Content-type", 'application/octet-stream');
    //xmlhttp.setRequestHeader("Content-Length", data.length);  // Not allowed to set this, it gets it automatically
    xmlhttp.send(data);
}

<!-- alert("dweb.js loaded"); -->
