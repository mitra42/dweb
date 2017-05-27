from CryptoLib import CryptoLib, KeyPair, AuthenticationException, DecryptionFail
import nacl.signing
import nacl.encoding
from misc import ForbiddenException
from CommonList import EncryptionList

class AccessControlList(EncryptionList):
    """
    An AccessControlList is a list for each control domain, with the entries being who has access.

    To create a list, it just requires a key pair, like any other List

    See Authentication.rst
    From EncryptionList: accesskey   Key with which things on this list are encrypted
    From CommonList: keypair, _publichash, _list, _master, name

    """
    table = "acl"

    def preflight(self, dd):   #TODO-REFACTOR all preflight to have dd defined by caller (store)
        if (not self._master) and isinstance(self.keypair._key, nacl.signing.SigningKey):
            dd["naclpublic"] = dd.get("naclpublic") or dd["keypair"].naclpublicexport()   # Store naclpublic for verification
        # Super has to come after above as overrights keypair, also cant put in CommonList as MB's dont have a naclpublic and are only used for signing, not encryption
        return super(AccessControlList, self).preflight(dd)

    def add(self, viewerpublichash=None, verbose=False, **options):
        """
        Add a new ACL entry
        Needs publickey of viewer

        :param self:
        :return:
        """
        if verbose: print "AccessControlList.add viewerpublichash=",viewerpublichash
        if not self._master:
            raise ForbiddenException(what="Cant add viewers to ACL copy")
        viewerpublickeypair = KeyPair(hash=viewerpublichash).fetch(verbose=verbose)
        aclinfo = {
            # Need to go B64->binary->encrypt->B64
            "token": viewerpublickeypair.encrypt(CryptoLib.b64dec(self.accesskey), b64=True, signer=self),
            "viewer": viewerpublichash,
        }
        sb = StructuredBlock(data=aclinfo)
        self.signandstore(sb, verbose, **options)
        return self # For chaining

    def tokens(self, viewerkeypair=None, verbose=False, decrypt=True, **options):
        """
        Find the entries for a specific viewer
        There might be more than one if either the accesskey changed or the person was added multiple times.
        Entries are StructuredBlocks with token being the decryptable token we want

        :param viewerkeypair:  KeyPair of viewer
        :param verbose:
        :param options:
        :return:
        """
        if verbose: print "AccessControlList.tokens decrypt=",decrypt
        self.fetch(verbose=verbose, fetchblocks=False)
        viewerhash = viewerkeypair._hash
        toks = [ a.block().token for a in self._list if a.block().viewer == viewerhash ]
        if decrypt:
            toks = [ viewerkeypair.decrypt(str(a), b64=True, signer=self) for a in toks ]
        return toks

    def encrypt (self, res, b64=False):
        """
        Encrypt an object (usually represented by the json string). Pair of .decrypt()

        :param res: The material to encrypt, usually JSON but could probably also be opaque bytes
        :param b64: 
        :return: 
        """
        return CryptoLib.sym_encrypt(res, CryptoLib.b64dec(self.accesskey), b64=b64)

    def decrypt(self, data, viewerkeypair=None, verbose=False):
        """

        :param data: string from json - b64 encrypted
        :param viewerkeypair:
        :param verbose:
        :return:
        """
        #vks = viewerkeypair or AccessControlList.myviewerkeys
        vks = viewerkeypair or KeyChain.myviewerkeys()
        if not isinstance(vks, (list, tuple, set)):
            vks = [ vks ]
        for vk in vks:
            for symkey in self.tokens(viewerkeypair = vk, decrypt=True, verbose=verbose):
                try:
                    r = CryptoLib.sym_decrypt(data, symkey, b64=True) #Exception DecryptionFail
                    return r    # Dont continue to process when find one
                except DecryptionFail as e:  # DecryptionFail but keep going
                    pass    # Ignore if cant decode maybe other keys will work
        raise AuthenticationException(message="ACL.decrypt: No valid keys found")

