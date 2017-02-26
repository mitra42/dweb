# encoding: utf-8
from datetime import datetime

class MyBaseException(Exception):
    """
    Base class for Exceptions

    msgargs Arguments that slot into msg
    __str__ Returns msg expanded with msgparms
    """
    errno=0
    httperror = 500
    msg="Generic Model Exception"   #: Parameterised string for message
    def __init__(self, **kwargs):
        self.msgargs=kwargs # Store arbitrary dict of message args (can be used ot output msg from template

    def __str__(self):
        try:
            return self.msg.format(**self.msgargs)
        except:
            return self.msg+" "+unicode(self.msgargs)


class ToBeImplementedException(MyBaseException):
    """
    Raised when some code has not been implemented yet
    """
    httperror = 501
    msg = "{name} needs implementing"

def filecontent(filename):
    """
    Utility function to open, read and close a file

    :param filename:
    :return: contents of file
    """
    with open(filename, mode='rb') as file:  # b is important -> binary
        content = file.read()
    return content

