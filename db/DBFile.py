##
## DBFile.py
##      - SQLAlchemy ORM object representing a row in the "file" table.
##


# import of required modules {{{
import sqlalchemy

from .DBBase import DBBase
# }}}


# class DBFile() {{{
class DBFile(DBBase):
    # DOC {{{
    """SQLAlchemy ORM object representing a row in the "file" table.
    """
    # }}}


    # STATIC VARIABLES {{{
    # SQLAlchemy table name
    __tablename__ = "file"

    # SQLAlchemy columns {{{
    # id (primary key)
    fileId          = sqlalchemy.Column(name = 'idno', type_ = sqlalchemy.Integer, primary_key = True)

    # filename
    fileName        = sqlalchemy.Column(name = 'name', type_ = sqlalchemy.String)

    # group
    group           = sqlalchemy.Column(type_ = sqlalchemy.String)

    # comment
    comment         = sqlalchemy.Column(type_ = sqlalchemy.String)

    # size in bytes
    fileSize        = sqlalchemy.Column(name = 'size', type_ = sqlalchemy.Integer)

    # MD5 of the first megabyte
    md1             = sqlalchemy.Column(type_ = sqlalchemy.String)

    # MD5 of the whole file
    md5             = sqlalchemy.Column(type_ = sqlalchemy.String)

    # ED2K checksum
    ed2k            = sqlalchemy.Column(type_ = sqlalchemy.String)
    # }}}
    # }}}


    # METHODS {{{
    def __init__(self, fileId=None, fileName=None, group=None, comment=None,
                 fileSize=None, md1=None, md5=None, ed2k=None):
        # DOC {{{
        """Initializes the instance of the ORM representation of registered
        file.

        Parameters

            fileId -- (optional) the ID (primary key) of the file in the DB

            fileName -- (optional) the name of the file

            group -- (optional) the group of the file

            comment -- (optional) the comment of the file

            fileSize -- (optional) the integer size of the file

            md1 -- (optional) the MD5 of the first megabyte of the file

            md5 -- (optional) the MD5 of the entire file

            ed2k -- (optional) the ED2K sum of the entire file
        """
        # }}}

        # CODE {{{
        # sanitize empty id (to be None rather than zero or empty string)
        # and therefore will be determined by the SQLAlchemy/SQLite {{{
        if (not fileId):
            fileId = None
        # }}}

        # save the parameters {{{
        self.fileId         = fileId
        self.fileName       = fileName
        self.group          = group
        self.comment        = comment
        self.fileSize       = fileSize
        self.md1            = md1
        self.md5            = md5
        self.ed2k           = ed2k
        # }}}
        # }}}


    # }}}
# }}}
