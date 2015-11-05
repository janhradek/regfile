##
## DBFileQueryArguments.py
##      - Provides storage for filter values of queries about DBFile()s.
##


# class DBFileQueryArguments() {{{
class DBFileQueryArguments(object):
    # DOC {{{
    """Provides storage for filter values of queries about DBFile()s.
    """
    # }}}


    # STATIC VARIABLES {{{
    # prevent assignment/creation of any other instance attributes than those listed
    __slots__   = [ 'fileId', 'fileName', 'group', 'comment', 'fileSize', 'md1', 'md5', 'ed2k',]

    # sentinel representing undefined value (to allow e.g. None and empty strings as valid values)
    _UNDEFINED  = object()
    # }}}


    # METHODS {{{
    def __init__(self, fileId = _UNDEFINED, fileName = _UNDEFINED,
                 group = _UNDEFINED, comment = _UNDEFINED,
                 fileSize = _UNDEFINED, md1 = _UNDEFINED, md5 = _UNDEFINED,
                 ed2k = _UNDEFINED):
        # DOC {{{
        """Initializes the instance, stores the parameters.

        Parameters

            fileId -- (optional) the identification of a DBFile() to match as
                is

            fileName -- (optional) the file name of a DBFile() to match in
                'like' fashion

            group -- (optional) the group of a DBFile() to matchin 'like'
                fashion

            comment -- (optional) the comment of a DBFile() to matchin 'like'
                fashion

            fileSize -- (optional) the size of a file  of a DBFile() to match
                as is

            md1 -- (optional) the MD5 sum of the first megabyte of a DBFile()
                to match as is

            md5 -- (optional) the MD5 sum of the entire file of a DBFile() to
                match as is

            ed2k -- (optional) the ED2K sum of the entire file of a DBFile() to
                match as is

        """
        # }}}

        # CODE {{{
        # NOTE: see also __slots__
        self.fileId     = fileId
        self.fileName   = fileName
        self.group      = group
        self.comment    = comment
        self.fileSize   = fileSize
        self.md1        = md1
        self.md5        = md5
        self.ed2k       = ed2k
        # }}}


    @classmethod
    def isDefined(cls, value):
        # DOC {{{
        """Returns True if the specified value is defined in the sense that it
        does not have the 'undefined' sentinel's value.

        Parameters

            value -- a value to check
        """
        # }}}

        # CODE {{{
        return (value is not cls._UNDEFINED)
        # }}}


    # }}}
# }}}
