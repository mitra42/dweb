from KeyPair import KeyPair
from Errors import ForbiddenException, AuthenticationException, DecryptionFail
from CommonList import CommonList
from SmartDict import SmartDict
from Dweb import Dweb
from KeyChain import KeyChain


class AccessControlList(CommonList):
    """
    An AccessControlList is a list for each control domain, with the entries being who has access.

    To create a list, it just requires a key pair, like any other List

    Fields:
    accesskey:  Secret key with which things are encrypted. We are controlling who gets this.
    _list: Contains a list of signatures, each for a SmartDict each of which is:
        viewerkeypair: public URL of the KeyPair of an authorised viewer
        token:  accesskey encrypted with PublicKey from the KeyPair
    """
    table = "acl"

    @classmethod
    def new(cls, data=None, master=None, key=None, verbose=False, options=None, kc=None):
        """
        Create a new AccessControlList, store, add to keychain

        :param data,master,key,verbose,options: see new CommonList
        :param kc: Optional KeyChain to add to
        """
        acl = cls(data, master, key, verbose, options)  # Create ACL
        if master:
            kc = kc or Dweb.keychains[0]        # Default to first KeyChain
            if kc:
                kc.push(acl, verbose)
            else:
                acl.store(verbose)              # Ensure stored even if not put on KeyChain
            return acl

    def preflight(self, dd):
        """
        Prepare data for storage, ensure publickey available

        :param dd: dict containing data preparing for storage (from subclass)
        :returns: dict ready for storage if not modified by subclass
        """
        if (not self._master) and self.keypair._key["sign"]:
            dd["publickey"] = dd.get("publickey") or dd["keypair"].publicexport()   # Store publickey for verification

        # Super has to come after above as overrights keypair, also cant put in CommonList as MB's dont have a publickey and are only used for signing, not encryption
        return super(AccessControlList, self).preflight(dd)

    def add_acle(self, viewerpublicurl=None, verbose=False):
        """
        Add a new ACL entry - that gives a viewer the ability to see the accesskey of this URL

        :param viewerpublicurl: The url of the viewers KeyPair object (contains a publickey)
        :resolves to: this for chaining
        """
        if verbose: print "AccessControlList.add viewerpublicurl=",viewerpublicurl

        if not self._master:
            raise ForbiddenException(what="Cant add viewers to ACL copy")

        viewerpublickeypair = SmartDict.fetch(viewerpublicurl, verbose) # Fetch the public key will be KeyPair
        # Create a new ACLE with access key, encrypted by publickey
        acle = SmartDict({
                    #Need to go B64->binary->encrypt->B64
                    "token": viewerpublickeypair.encrypt(data=KeyPair.b64dec(self.accesskey), b64=True, signer=self),
                    "viewer": viewerpublicurl
                }, verbose=verbose)
        self.p_push(acle, verbose=verbose)
        return self

    def tokens(self, viewerkeypair=None, decrypt=True, verbose=False, **options):
        """
        Find the entries, if any, in the ACL for a specific viewer
        There might be more than one if either the accesskey changed or the person was added multiple times.
        Entries are SmartDict with token being the decryptable accesskey we want
        The ACL should have been p_list_then_elements() before so that this can run synchronously.

        :param viewerkeypair:  KeyPair of viewer
        :param decrypt: If should decrypt the
        :return:    Array of encrypted tokens (strings) or array of BINARY strings  (Note difference with JS #TODO-API)
        :throws:    CodingError if not yet fetched
        """

        if verbose: print "AccessControlList.tokens decrypt=",decrypt

        viewerurl = viewerkeypair._url

        # Find any sigs that match this viewerurl - should be decryptable
        toks = [ sig.data.token for sig in self._list if sig.data.viewer == viewerurl ]

        if decrypt:    # If requested, decrypt each of them
            toks = [ viewerkeypair.decrypt(data=str(tok), signer=self, outputformat="text") for tok in toks ]  # Note JS uses outputformat = "uint8array"
        return toks

    def encrypt(self, data, b64=False):
        """
        Encrypt some data based on the accesskey of this list.

        :param data: string - data to be encrypted
        :param b64: true if want result as urlbase64 string, otherwise string
        :return: string, possibly encoded in urlsafebase64
        """
        return KeyPair.sym_encrypt(data, self.accesskey, b64)

    def decrypt(self, data, viewerkeypair=None, verbose=False):
        """
        Decrypt data for a viewer.
        Chain is SD.p_fetch > SD.p_decryptdata > ACL|KC.decrypt, then SD.setdata

        :param data: string from json of encrypted data - b64 encrypted
        :param viewerkeypair:   Keypair of viewer wanting to decrypt, or array, defaults to all KeyPair in Dweb.keychains
        :return:                Decrypted data
        :throw:                 AuthenticationError if there are no tokens for our ViewerKeyPair that can decrypt the data
        """
        vks = viewerkeypair or KeyChain.mykeys(KeyPair)
        if not isinstance(vks, (list, tuple, set)): # // Convert singular key into an array
            vks = [ vks ]

        for vk in vks:
            # Find any tokens in ACL for this KeyPair and decrypt to get accesskey (maybe empty)
            for accesskey in self.tokens(viewerkeypair = vk, decrypt=True, verbose=verbose):
                try: # If can descrypt then return the data
                    return KeyPair.sym_decrypt(data=data, sym_key=accesskey, outputformat="text") #Exception DecryptionFail
                    # Dont continue to process when find one
                except DecryptionFail as e:  # DecryptionFail but keep going
                    pass    # Ignore if cant decode maybe other keys will work
        raise AuthenticationException(message="ACL.decrypt: No valid keys found")

    def _storepublic(self, verbose=False):
        """
        Store a public version of the ACL - should not include accesskey, or privatekey
        Note - does not return a promise, the store is happening in the background
        Sets _publicurl to the URL stored under.
        """
        if (verbose): print("AccessControlList._storepublic");
        #AC(data, master, key, verbose, options) {
        acl = AccessControlList(data={"name": self.name}, master=False, key=self.keypair, verbose=verbose, options={})
        acl.store(verbose)
        self._publicurl = acl._url

    @classmethod
    def decryptdata(cls, value, verbose=False):
        """
        Takes a dict,
        checks if encrypted (by presence of "encrypted" field, and returns immediately if not
        Otherwise if can find the ACL's url in our keychains then decrypt with it (it will be a KeyChain, not a ACL in that case.
        Else returns a promise that resolves to the data
        No assumption is made about what is in the decrypted data

        Chain is SD.p_fetch > SD.p_decryptdata > ACL.p_decrypt > ACL|KC.decrypt, then SD.setdata

        :param value: object from parsing incoming JSON that may contain {acl, encrypted} acl will be url of AccessControlList or KeyChain
        :return: data or promise that resolves to data
        :throws: AuthenticationError if cannot decrypt
        """
        if not value.get("encrypted"):
            return value
        else:
            #TODO-AUTHENTICATION probably add person - to - person version
            aclurl = value.get("acl")
            kc = KeyChain.keychains_find({"_publicurl": aclurl}, verbose=verbose)  # Matching KeyChain or None
            if kc:
                data = kc.decrypt(data=value["encrypted"], verbose=verbose) # Exception: DecryptionFail - unlikely since publicurl matches
            else:
                acl = SmartDict.fetch(url=aclurl, verbose=verbose) # Will be AccessControlList
                acl.p_list_then_elements(verbose)               # Will load blocks in sig as well
                data = acl.decrypt(data=value.get("encrypted"), viewerkeypair=None, verbose=verbose) #Resolves to data or throws AuthentictionError
            return Dweb.transport().loads(data)
