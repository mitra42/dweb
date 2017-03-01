// Javascript library for dweb

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
               document.getElementById(div).innerHTML = xmlhttp.responseText;
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
function dwebupdate(div, table, hash, type, data) {
    var xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function() {
        if (xmlhttp.readyState == XMLHttpRequest.DONE ) {
           if (xmlhttp.status == 200) {
               document.getElementById(div).innerHTML = xmlhttp.responseText;
           }
           else if (xmlhttp.status == 400) {
              alert('There was an error 400');
           }
           else {
               alert('Status code '+xmlhttp.status);
           }
        }
    };
    url = dweburl("update", table, hash) + "/" + type;
    xmlhttp.open("POST", url, true);
    //Send the proper header information along with the request
    xmlhttp.setRequestHeader("Content-type", 'application/octet-stream');
    //xmlhttp.setRequestHeader("Content-Length", data.length);  // Not allowed to set this, it gets it automatically
    xmlhttp.send(data);
}

<!-- alert("dweb.js loaded"); -->
