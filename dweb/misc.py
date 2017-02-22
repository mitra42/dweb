# encoding: utf-8
from datetime import datetime

class MyBaseException(Exception):
    """
    Base class for Exceptions
    errno   Number of error,
    msg     Parameterised string for message
    msgargs Arguments that slot into msg
    __str__ Returns msg expanded with msgparms
    """
    errno=0
    msg="Generic Model Exception"
    def __init__(self, **kwargs):
        self.msgargs=kwargs # Store arbitrary dict of message args (can be used ot output msg from template

    def __str__(self):
        try:
            return self.msg.format(**self.msgargs)
        except:
            return self.msg+" "+unicode(self.msgargs)

class ToBeImplementedException(MyBaseException):
    msg = "{name} needs implementing"


def json_default(obj):
    """
    Default JSON serialiser especially for handling datetime
    :param obj: Anything json dumps can't serialize
    :return: string for extended types
    """
    if isinstance(obj, (datetime,)):    # Using isinstance rather than hasattr because __getattr__ always returns true
    #if hasattr(obj,"isoformat"):  # Especially for datetime
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % obj.__class__.__name__)