##
## DBFileRegister.py
##      - Provides methods that query, store and update DBFile()s in the
##        database.
##


# import of required modules {{{
import re

from .DBFile import DBFile
# }}}


# class DBFileRegister() {{{
class DBFileRegister(object):
    # DOC {{{
    """Provides methods that query, store and update DBFile()s in the
    database.
    """
    # }}}


    # STATIC VARIABLES {{{
    # a compiled regular expression that matches the begining, the end, all spaces and
    # percent signs of a string to replace these parts of that string with a single percent sign
    _LIKELIZE_VALUE_RE           = re.compile(r'(%|^|$|\s)+')
    # }}}


    # METHODS {{{
    @classmethod
    def queryinfo(cls, session, dbf):
        # DOC {{{
        """Returns all records mathing the specified dbf info properties
        (fileId, fileName, group and comment). Properties set to None will be
        ignored.
        """
        # }}}

        # CODE {{{
        query = session.query(DBFile).order_by(DBFile.fileId)

        if (dbf.fileId is not None):
            query = query.filter(DBFile.fileId == dbf.fileId)
        if (dbf.fileName):
            query = query.filter(DBFile.fileName.ilike(cls._likelizeString(dbf.fileName)))
        if (dbf.group):
            query = query.filter(DBFile.group.ilike(cls._likelizeString(dbf.group)))
        if (dbf.comment):
            query = query.filter(DBFile.comment.ilike(cls._likelizeString(dbf.comment)))

        dbFiles = query.all()
        if (len(dbFiles) == 0):
            return None
        return dbFiles
        # }}}


    @staticmethod
    def querydata(session, dbf, quick=False):
        # DOC {{{
        """Returns all records mathing the specified dbf data properties
        (fileSize, md1, md5, ed2k). If quick is True only fileSize and md1 is
        queried. Properties set to None will be ignored.
        """
        # }}}

        # CODE {{{
        query = session.query(DBFile).order_by(DBFile.fileId)
        query = query.filter(DBFile.fileSize == dbf.fileSize)
        query = query.filter(DBFile.md1 == dbf.md1)
        if not quick:
            query = query.filter(DBFile.md5 == dbf.md5)
            query = query.filter(DBFile.ed2k == dbf.ed2k)

        dbFiles = query.all()
        if (len(dbFiles) == 0):
            return None
        return dbFiles
        # }}}


    @staticmethod
    def _likelizeString(value):
        # DOC {{{
        """Replaces spaces in the specified string with a percent sign (%) and
        also puts the percent sign at the begining and at the end of the
        string, so the resulting string would match any string containing the
        words in the original string in SQL. E.g. "hello world" ->
        "%hello%world%"

        Parameters

            value -- a string to likelize
        """
        # }}}

        # CODE {{{
        return DBFileRegister._LIKELIZE_VALUE_RE.sub("%", value)
        # }}}


    @staticmethod
    def insert(session, *dbfs, commit=True):
        # DOC {{{
        """Inserts the specified DBFile()s  into the database. The session is
        commited after the insert if commit is True.
        """
        # }}}

        # CODE {{{
        if not dbfs:
            raise ValueError("No DBFiles() specified!")

        for dbf in dbfs:
            session.add(dbf)
            session.flush()     # this will refresh the fileId

        if commit:
            session.commit()
        # }}}


    @staticmethod
    def update(session, dbf, setall=False):
        # DOC {{{
        """Updates a DBFile() persisted in the database specified by the given
        DBFile()'s fileId with the properties from the specified DBFile().
        Only filename, group and comment are updated. Returns True if the
        update was successfull, returns False if the record doesnt exists or
        nothing was set.
        """
        # }}}

        # CODE {{{
        query = session.query(DBFile).filter(DBFile.fileId == dbf.fileId)

        persistedDBFile = None
        try:
            persistedDBFile = query.one()
        except:
            return None

        changed = False

        if dbf.fileName or setall:
            persistedDBFile.fileName = dbf.fileName if dbf.fileName != "" else None
            changed = True

        if dbf.group or setall:
            persistedDBFile.group = dbf.group if dbf.group != "" else None
            changed = True

        if dbf.comment or setall:
            persistedDBFile.comment = dbf.comment if dbf.comment != "" else None
            changed = True

        if changed:
            # add the (persisted and) changed DBFile() to the session (unnecessary but clear)
            session.add(persistedDBFile)

            # emit the SQL immediately since the DBFile will be expunged (read removed) from the session
            session.flush()

            # remove the instance from the session so attributes will not expire and would not need to be refreshed
            session.expunge(persistedDBFile)

            # commit the session
            session.commit()

            # NOTE: another approach to the add-flush-expunge-commit would be
            # NOTE: to add-commit-refresh but:
            # NOTE:   1) anything can happen between commit and refresh,
            # NOTE:      notably another client may change the entity
            # NOTE:   2) an SQL is issued to refresh the entity's attributes
            # NOTE:      which is IMO 'expensive' and unnecessary
            # NOTE: Rollback is OK, SQLAlchemy would just do rollback to undo
            # NOTE: the changes.
        else:
            return None

        return persistedDBFile
        # }}}


    # }}}
# }}}
