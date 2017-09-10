# encoding: utf-8
import dateutil.parser  # pip py-dateutil
from Errors import ToBeImplementedException
from Dweb import Dweb
from Transportable import Transportable

class SmartDict(Transportable):
    """
    Subclass of Transport that stores a data structure, usually a single layer Javascript dictionary object.
    SmartDict is intended to support the mechanics of storage and retrieval while being  subclassed to implement functionality
    that understands what the data means.

    By default any fields not starting with “_” will be stored, and any object will be converted into its url.

    The hooks for encrypting and decrypting data are at this level, depending on the _acl field, but are implemented by code in KeyPair.

     _acl If set (on master) defines storage as encrypted
    """
    table = "sd"

    def __init__(self, data=None, url=None, verbose=False, **options):
        """
        Creates and initialize a new SmartDict.

        :param data:	String|Object, If a string (typically JSON), then pass to Transport.loads first.
                A object with attributes to set on SmartDict via _setdata
        :param options:	Passed to _setproperties, by default overrides attributes set by data


        """
        super(SmartDict, self).__init__(data=data) # Uses _data.setter to set data
        self._setproperties(options)                # Note overrides any properties stored with data

    def __str__(self):
        return self.__class__.__name__+"("+str(self.__dict__)+")"

    def __repr__(self):
        return repr(self.__dict__)

    # Allow access to arbitrary attributes, allows chaining e.g. xx.data.len
    def __setattr__(self, name, value):
        # THis code was running self.dirty() - problem is that it clears url during loading from the dWeb
        if name[0] != "_":
            if "date" in name and isinstance(value,basestring):
                value = dateutil.parser.parse(value)
        return super(SmartDict, self).__setattr__(name, value)  # Calls any property esp _data

    def _setproperties(self, options):
        for k in options:
            self.__setattr__(k, options[k])

    def __getattr__(self, name):    # Need this in Python while JS supports foo._url
        return self.__dict__.get(name)



    def _setproperties(self, value):
        for k in value:
            self.__setattr__(k, value[k])

    def preflight(self, dd):
        """
        Default handler for preflight, strips attributes starting “_” and stores and converts objects to urls.
        Subclassed in AccessControlList and KeyPair to avoid storing private keys.
        :param dd:	dictionary to convert..
        :return:	converted dictionary
        """
        res = {
            k: dd[k].store()._url if isinstance(dd[k], Transportable) else dd[k]
            for k in dd
            if k[0] != '_'
        }
        res["table"] = res.get("table",self.table)  # Assumes if used table as a field, that not relying on it being the table for loading
        assert res["table"]
        return res

    def _getdata(self):
        """
        Prepares data for sending. Retrieves attributes, runs through preflight.
        If there is an _acl field then it passes data through it for encrypting (see AccessControl library)
        Exception: UnicodeDecodeError - if its binary
        :return:	String suitable for p_rawstore
        """
        try:
            res = self.transport().dumps(self.preflight(self.__dict__.copy())) # Should call self.dumps below { k:self.__dict__[k] for k in self.__dict__ if k[0]!="_" })
        except UnicodeDecodeError as e:
            print "Unicode error in StructuredBlock"
            print self.__dict__
            raise e
        if self._acl:   # Need to encrypt
            encdata = self._acl.encrypt(res, b64=True)
            dic = {"encrypted": encdata, "acl": self._acl._publicurl, "table": self.table}
            res = self.transport().dumps(dic)
        return res

    def _setdata(self, value):
        """
        Stores data, subclass this if the data should be interpreted as its stored.

        :param value:	Object, or JSON string to load into object.
        """

        if value:  # Just skip if no initialization
            if not isinstance(value, dict):
                # Its data - should be JSON
                value = self.transport().loads(value)  # Will throw exception if it isn't JSON
            if "encrypted" in value:
                raise EncryptionException("Should have been decrypted in p_fetch")
            self._setproperties(value)

    def _match(self, key, val):
        if key[0] == '.':
            return (key == '.instance' and isinstance(self, val))
        else:
            return (val == self.__dict__[key])

    def match(self, dict):
        """
        Checks if a object matches for each key:value pair in the dictionary.
        Any key starting with "." is treated specially esp:
        .instanceof: class: Checks if this is a instance of the class
        other fields will be supported here, any unsupported field results in a false.

        :returns: boolean, true if matches
        """
        return all([self._match(k, dict[k]) for k in dict])


    @classmethod
    def p_fetch(cls, url, verbose):
        """
        Fetches the object from Dweb, passes to p_decrypt in case it needs decrypting,
        and creates an object of the appropriate class and passes data to _setdata
        This should not need subclassing, (subclass _setdata or p_decrypt instead).

        :return: New object - e.g. StructuredBlock or MutableBlock
        :catch: TransportError - can probably, or should throw TransportError if transport fails
        :throws: TransportError if url invalid, Authentication Error
        """
        from letter2class.py import LetterToClass
        if verbose: print "SmartDict.p_fetch", url;
        data = super(SmartDict, cls).p_fetch(url, verbose) #Fetch the data Throws TransportError immediately if url invalid, expect it to catch if Transport fails
        data = Dweb.transport(url).loads(data)          # Parse JSON //TODO-REL3 maybe function in Transportable
        table = data.table                              # Find the class it belongs to
        cls = LetterToClass[table]             # Gets class name, then looks up in Dweb - avoids dependency
        if not cls:
            raise ToBeImplementedException("SmartDict.p_fetch: "+table+" isnt implemented in table2class")
        if not isinstance(Dweb.table2class[table], cls):
            raise ForbiddenException("Avoiding data driven hacks to other classes - seeing "+table);
        data = cls.p_decrypt(data, verbose)             # decrypt - may return string or obj , note it can be suclassed for different encryption
        data["_url"] = url;                             # Save where we got it - preempts a store - must do this afer decrypt
        return cls(data)

    @classmethod
    def p_decrypt(data, verbose):
        """
         This is a hook to an upper layer for decrypting data, if the layer isn't there then the data wont be decrypted.
         Chain is SD.p_fetch > SD.p_decryptdata > ACL|KC.decrypt, then SD.setdata

         :param data: possibly encrypted object produced from json stored on Dweb
         :return: same object if not encrypted, or decrypted version
         """
        return AccessControlList.decryptdata(data, verbose)

    def dumps(self):    # Called by json_default, but preflight() is used in most scenarios rather than this
        1/0 # DOnt believe this is used
        return {k: self.__dict__[k] for k in self.__dict__ if k[0] != "_"}  # Serialize the dict, excluding _xyz

    def copy(self):
        return self.__class__(self.__dict__.copy())
