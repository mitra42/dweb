from pathlib2 import Path, PosixPath
from datetime import datetime
from Block import Block
from StructuredBlock import StructuredBlock
#import magic
#from mimetypes import MimeTypes
import mimetypes
mimetypes.init()
mimetypes.add_type('text/plain','.md')
from Dweb import Dweb
#TODO-BACKPORT - review this file

class File(StructuredBlock):
    """
    A Subclass of File that specifically deals with file system objects,
    """
    maxcontentlen = 10000

    def __init__(self, content=None, **options):
        """

        :param dict {filepath}
        """
        super(File, self).__init__(**options)
        self.data = content     # Done this way because subclass (StructuredBlock->SmartDict) uses "data" to set _data i.e. would be fine if this was json for the SB.

    @staticmethod
    def _write(filepath, data):
        if filepath:
            with open(filepath, 'wb') as f:
                f.write(data)

    @staticmethod
    def _content(filepath):
        p = filepath if isinstance(filepath, (Path,)) else Path(filepath)
        with p.open(mode='rb') as file:  # b is important -> binary
            return file.read()

    @classmethod
    def _uploadbinary(cls, content, meta, verbose=False):
        """
        Upload content as a binary

        :param content: Content of the file
        :param meta:    Any meta data about the file e.g. contentype or date
        :param verbose:
        :return:        File() with _url and data set
        """
        # Utility method to upload binary content as a Block and attach.
        url = Dweb.transport.rawstore(data=content, verbose=verbose)
        f = cls(**meta)
        f.url = url
        f.store(verbose=verbose)  # This will have data and _url, the _url reflects the SB not the data
        return f

    @classmethod
    def load(cls, filepath=None, contenttype=None, upload=False, verbose=False, **options):
        """
        Load from a file, and return a File
        images are stored as separate blocks.

        :param filepath:
        :param contenttype: Appropriate for Content-type header e.g. image/png
        :param dict:    Metadata - especially Content-type
        :param upload:  Set to True to send to transport
        :param options:
        :return:
        """
        if verbose: print "File.load:",filepath
        p = filepath if isinstance(filepath, (Path,)) else Path(filepath)
        content = cls._content(p)
        if not contenttype:
        #mime= magic.Magic(mime=True) would be better, but doesnt work on Macs if libmagic not installed (it isnt be default)
            #print mime.from_file(filepath)
            contenttype, encoding_unused = mimetypes.guess_type(unicode(filepath))
        meta = {"Content-type": contenttype,
                "name": p.name,
                "date": datetime.fromtimestamp(p.stat().st_mtime),
                "size": len(content)
                }
        if contenttype is None or "image" in contenttype or len(content)>cls.maxcontentlen or \
            ("application" in contenttype and "json" not in contenttype):   # e.g. .eot; .ttf, .woff
            if upload:
                f = cls._uploadbinary(content, meta, verbose=verbose)
            else:
                f = cls(content=content, **meta)   # Note this may never be uploadable, as data may not be serialisable
        else:
            f = cls(content=content, **meta) # File, the ** is because can't pass hyphenated fields as arguments
            if upload:
                try:
                    f.store(verbose=verbose)  # This will have data and _url, the _url reflects the SB not the data
                except UnicodeDecodeError as e:
                    print "XXX@82 failed unicode on",filepath,"contenttype=",contenttype
                    f = cls._uploadbinary(content, meta, verbose=verbose)
        return f


class Dir(File):

    @classmethod
    def load(cls, filepath=None, upload=False, verbose=False, **options):
        """
        Load (optionally upload) an entire directory (recursively), return a SB with a set of links.

        :param filepath:    To Directory, no trailing slash
        :param upload:      True to send out, (Note there is currently no easy way to upload AFTER doing a load with upload=False
        :param verbose:
        :param options:
        :return:
        """
        if verbose: print "Dir.load:",filepath
        pp = filepath if isinstance(filepath, (Path,)) else Path(filepath)
        f = File(data={         # Passed as data so will be loaded by StructuredBlock->SmartDict into dict
            "name": pp.name,
            "date": datetime.fromtimestamp(pp.stat().st_mtime),
            "links": []
        }) # Create a File for an empty directory
        for p in pp.iterdir():
            if p.name not in (".DS_Store",):    # Silently ignore filler OS files
                if p.is_file():
                    # Upload a file
                    child = File.load(filepath=p, upload=upload, verbose=verbose, **options)  # TODO need contenttype to pass, should use well known table
                    f.links.append(child)       # Alt "data"
                elif p.is_dir():
                    child = Dir.load(filepath=p, upload=upload, verbose=verbose, **options)    # Recurse
                    f.links.append(child)       # Alt "data"
                else:
                    print "TODO not a file or a directory:", p
        if upload:
            f.store(verbose=verbose, **options)
        return f
