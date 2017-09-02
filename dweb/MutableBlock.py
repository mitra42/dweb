# encoding: utf-8

from StructuredBlock import StructuredBlock
from misc import AssertionFail
from CommonList import CommonList
from AccessControlList import AccessControlList
#TODO-BACKPORT - review this file

class MutableBlock(CommonList):
    """
    Encapsulates a block that can change.
    Get/Set non-private attributes writes to the StructuredBlock at _current.

    {   _current: StructuredBlock       Most recently published item
        _list: [ StructuredBlock* ] }   List of all published item (think of as previous versions)
        contentacl                      ACL, or its hash to use for content (note the MB itself is encrypted with via its own _acl field)
        From CommonList: _publichash, _master bool, keypair
        From SmartDict: _acl,
        From Transportable: _data, _hash
    """
    table = "mb"

    def __init__(self, master=False, keypair=None, data=None, hash=None, contenthash=None, contentacl=None, keygen=False, verbose=False, **options):
        """
        Create and initialize a MutableBlock
        Adapted to dweb.js.MutableBlock.constructor
        Exceptions: PrivateKeyException if passed public key and master=True


        :param data: Public or Private key text as exported by "PEM"
        :param hash: of key
        :param contenthash: hash of initial content (only currently applicable to master)
        :param options: # Can indicate how to initialize content
        """
        # This next line for "hash" is odd, side effect of hash being for content with MB.master and for key with MB.!master
        if verbose: print "MutableBlock( keypair=",keypair, "data=",data, "hash=", hash, "keygen=", keygen, "options=", options,")"
        super(MutableBlock, self).__init__(master=master, keypair=keypair, data=data, hash=hash, keygen=keygen, verbose=verbose, **options)
        # Exception PrivateKeyException if passed public key and master=True
        self.contentacl = contentacl    # Hash of content when publishing - calls contentacl.setter which retrieves it , only has meaning if master - triggers setter on content
        self._current = StructuredBlock(hash=contenthash, verbose=verbose) if master else None # Create a place to hold content, pass hash to load content
        #OBS - table is always mb: self.__dict__["table"] = "mbm" if master else "mb"

    @property
    def contentacl(self):
        return self.__dict__.get("contentacl", None)

    @contentacl.setter
    def contentacl(self, value):
        """
        Set the contentacl used to control whether content encrypted or not

        :param value: hash, AccessControlList or None
        """
        if value:
            if not isinstance(value, AccessControlList):
                value = AccessControlList(value)
        self.__dict__["contentacl"] = value

    def fetch(self, verbose=False, **options):
        """
        Copied to dweb.js.

        :return: self for chaining
        """
        if verbose: print "MutableBlock.fetch pubkey=",self._hash
        super(MutableBlock, self).fetch(verbose=verbose, fetchblocks=False, **options)  # Dont fetch old versions
        if len(self._list):
            sig = self._list[-1] # Note this is the last of the list, if lists can get disordered then may need to sort
            self._current = sig and sig.block() # Fetch current content
        return self # For chaining

    def content(self, verbose=False, **options):
        self.fetch()    # defaults fetchlist=True, fetchblocks=False
        self._current = self._current.fetch()   # To fetch just the current block (the assignment is because will change class)
        return self._current.content(verbose=verbose, **options)

    def file(self, verbose=False, **options):
        if verbose: print "MutableBlock.file", self
        self.fetch(verbose=verbose, **options)    #TODO-EFFICIENCY look at log for test_file, does too many fetches and lists
        if not self._current:
            raise AssertionFail(message="Looking for a file on an unloaded MB")
        return self._current.file(verbose=verbose, **options)

    def signandstore(self, verbose=False, **options):
        """
        Sign and Store a version, or entry in MutableBlock master
        Exceptions: SignedBlockEmptyException if neither hash nor structuredblock defined, ForbiddenException if !master

        :return: self to allow chaining of functions
        """
        if (not self._current._acl) and self.contentacl:
            self._current._acl = self.contentacl    # Make sure SB encrypted when stored
            self._current.dirty()   # Make sure stored again if stored unencrypted. - _hash will be used by signandstore
        return super(MutableBlock, self).signandstore(self._current, verbose=verbose, **options) # ERR SignedBlockEmptyException, ForbiddenException

    def path(self, urlargs, verbose=False, **optionsignored):
        return self._current.path(urlargs, verbose)  # Pass to _current, (a StructuredBlock)  and walk its path


    @classmethod
    def new(cls, acl=None, contentacl=None, name=None, _allowunsafestore=False, content=None, signandstore=False, verbose=False, **options):
        """
        Utility function to allow creation of MB in one step

        :param acl:             Set to an AccessControlList or KeyChain if storing encrypted (normal)
        :param contentacl:      Set to enryption for content
        :param name:            Name of block (optional)
        :param _allowunsafestore: Set to True if not setting acl, otherwise wont allow storage
        :param content:         Initial data for content
        :param verbose:
        :param signandstore:    Set to True if want to sign and store content, can do later
        :param options:
        :return:
        """
        # See test_mutableblock for canonical testing of this
        if verbose: print "MutableBlock.new: Creating MutableBlock", name
        mblockm = cls(name=name, master=True, keygen=True, contentacl=contentacl, verbose=verbose)  # Create a new block with a new key
        mblockm._acl = acl              # Secure it
        mblockm._current.data = content  # Preload with data in _current.data
        if _allowunsafestore:
            mblockm._allowunsafestore = True
            mblockm.keypair._allowunsafestore = True
        mblockm.store()
        if signandstore and content:
            mblockm.signandstore(verbose=verbose)  # Sign it - this publishes it
        if verbose: print "Created MutableBlock hash=", mblockm._hash
        return mblockm


