from Block import Block
from StructuredBlock import StructuredBlock

class File(StructuredBlock):

    def __init__(self, dict=None, **options):
        """

        :param dict {filepath}
        """
        super(File, self).__init__(dict, **options)

    @staticmethod
    def _content(filepath):
        with open(filepath, mode='rb') as file:  # b is important -> binary
            return file.read()

    @classmethod
    def load(cls, filepath=None, **options):
        """
        Utility function to load a File from a path

        :param filepath:
        """
        f = cls({"filepath": filepath}, **options)
        f.data = cls._content(filepath)
        return f

    @classmethod
    def upload(cls, filepath=None, contenttype=None, verbose=False, **options):
        """
        Upload a file, and return a File.
        images are stored as separate blocks.

        :param filepath:
        :oaram contenttype: Appropriate for Content-type header e.g. image/png
        :param dict:    Metadata - especially Content-type
        :param options:
        :return:
        """
        content = cls._content(filepath)
        if "image" in contenttype:
            b = Block(data=content)  # Store raw
            hash = b.store(verbose=verbose)
            f = cls(hash=hash, **{"Content-type": contenttype})    # File, the ** is because can't pass hyphenated fields as arguments
            f.store(verbose=verbose)  # This will have data and _hash, the _hash reflects the SB not the data
        else:
            f = StructuredBlock(data=content, **{"Content-type": contenttype}) # File, the ** is because can't pass hyphenated fields as arguments
            f.store(verbose=verbose)  # This will have data and _hash, the _hash reflects the SB not the data
        return f
