// Javascript library for dweb
//TODO very much at experimental stage expect it all to change
//TODO rename this to just ajax OR make it specific
function loadXMLDoc() {
    var xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function() {
        if (xmlhttp.readyState == XMLHttpRequest.DONE ) {
           if (xmlhttp.status == 200) {
               document.getElementById("myDiv").innerHTML = xmlhttp.responseText;
           }
           else if (xmlhttp.status == 400) {
              alert('There was an error 400');
           }
           else {
               alert('Status code '+xmlhttp.status);
           }
        }
    };
    xmlhttp.open("GET", "/dweb/examples/snippet.html", true);
    xmlhttp.send();
}

var dwebserver = 'localhost'
var dwebport = '4243'

function dweburl(command, table, hash) {
    var url = "http://"+dwebserver+":"+dwebport+"/"+ command + "/" + table + "/" + hash;
    return url;
}

function dwebget() {
    var xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function() {
        if (xmlhttp.readyState == XMLHttpRequest.DONE ) {
           if (xmlhttp.status == 200) {
               document.getElementById("myDiv").innerHTML = xmlhttp.responseText;
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
    url = dweburl("file", "mb", "SHA3256B64URL.qfXDp8M0AIKQ3_d0kX0Isbl4uakA3SVujPys_IB5SZk=")
    xmlhttp.open("GET", url, true);
    xmlhttp.send();
}
function dwebsend() {
    var xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function() {
        if (xmlhttp.readyState == XMLHttpRequest.DONE ) {
           if (xmlhttp.status == 200) {
               document.getElementById("myDiv").innerHTML = xmlhttp.responseText;
           }
           else if (xmlhttp.status == 400) {
              alert('There was an error 400');
           }
           else {
               alert('Status code '+xmlhttp.status);
           }
        }
    };
    url = dweburl("file", "mb", "SHA3256B64URL.qfXDp8M0AIKQ3_d0kX0Isbl4uakA3SVujPys_IB5SZk=")
    xmlhttp.open("GET", "/dweb/examples/snippet.html", true);
    xmlhttp.send();
}

<!-- alert("dweb.js loaded"); -->
