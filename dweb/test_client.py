# encoding: utf-8
from unittest import TestCase

from datetime import datetime
import os
from pathlib2 import Path
from json import loads, dumps
import base64
import time
from Crypto.PublicKey import RSA
import nacl.public
import nacl.signing
import nacl.encoding

from misc import _print
from CryptoLib import CryptoLib
from KeyPair import KeyPair
from Transport import TransportBlockNotFound, TransportURLNotFound, TransportFileNotFound
from TransportLocal import TransportLocal
from TransportHTTP import TransportHTTP
from TransportDist_Peer import TransportDistPeer, Peer, ServerPeer
from CommonBlock import Transportable
from Block import Block
from StructuredBlock import StructuredBlock
from CommonList import CommonList
from MutableBlock import MutableBlock
from AccessControlList import AccessControlList
from KeyChain import KeyChain
from File import File, Dir
from Dweb import Dweb
from ServerHTTP import DwebHTTPRequestHandler
#TODO-BACKPORT - review this file

class Testing(TestCase):
    def setUp(self):
        super(Testing, self).setUp()
        testTransporttype = 2 #TransportLocal, TransportHTTP, TransportDistPeer, TransportDistPeer = multi  # Can switch between TransportLocal and TransportHTTP to test both
        self.verbose=False
        self.quickbrownfox =  "The quick brown fox ran over the lazy duck"
        self.dog = "But the clever dog chased the fox"
        self.mydic = { "a": "AAA", "1":100, "B_date": datetime.now()}  # Dic can't contain integer field names
        self.ipandport = DwebHTTPRequestHandler.defaultipandport  # Serve it via HTTP on all addresses
        #self.ipandport = ('192.168.1.156',4243)  # Serve it via HTTP on all addresses
        self.exampledir = "../examples/"    # Where example files placed
        self.keytail = ["_rsa","_nacl"][CryptoLib.defaultlib]
        # Random valid mnemonic
        #self.mnemonic = "lecture name virus model jealous whisper stone broom harvest april notable lunch"  # 16byte
        #self.mnemonic = "olympic high dress found sport caution grant insect receive upper connect regret limit awesome image text bamboo dawn fold pen raccoon math delay virus" # 32 byte
        self.seed = "01234567890123456789012345678901"
        self.mnemonic="coral maze mimic half fat breeze thought champion couple muscle snack heavy gloom orchard tooth alert cram often ask hockey inform broken school cotton"
        if testTransporttype == 0: # TransportLocal:
            Dweb.transport = TransportLocal.setup({"local": {"dir": "../cache_local"}}, verbose=False)  # HTTP server is storing locally
        elif testTransporttype == 1: # TransportHTTP:
            # Run python -m ServerHTTP; before this
            Dweb.transport = TransportHTTP.setup({ "http": DwebHTTPRequestHandler.defaulthttpoptions }, self.verbose)
        elif testTransporttype in (2,3): # TransportDistPeer:
            #TODO-BACKPORT check its distpeer for TransportDistPeer
            Dweb.transport = TransportDistPeer.setup({ "distpeer": {}, "http": {"ipandport": DwebHTTPRequestHandler.defaultipandport}, "local": {"dir": "../cache"}}, self.verbose)
            Dweb.transport.peers.append(Peer(ipandport=ServerPeer.defaultipandport, verbose=self.verbose).connect())
            if testTransporttype == 3:
                #TODO replace this with a "learnfrom" experience, so connects background etc
                maxport = ServerPeer.defaultipandport[1]+10
                for i in range(ServerPeer.defaultipandport[1],maxport):
                    if self.verbose: print "Adding peer",i
                    Dweb.transport.peers.append(Peer(ipandport=(ServerPeer.defaultipandport[0],i), verbose=self.verbose).connect(verbose=self.verbose))
        else:
            assert False, "Unimplemented test for Transport "+testTransport.__class__.__name__

    def tearDown(self):
        time.sleep(1)   # Allow background thread to finish
        super(Testing, self).tearDown()

    def keyfromfile(self, keyname, keytype=None, private=False):
        """
        Load a key from a file, if file doesnt exist then create it with a new randome key.
        Note that in normal testing, the file will be created when the test is run first, then that key file will end up in git so will be same on all machines.
        """
        keypath = self.exampledir + keyname + self.keytail
        if not os.path.exists(keypath):
            keypair = KeyPair.keygen(keytype=keytype)
            data=keypair.privateexport if private else keypair.publicexport
            File._write(filepath=keypath, data=data)
        return File.load(filepath=keypath).content()

    # ======== STANDARD CREATION ROUTINES
    def _makeacl(self): # See test_keychain for use and canonical testing
        if self.verbose: print "Creating AccessControlList"
        # Create a acl for testing, - full breakout is in test_keychain
        accesskey=CryptoLib.randomkey()
        acl = AccessControlList(name="test_acl.acl", master=True, keypair=self.keyfromfile("test_acl1"+self.keytail, private=True, keytype=KeyPair.KEYTYPESIGN),
                                accesskey=CryptoLib.b64enc(accesskey), verbose=self.verbose)
        acl._allowunsafestore = True    # Not setting _acl on this
        h = acl.store(verbose=self.verbose)
        acl._allowunsafestore = False
        if self.verbose: print "Creating AccessControlList url=", acl._url
        return acl

    def _makesb(self, acl=None):    # See test_structuredblock for canonical testing of this
        """

        :param acl:
        :return:
        """
        if self.verbose: print "Create Structured Block"
        sb = StructuredBlock()
        sb.name = "test _sb"
        sb.data = self.quickbrownfox
        sb._acl = acl
        sb.store(verbose=self.verbose)  # Automatically encrypts based on ACL
        if self.verbose: print "Created Structured Block url=",sb._url
        return sb

    # ======== END OF STANDARD CREATION ROUTINES


    def test_Block(self):
        url = Block(data=self.quickbrownfox).store(verbose=self.verbose)._url
        block = Block(url=url, verbose=self.verbose).fetch(verbose=self.verbose)
        assert block._data == self.quickbrownfox, "Should return data stored"

    def test_StructuredBlock(self):
        # Test Structured block
        sb = StructuredBlock(data=CryptoLib.dumps(self.mydic), verbose=self.verbose)
        assert sb.a == self.mydic['a'], "Testing attribute access"
        multiurl = sb.store(verbose=self.verbose)._url
        sb2 = StructuredBlock(url=multiurl, verbose=self.verbose)
        sb2.fetch(verbose=self.verbose)
        assert sb2.a == self.mydic['a'], "Testing StructuredBlock round-trip"
        assert sb2.B_date == self.mydic["B_date"], "DateTime should survive round trip"

    def test_Signatures(self):
        # Test Signatures
        #self.verbose=True
        signedblock = StructuredBlock(data=self.mydic)
        keypair = KeyPair.keygen(keytype=KeyPair.KEYTYPESIGN)
        # This test should really fail, BUT since keypair has private it passes signature
        #commonlist0 = CommonList(keypair=keypair, master=False)
        #print commonlist0
        #signedblock.sign(commonlist0, verbose=self.verbose) # This should fail, but
        if self.verbose: print "test_Signatures CommonLost"
        CommonList.table = "BOGUS"  # Defeat errors
        commonlist = CommonList(keypair=keypair, keygen=True, master=True, name="test_Signatures.commonlist")
        if self.verbose: print "test_Signatures sign"
        commonlist._allowunsafestore = True
        signedblock.sign(commonlist, verbose=self.verbose)
        commonlist._allowunsafestore = False
        if self.verbose: print "test_Signatures verification"
        assert signedblock.verify(verify_atleastone=True, verbose=self.verbose), "Should verify"
        signedblock.a="A++"
        signedblock.dirty()
        assert not signedblock.verify(verify_atleastone=True, verbose=self.verbose), "Should fail"

    def test_MutableBlocks(self):
        #self.verbose=True
        if self.verbose: print "test_MutableBlocks: Create master"
        mblockm = MutableBlock(master=True, keygen=True, verbose=self.verbose)      # Create a new block with a new key
        mblockm._current.data = self.quickbrownfox                       # Put some data in it (goes in the StructuredBlock at _current
        mblockm._allowunsafestore = True                        # Avoid dependency on ACL and encryption in this test
        mblockm.signandstore(verbose=self.verbose)              # Sign it - this publishes it
        mblockm._allowunsafestore = False
        testurl0 = mblockm._current._url                      # Get a pointer to that version
        if self.verbose: print "test_MutableBlocks: Edit it"
        mblockm._current.data = self.dog                        # Put some different content in it
        mblockm._current.dirty()                                # Have to manually "dirty" it since already written
        mblockm._allowunsafestore = True                        # Avoid dependency on ACL and encryption in this test
        mblockm.signandstore(verbose=self.verbose)              # Publish new content
        mblockm.store()
        mblockm._allowunsafestore = False
        testurl = mblockm._current._url                       # Get a pointer to the new version
        mbmpuburl = mblockm._publicurl
        if self.verbose: print "test_MutableBlocks: And check it"
        mblock = MutableBlock(url=mbmpuburl, verbose=self.verbose)                     # Setup a copy (not Master) via the publickey
        mblock.fetch(verbose=self.verbose)                      # Fetch the content
        assert mblock._current._url == testurl, "Should match url stored above"
        assert mblock._list[0].url == testurl0, "Prev list should hold first stored"

    def test_LongFiles(self):
        from StructuredBlock import StructuredBlock
        sb1 = StructuredBlock({ "data": self.quickbrownfox}) # Note this is data held in the SB, as compared to _data which is data representing the SB
        assert sb1.size(verbose=self.verbose) == len(self.quickbrownfox), "Should get length"
        assert sb1.content(verbose=self.verbose) == self.quickbrownfox, "Should fetch string"
        multiurl = Block(data=self.dog).store(verbose=self.verbose)._url
        sb2 = StructuredBlock({ "url": multiurl})  # Note passing multiurl as the url of the data, not the url of the SB.
        assert sb2.content(verbose=self.verbose) == self.dog, "Should fetch dog string"
        assert sb2.size(verbose=self.verbose) == len(self.dog), "Should get length"
        slinksblock = StructuredBlock({ "links": [
                                            StructuredBlock({ "data": self.quickbrownfox}),
                                            StructuredBlock({ "url": multiurl}),
                                        ]})
        assert slinksblock.content(verbose=self.verbose) == self.quickbrownfox+self.dog, "Should get concatenation"
        assert slinksblock.size(verbose=self.verbose) == len(self.quickbrownfox)+len(self.dog), "Should get length"

    def test_http(self):
        # Run python -m ServerHTTP; before this
        multiurl = Block(data=self.quickbrownfox).store(verbose=self.verbose)._url
        block = Block(url=multiurl, verbose=self.verbose).fetch(verbose=self.verbose)
        assert block._data == self.quickbrownfox, "Should return data stored"

    def test_file(self):
        content = File.load(filepath=self.exampledir + "index.html", verbose=self.verbose).content(verbose=self.verbose)
        sb = StructuredBlock(**{"Content-type":"text/html"})  # ** because cant use args with hyphens\
        sb.data = content
        sb.store(verbose=self.verbose)
        if isinstance(Dweb.transport, TransportLocal):
            print "Can't run all of test_file on TransportLocal"
        else:
            sburl = sb.xurl(command="file", url_output="getpost") #TODO-BACKPORT expect to break
            assert sburl == [False, "file", ["sb", sb._url]]
            resp = Dweb.transport._sendGetPost(sburl[0], sburl[1], sburl[2], verbose=self.verbose)
            assert resp.text == content, "Should return data stored"
            assert resp.headers["Content-type"] == "text/html", "Should get type"
        # Now test a MutableBlock that uses this content
        mbm = MutableBlock(master=True, keypair=self.keyfromfile("index_html"+self.keytail, private=True, keytype=KeyPair.KEYTYPESIGN), contenturl=sb._url)
        mbm._allowunsafestore = True
        mbm.store().signandstore(verbose=self.verbose)
        mbm._allowunsafestore = False
        if self.verbose: print "store tells us:", mbm.content()
        assert mbm.content()==content, "Should match content stored"
        mb = MutableBlock(url=mbm._publicurl)
        mb.fetch()      # Just fetches the signatures
        assert mb.content() == mbm.content(), "Should round-trip HTML content"
        if isinstance(Dweb.transport, TransportLocal):
            pass # print "Can't run all of test_file on TransportLocal"
        else:
            getpostargs=mb.xurl(command="file", url_output="getpost")  #TODO-BACKPORT expect to break
            mbcontent2 = Dweb.transport._sendGetPost(*getpostargs).text
            assert mbcontent2 == mbm.content(), "Should fetch MB content via its URL"

    def test_typeoverride(self):    # See if can override the type on a block
        if isinstance(Dweb.transport, TransportLocal):
            print "Can't test_typeoverride on",Dweb.transport.__class__.__name__
            return
        Dweb.transport = TransportHTTP.setup({"http": {"ipandport": self.ipandport}}, self.verbose)
        # Store the wrench icon
        content = File.load(filepath=self.exampledir + "WrenchIcon.png").content()
        wrenchurl = Block(data=content).store(verbose=self.verbose)._url
        # And check it got there
        resp = Dweb.transport._sendGetPost(False, "rawfetch",  [wrenchurl], params={"contenttype": "image/png"})
        assert resp.headers["Content-type"] == "image/png", "Should get type"
        assert resp.content == content, "Should return data stored"
        resp = Dweb.transport._sendGetPost(False, "file",  ["b", wrenchurl], params={"contenttype": "image/png"})
        assert resp.headers["Content-type"] == "image/png", "Should get type"
        assert resp.content == content, "Should return data stored"

    def test_badblock(self):
        try:
            resp = Dweb.transport.rawfetch(url="12345")
            #resp = Dweb.transport._sendGetPost(False, "rawfetch", [ "12345"], params={"contenttype": "image/png"})
        except (TransportURLNotFound,TransportFileNotFound, TransportBlockNotFound) as e:
            pass
        else:
            assert False, "Should raise a TransportURLNotFound, TransportBlockNotFound or TransportFileNotFound error"

    def _storeas(self, filename, keyname, contenttype, **options):
        filepath = self.exampledir + filename
        if os.path.isdir(filepath):
            f = Dir.load(filepath=filepath, upload=True, verbose=self.verbose, option=options) # Recurses
        else:
            f = File.load(filepath=filepath, contenttype=contenttype, upload=True, verbose=self.verbose, **options)
        if self.verbose: print f
        if keyname:
            mbm = MutableBlock(master=True, keypair=self.keyfromfile(keyname, private=True, keytype=KeyPair.KEYTYPESIGN), contenturl=f._url, verbose=self.verbose)
            mbm._allowunsafestore = True    # TODO could encrypt these
            mbm.store(private=True, verbose=self.verbose)
            mbm.signandstore(verbose=self.verbose)
            mbm._allowunsafestore = False
            #print filename + " editable:" + mbm.privateurl()    # Side effect of storing
            #print filename + ":" + mbm.publicurl(command="file", table="mb")
            url = mbm.publicurl(command="file", table="mb")
            self.uploads[filename]  = { "publicurl": mbm._publicurl, "editable": mbm.privateurl(), "editableurl": mbm._url, "read": url, "relread": "/"+url.split('/', 3)[3], "contenturl": mbm._current._url}
            #print self.uploads[filename]
        else:
            #print filename + ":" + f.url(command="file", table="sb")
            url = f.xurl(command="file", table="sb")  #TODO-BACKPORT expect to break
            scheme, ipandport, unused, rest = url.split('/', 3)
            self.uploads[filename]  = { "publicurl": f._url, "relread": "/"+url.split('/', 3)[3], "read": url}
            #print self.uploads[filename]


    def test_uploads(self):
        # A set of tools to upload things so available for testing.
        # All the functionality in storeas should have been tested elsewhere.
        if isinstance(Dweb.transport, TransportLocal):
            print "Can't test_uploads on",Dweb.transport.__class__.__name__
            return
        ext = False   # True to upload larger directories (tinymce, docs)
        b=Block(data=self.dog); b.store(); print self.dog,b.xurl()  #TODO-BACKPORT expect to break
        self.uploads = {}
        #self._storeas("dweb.js", "dweb_js", "application/javascript")
        #self._storeas("jquery-3.1.1.js", None, "application/javascript")
        self._storeas("index.html", "index_html", "text/html")
        self._storeas("test.html", "test_html", "text/html")
        self._storeas("snippet.html", "snippet_html", "text/html")
        self._storeas("snippet2.html", "snippet_html", "text/html")
        self._storeas("WrenchIcon.png", None, "image/png")
        self._storeas("DWebArchitecture.png", "DwebArchitecture_png","image/png")
        self._storeas("objbrowser.html", "objbrowser_html", "text/html")
        #self._storeas("libsodium", None, None)
        self._storeas("../dweb_bundled.js","dweb_bundled_js", "application/javascript")

        if ext: # Not uploaded if doing fast cycle dev
            self._storeas("../tinymce", "tinymce", None)
            self._storeas("../docs/_build/html", "docs_build_html", None)
        #self._storeas("mnemonic.js", None, None)
        print "INDEX.HTML at",self.uploads["index.html"]["read"]
        print "dweb_bundled.js", self.uploads["../dweb_bundled.js"]["relread"]
        #print "jquery-3.1.1.js",self.uploads["jquery-3.1.1.js"]["relread"]
        #print "libsodium", self.uploads["libsodium"]["relread"]+"/sodium.js"
        #print "dweb.js",self.uploads["dweb.js"]["relread"]
        if ext: print "../tinymce/tinymce.min.js", self.uploads["../tinymce"]["relread"]+"/tinymce.min.js"
        print "snippet.html", self.uploads["snippet.html"]["editableurl"]
        print "cleverdog", b._url
        print "snippet.html content", self.uploads["snippet.html"]["contenturl"]
        print "snippet.html", self.uploads["snippet.html"]["relread"]
        print "WrenchIcon.png", self.uploads["WrenchIcon.png"]["relread"]
        print "DWebArchitecture.png", self.uploads["DWebArchitecture.png"]["relread"]
        if ext: print "Sphinx Documentation", self.uploads["../docs/_build/html"]["relread"]
        print "test.html",self.uploads["test.html"]["relread"]
        print "objbrowser.html", self.uploads["objbrowser.html"]["relread"]
        print "TEST.HTML at",self.uploads["test.html"]["read"]
        print "or OBJECTBROWSER.HTML at", self.uploads["objbrowser.html"]["read"]
        print "dweb_bundled.js", self.uploads["../dweb_bundled.js"]["relread"]
        #print "libsodium", self.uploads["libsodium"]["relread"]+"/sodium.js"
        #print "dweb.js",self.uploads["dweb.js"]["relread"]
        if ext: print "mburl Tinymce", self.uploads["../tinymce"]["publicurl"]
        if ext: print "mb2url Sphinx docs", self.uploads["../docs/_build/html"]["publicurl"]
        if ext: print "sburl Tinymce cont", self.uploads["../tinymce"]["contenturl"]
        print "EXPERIMENTAL"
        #print "mnemonic.js", self.uploads["mnemonic.js"]["relread"]+"/mnemonic.js"

    def test_uploadandrelativepaths(self):
        # Test that a directory can be uploaded and then accessed by a relative path
        if isinstance(Dweb.transport, TransportLocal):
            print "Can't test_uploadandrelativepaths on",Dweb.transport.__class__.__name__
            return
        f1sz = File.load("../tinymce/langs/readme.md").size
        # Upload a multi-level directory
        f = Dir.load(filepath="../tinymce", upload=True, verbose=self.verbose,)
        #print f.url()  # url of sb at top of directory
        sb = StructuredBlock(url=f._url, verbose=self.verbose).fetch(verbose=self.verbose)
        assert len(sb.links) == 7, "tinymce should have 7 files but has "+str(len(sb.links))
        resp = Dweb.transport._sendGetPost(False, "file", ["sb", f._url,"langs/readme.md"])
        assert int(resp.headers["Content-Length"]) == f1sz,"Should match length of readme.md"
        # /file/mb/SHA3256B64URL.88S-FYlEN1iF3WuDRdXoR8SyMUG6crR5ehM21IvUuS0=/tinymce.min.js

    def test_crypto(self):
        if self.verbose: print "test_crypto: tests of the crypto library - esp round trips through functions"
        # Try symetric encrypt/decrypt
        symkey = CryptoLib.randomkey()
        enc = CryptoLib.sym_encrypt(self.quickbrownfox, symkey)
        dec = CryptoLib.sym_decrypt(enc, symkey)
        assert dec == self.quickbrownfox
        if CryptoLib.defaultlib == CryptoLib.NACL:
            keypair = KeyPair.keygen(keytype=KeyPair.KEYTYPEENCRYPT)
            svpair = KeyPair.keygen(keytype=KeyPair.KEYTYPESIGN)
            svpair_key = svpair._key.encode(nacl.encoding.RawEncoder)
            svpair_encrypt = nacl.public.PrivateKey(svpair_key)
            newkey = svpair_encrypt.encode(nacl.encoding.RawEncoder)
            print "FAILING", "assert svpair_key != newkey", "TODO - Looks like PrivateKey didn't actually use as a seed"
            sendingbox = nacl.public.Box(svpair_encrypt, keypair._key.public_key)
            #print "sendingbox.sharedsecret=",sendingbox.shared_key()
            encmsg = sendingbox.encrypt(self.quickbrownfox)
            receivingbox = nacl.public.Box(keypair._key, svpair_encrypt.public_key)
            #print "receivingbox.sharedsecret=",receivingbox.shared_key()
            assert sendingbox.shared_key() == receivingbox.shared_key()
            res = receivingbox.decrypt(encmsg)
            assert res == self.quickbrownfox
            #print res
            assert sendingbox.encode(nacl.encoding.URLSafeBase64Encoder) == receivingbox.encode(nacl.encoding.URLSafeBase64Encoder)
            seed = "01234567890123456789012345678901"
            boxkey = nacl.public.PrivateKey(seed)
            pe = boxkey.encode(nacl.encoding.RawEncoder)
            assert seed == pe
        else:
            # Try RSA encrypt/decrypt
            keypair = KeyPair.keygen()
            enc = keypair.encrypt(self.quickbrownfox)
            enclong = keypair.encrypt(self.quickbrownfox*100)
            dec = keypair.decrypt(enc)
            assert dec == self.quickbrownfox
        #These should work for any defaultlib
        foo = KeyPair.keygen(keytype=KeyPair.KEYTYPESIGN, seed=self.seed)
        assert foo.mnemonic == self.mnemonic



    def test_keychain(self):
        """
        This is a supercomplex test, that effectively tests a lot of subsystems including AccessControlLists, KeyChains and encryption in transport
        """
        #self.verbose=True
        if self.verbose: print "KEYCHAIN 0 - create"
        # Not using KeyChain.new as don't want to fetch for test, .new is tested below
        kc = KeyChain(mnemonic=self.mnemonic, verbose=self.verbose, name="test_keychain kc").store(verbose=self.verbose)
        KeyChain.addkeychains(kc)
        if self.verbose: print "KEYCHAIN 1 - add mbm to it"
        mblockm = MutableBlock.new(name="test_keychain mblockm", acl=kc, content=self.quickbrownfox, _allowunsafestore=True, signandstore=True, verbose=self.verbose)
        mbmurl = mblockm._url
        kc.add(mblockm, verbose=self.verbose)   # Sign and store on KC's list
        if self.verbose: print "KEYCHAIN 2 - add viewerkeypair to it"
        vkpname="test_keychain viewerkeypair"
        viewerkeypair = KeyPair(name=vkpname, key=self.keyfromfile("test_viewer1"+self.keytail, private=True, keytype=KeyPair.KEYTYPEENCRYPT))
        viewerkeypair._acl = kc
        viewerkeypair.store(verbose=self.verbose) # Defaults to store private=False
        kc.add(viewerkeypair, verbose=self.verbose)
        if self.verbose: print "KEYCHAIN 3: Fetching mbm url=",mbmurl
        mbm2 = MutableBlock(url=mbmurl, master=True, verbose=self.verbose, name="test_keychain mbm2")
        mbm2.fetch(verbose=self.verbose)
        assert mbm2.name == mblockm.name, "Names should survive round trip"
        if self.verbose: print "KEYCHAIN 4: reconstructing KeyChain and fetch"
        Dweb.keychains = [] # Clear Key Chains
        kcs2 = KeyChain.new(mnemonic=self.mnemonic, verbose=self.verbose, name="test_keychain kc") # Note only fetches if name matches
        if self.verbose: print "KEYCHAIN 5: Check MBM carried ok"
        mbm3 = kcs2.mymutableBlocks()[-1]
        assert mbm3.__class__.__name__ == "MutableBlock", "Should be a mutable block"
        assert mbm3.name == mblockm.name, "Names should survive round trip"
        if self.verbose: print "KEYCHAIN 5: Check can user ViewerKeyPair"
        acl = self._makeacl()   # Create Access Control List    - dont require encrypting as pretending itssomeone else's
        acl._allowunsafestore = True
        acl.add(viewerpublicurl=viewerkeypair._url, verbose=self.verbose)   # Add us as viewer
        sb = self._makesb(acl=acl)   # Encrypted obj
        assert KeyChain.myviewerkeys()[0].name == vkpname, "Should find viewerkeypair stored above"
        if self.verbose: print "KEYCHAIN 6: Check can fetch and decrypt - should use viewerkeypair stored above"
        sb2 = StructuredBlock(url=sb._url, verbose=self.verbose).fetch(verbose=self.verbose) # Fetch & decrypt
        assert sb2.data == self.quickbrownfox, "Data should survive round trip"
        if self.verbose: print "KEYCHAIN 7: Check can store content via an MB"
        print "XXX@428 - next line looks wrong, mbm doesn't ahve a content field"
        mblockm = MutableBlock.new(contentacl=acl, name="mblockm", _allowunsafestore=True, content=self.quickbrownfox, signandstore=True, verbose=self.verbose)  # Simulate other end
        mb = MutableBlock(name="test_acl mb", url=mblockm._publicurl, verbose=self.verbose)
        assert mb.content(verbose=self.verbose) == self.quickbrownfox, "should round trip through acl"
        if self.verbose: print "test_keychain: done"
        #TODO - named things in keychain
        #TODO - test_keychain with HTML


    def test_peer(self):
        # def test_peer(self):
        # Experimental testing of peer
        #self.verbose=True
        # Use cache as the local machine's - remote will use cache_peer
        if not isinstance(Dweb.transport, TransportDistPeer):
            print "Can't run test_peer on ",Dweb.transport.__class__.__name__
            return
        if CryptoLib.defaultlib == CryptoLib.CRYPTO:
            qbfurl="SHA3256B64URL.heOtR2QnWEvPuVdxo-_2nPqxCSOUUjTq8GShJv8VUFI="    # Hash of self.quickbrownfox
            cdurl = "SHA3256B64URL.50GNWgUQ9GgrVfMvpedEg77ByMRYkUgPRU9P1gWaNF8="  # Hash of self.dog "Clever Dog" string saved in test_upload
            newdataurl = "SHA3256B64URL.ZhVKuERkgeQtVaTnfLxU2QRpBptdk11J8vw30G8DhIU="
        else:
            qbfurl = "BLAKE2.YOanaCqfg3UsKoqlNmVG7SFwLgDyB3aToEmLCH-vOzs="
            cdurl = "BLAKE2.A5JOSLvsRV-dFuFqNlpQeBP5OojtIuJmUq9mmoAJXkA="
            newdataurl = "BLAKE2.nlUV_dAC5psmShv8jSCmDAa1-LWGbMrGKOQ2PkHcx5g="
        newdata = "I am a new piece of data"    # Note *not* stored by any other test here
        url = Dweb.transport.rawstore(data=self.quickbrownfox, verbose=self.verbose)
        assert url == qbfurl, "Stored correctly (locally - no peers connected yet, got "+url+" expected "+qbfurl
        data = Dweb.transport.rawfetch(url=qbfurl,verbose=self.verbose)
        assert data == self.quickbrownfox, "Local cache of quick brown fox"+data
        invalidurl="SHA3256B64URL.aaaabbbbccccVfMvpedEg77ByMRYkUgPRU9P1gWaNF8="
        try:
            data = Dweb.transport.rawfetch(url=invalidurl,verbose=self.verbose)
        except (TransportBlockNotFound, TransportFileNotFound) as e:
            if self.verbose: print e
        else:
            assert False, "Should trigger exception"
        # This chunk may end up in a method on TransportDist_Peer
        node = Dweb.transport
        ipandport = ServerPeer.defaultipandport
        peer = node.peers.find(ipandport=ipandport) # Returns single result
        if not peer:
            peer = Peer(ipandport=ipandport, verbose=self.verbose)    # Dont know nodeid yet
            node.peers.append(peer)
        peer.connect(verbose=self.verbose)
        assert peer.connected
        assert peer.info["type"] == "DistPeerHTTP","Unexpected peer.info"+repr(peer.info)
        # Now we've got a peer so try again, should get bounced off peer server
        try:
            data = Dweb.transport.rawfetch(url=invalidurl, verbose=self.verbose)
        except TransportBlockNotFound as e:
            if self.verbose: print e
        else:
            assert False, "Should trigger exception"
        assert Dweb.transport.rawstore(data=self.dog, verbose=self.verbose) == cdurl
        assert Dweb.transport.rawfetch(url=cdurl, verbose=self.verbose) == self.dog
        maxport = ServerPeer.defaultipandport[1]+10
        for i in range(ServerPeer.defaultipandport[1],maxport):
            if self.verbose: print "Adding peer",i
            Dweb.transport.peers.append(Peer(ipandport=(ServerPeer.defaultipandport[0],i), verbose=self.verbose).connect(verbose=self.verbose))
        url = Dweb.transport.rawstore(data=newdata, verbose=self.verbose)
        assert newdataurl == url,"urles dont match exp "+newdataurl+" got "+url
        assert newdata == Dweb.transport.rawfetch(url=newdataurl, verbose=self.verbose, ignorecache=True)

    def Xtest_current(self):
        self.verbose=True
        self.test_keychain()
        #self.test_keychain()

        #self.uploads = {}
        #self._storeas("libsodium", None, None)
        #self._storeas("test.html", "test_html", "text/html")
        #print "EXPERIMENTAL"
        #print "test.html",self.uploads["test.html"]["read"]
        #print "libsodium", self.uploads["libsodium"]["relread"]+"/sodium.js"



