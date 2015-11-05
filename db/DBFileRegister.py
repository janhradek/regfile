##
## DBFileRegister.py
##      - Provides methods that query, store and update DBFile()s in the
##        database.
##


# import of required modules {{{
import re

from .DBFile import DBFile
from .DBFileQueryArguments import DBFileQueryArguments
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
    def query(cls, session, dbFileQueryArguments = None, **kwargs):
        # DOC {{{
        """Returns a list of all DBFile()s matching the specified
        DBFileQueryArguments() or None if no such DBFile()s were found. Any
        surplus keyword arguments are added to the DBFileQueryArguments() or
        used to build it if it was not specified.

        Parameters

            session -- an instance of SQLAlchemy's Session()

            dbFileQueryArguments -- (optional) an instance of
                DBFileQueryArguments()

            **kwargs -- any surplus keyword arguments are added to the
                specified DBFileQueryArguments() or used to build a new one.
        """
        # }}}

        # CODE {{{
        # build the SQLAlchemy's Query() from the specified DBFileQueryArguments() in the Session()
        query = cls._buildQuery(session, dbFileQueryArguments, **kwargs)

        # retrieve all DBFile()s matching the query from the database as a list
        dbFiles = query.all()

        # return the resulting list of DBFile()s if there are any {{{
        if (dbFiles):
            return dbFiles
        # }}}
        # otherwise return None {{{
        else:
            return None
        # }}}
        # }}}


    @classmethod
    def queryFirst(cls, session, dbFileQueryArguments = None, **kwargs):
        # DOC {{{
        """Returns the first DBFile() matching the specified
        DBFileQueryArguments() or None if no such DBFile() was found. Any
        surplus keyword arguments are added to the DBFileQueryArguments() or
        used to build it if it was not specified.

        Parameters

            session -- an instance of SQLAlchemy's Session()

            dbFileQueryArguments -- (optional) an instance of
                DBFileQueryArguments()

            **kwargs -- any surplus keyword arguments are added to the
                specified DBFileQueryArguments() or used to build a new one.
        """
        # }}}

        # CODE {{{
        # build the SQLAlchemy's Query() from the specified DBFileQueryArguments() in the Session()
        query = cls._buildQuery(session, dbFileQueryArguments, **kwargs)

        # retrieve and return the first DBFile() matching the query from the
        # database as a list or None if no such DBFile() was found
        return query.first()
        # }}}


    @classmethod
    def queryExists(cls, session, dbFileQueryArguments = None, **kwargs):
        # DOC {{{
        """Returns True if there is at least one DBFile() matching the specified
        DBFileQueryArguments(), False otherwise. Any surplus keyword arguments
        are added to the DBFileQueryArguments() or used to build it if it was
        not specified.

        Parameters

            session -- an instance of SQLAlchemy's Session()

            dbFileQueryArguments -- (optional) an instance of
                DBFileQueryArguments()

            **kwargs -- any surplus keyword arguments are added to the
                specified DBFileQueryArguments() or used to build a new one.
        """
        # }}}

        # CODE {{{
        # return True if there is at least one matching DBFile(), False otherwise
        return (cls.queryFirst(session, dbFileQueryArguments, **kwargs) is not None)
        # }}}


    @staticmethod
    def _buildQuery(session, dbFileQueryArguments = None, **kwargs):
        # DOC {{{
        """Builds a query from the specified DBFileQueryArguments() in the
        provided session. Any surplus keyword arguments are added to the
        DBFileQueryArguments() or used to build it if it was not specified.

        Parameters

            session -- an instance of SQLAlchemy's Session()

            dbFileQueryArguments -- (optional) an instance of
                DBFileQueryArguments()

            **kwargs -- any surplus keyword arguments are added to the
                specified DBFileQueryArguments() or used to build a new one.
        """
        # }}}

        # CODE {{{
        # create a new query ordered by DBFile().fileId in the specified session
        query = session.query(DBFile).order_by(DBFile.fileId)

        # create a new DBFileQueryArguments() using the surplus arguments or
        # return the query as it is now if no DBFileQueryArguments() were specified {{{
        if (dbFileQueryArguments is None):
            # build a new DBFileQueryArguments() if there are any surplus arguments {{{
            if (kwargs):
                dbFileQueryArguments = DBFileQueryArguments(**kwargs)
            # }}}
            # otherwise return the query as it is {{{
            else:
                return query
            # }}}
        # }}}
        # otherwise add any surplus arguments to the specified DBFileQueryArguments() if there are any {{{
        elif (kwargs):
            # add the surplus arguments to the specified DBFileQueryArguments() {{{
            for attributeName, attributeValue in kwargs.items():
                # check that the attribute exists in dbFileQueryArguments (raises AttributeError)
                getattr(dbFileQueryArguments, attributeName)

                # set the value to the attribute
                setattr(dbFileQueryArguments, attributeName, attributeValue)
            # }}}
        # }}}

        # get the method to check whether the value is defined for convenience
        isDefined = DBFileQueryArguments.isDefined

        # add an equality filter over fileId if the corresponding query argument is defined {{{
        if (isDefined(dbFileQueryArguments.fileId)):
            query = query.filter(DBFile.fileId == dbFileQueryArguments.fileId)
        # }}}

        # add a 'like' filter over fileName if the corresponding query argument is defined {{{
        if (isDefined(dbFileQueryArguments.fileName)):
            query = query.filter(DBFile.fileName.ilike(DBFileRegister._likelizeString(dbFileQueryArguments.fileName)))
        # }}}

        # add a 'like' filter over group if the corresponding query argument is defined {{{
        if (isDefined(dbFileQueryArguments.group)):
            query = query.filter(DBFile.group.ilike(DBFileRegister._likelizeString(dbFileQueryArguments.group)))
        # }}}

        # add a 'like' filter over comment if the corresponding query argument is defined {{{
        if (isDefined(dbFileQueryArguments.comment)):
            query = query.filter(DBFile.comment.ilike(DBFileRegister._likelizeString(dbFileQueryArguments.comment)))
        # }}}

        # add an equality filter over fileSize if the corresponding query argument is defined {{{
        if (isDefined(dbFileQueryArguments.fileSize)):
            query = query.filter(DBFile.fileSize == dbFileQueryArguments.fileSize)
        # }}}

        # add an equality filter over MD5 sum of the first megabyte (md1) if the corresponding query argument is defined {{{
        if (isDefined(dbFileQueryArguments.md1)):
            query = query.filter(DBFile.md1 == dbFileQueryArguments.md1)
        # }}}

        # add an equality filter over MD5 sum if the corresponding query argument is defined {{{
        if (isDefined(dbFileQueryArguments.md5)):
            query = query.filter(DBFile.md5 == dbFileQueryArguments.md5)
        # }}}

        # add an equality filter over ED2K sum if the corresponding query argument is defined {{{
        if (isDefined(dbFileQueryArguments.ed2k)):
            query = query.filter(DBFile.ed2k == dbFileQueryArguments.ed2k)
        # }}}

        # return the prepared query
        return query
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


    @classmethod
    def update(cls, session, dbf, setall=False):
        # DOC {{{
        """Updates a DBFile() persisted in the database specified by the given
        DBFile()'s fileId with the properties from the specified DBFile().
        Only filename, group and comment are updated. Returns True if the
        update was successfull, returns False if the record doesnt exists or
        nothing was set.
        """
        # }}}

        # CODE {{{
        persistedDBFile = cls.queryFirst(
                session = session,
                fileId  = dbf.fileId,
        )

        if (persistedDBFile is None):
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
