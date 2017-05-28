from Dweb import Dweb
from CryptoLib import WordHashKey
from MutableBlock import MutableBlock

_verbose = False

def mnemonicgen(verbose=False):
    return WordHashKey.generate()


def keychain(mnemonic=None):
    """
    Create or load a keychain, and add to Dweb.keychains

    :param mnemonic: Optional set of mnemonic words to build keychain from.
    :return:
    """
    from KeyChain import KeyChain
    from CryptoLib import WordHashKey, WordHashKey
    from KeyPair import KeyPair
    return KeyChain.new(mnemonic=mnemonic, keygen=(False if mnemonic else WordHashKey), verbose=_verbose)


def verbose(cls, new=None):
    """
    Set, or toggle verbosity

    :param new: If set then verbose becomes this, otherwise toggled
    :return:
    """
    global _verbose
    if new is not None:
        _verbose = new
    else:
        _verbose = not _verbose
    print "Setting verbose to", _verbose

def mb(acl=None, contentacl=None, name=None, _allowunsafestore=False, content=None, signandstore=None, **options):
    if not acl:
        acl = Dweb.keychains[0] # First keychain
    if signandstore is None:
        signandstore = content is not None
    return MutableBlock.new(acl=acl, contentacl=contentacl, name=name, _allowunsafestore=_allowunsafestore,
                            content=content, verbose=_verbose, sigandstore=signandstore)


print "Testing commandline"
verbose(True)
Dweb.settransport("local")
#Dweb.transport("http")
keychain()
mb(name="My MB", content="Have a nice day")
#keychain(mnemonic, verbose=verbose)

print "TESTED COMMAND LINE"

