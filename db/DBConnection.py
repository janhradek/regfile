##
## DBConnection.py
##      - Manages the connection to the SQLite database and provides means to
##        create a new session and to get a runtime context friendly session
##        wrapper.
##


# import of required modules {{{
import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# }}}


# class DBConnection() {{{
class DBConnection(object):
    # DOC {{{
    """Manages the connection to the SQLite database and provides means to
    create a new session and to get a runtime context friendly session wrapper.
    """
    # }}}


    # METHODS {{{
    def __init__(self, sqliteFilePath, echoSQLCommands = False):
        # DOC {{{
        """Initializes the instance, creates the engine and session maker and
        creates the database structure if the SQLite file does not exists.

        Parameters

            sqliteFilePath -- path of the SQLite database file

            echoSQLCommands -- whether or not to print any issued SQL commands
        """
        # }}}

        # CODE {{{
        # expand '~' to the home directory of the current user in the SQLite file path
        self._sqliteFilePath = os.path.expanduser(sqliteFilePath)

        # create the database engine
        self._engine = create_engine('sqlite:///' + self._sqliteFilePath, echo = echoSQLCommands)

        # create and bind the session maker
        self._sessionMaker = sessionmaker(bind=self._engine)

        # create the database schema if necessary
        self._createDBSchemaIfNecessary()
        # }}}


    def _createDBSchemaIfNecessary(self):
        # DOC {{{
        """Creates the underlying database schema if the SQLite database file
        does not exist.
        """
        # }}}

        # CODE {{{
        # return if the SQLite database file exists {{{
        if (os.path.exists(self._sqliteFilePath)):
            return
        # }}}

        # import the DBBase declarative base
        from .DBBase import DBBase

        # import the DBFile to introduce it to the declarative base
        from .DBFile import DBFile              # pylint: disable=unused-variable

        # create the schema (i.e. the SQLite file)
        DBBase.metadata.create_all(self._engine)
        # }}}


    @property
    def isConnected(self):
        # DOC {{{
        """Returns True if the DBConnection() is connected to the database, False
        otherwise.
        """
        # }}}

        # CODE {{{
        return (self._sessionMaker is not None)
        # }}}


    def close(self):
        # DOC {{{
        """Closes all opened connections and sessions, disposes of the engine
        and the session maker.
        """
        # }}}

        # CODE {{{
        # return if the connection is not open {{{
        if (not self.isConnected):
            return
        # }}}

        # close all sessions
        self._sessionMaker.close_all()

        # delete the session maker
        self._sessionMaker = None

        # reinitialize engine's connection pool effectively closing all checked-in connections
        self._engine.dispose()

        # delete the engine
        self._engine = None
        # }}}


    def __del__(self):
        # DOC {{{
        """Gracefuly closes all connections and sessions and disposes of the
        engine.
        """
        # }}}

        # CODE {{{
        self.close()
        # }}}


    def getNewSession(self):
        # DOC {{{
        """Creates a new session and returns it.
        """
        # }}}

        # CODE {{{
        return (self._sessionMaker())
        # }}}


    @contextmanager
    def getSessionContext(self):
        # DOC {{{
        """Context manager that creates a new session, yields it for the
        runtime context ('with' statement) and closes it when the context ends.
        """
        # }}}

        # CODE {{{
        # get a new session
        session = self.getNewSession()

        # yield the session for the 'with' statement, runtime context starts here
        yield session

        # always close the session on return from the runtime context no matter
        # what happened in the runtime context
        session.close()
        # }}}


    # }}}
# }}}
