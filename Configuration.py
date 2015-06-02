##
## Configuration.py
##      - Implements the handling of the configuration.
##


# import of required modules {{{
import configparser
import os.path
# }}}


# class Configuration() {{{
class Configuration(object):
    # DOC {{{
    """Implements the handling of the configuration.
    """
    # }}}


    # STATIC VARIABLES {{{
    # the section where regfile's configuration is stored in the configparser
    REGFILE_SECTION         = "regfile"

    # the default location of the configuration
    DEFAULT_PATH            = os.path.expanduser("~/.regfile")

    # the default configuration {{{
    DEFAULT_CONFIGURATION   = {
        "db"            : "~/dbfile.sqlite",    # location of the database
        "log"           : "~/dbfile.log",       # location of the logfile
        "commit"        : "auto",               # other values may be: confirm, problem
        "pathtemplates" : "",                   # path templates configuration array
    }
    # }}}

    # commit values {{{
    # auto - always commit all the changes immediately
    COMMIT_AUTO             = "auto"

    # confirm - always confirm any changes to be commited
    COMMIT_CONFIRM          = "confirm"

    # problem - confirm changes only in case of a problem
    COMMIT_PROBLEM          = "problem"
    # }}}

    # a tuple of all supported values of commit {{{
    SUPPORTED_COMMIT_VALUES = (
            COMMIT_AUTO,
            COMMIT_CONFIRM,
            COMMIT_PROBLEM,
    )
    # }}}
    # }}}


    # METHODS {{{
    def __init__(self, path=DEFAULT_PATH):
        # DOC {{{
        """Initializes the instance of Configuration. Reads and sanitizes the
        configuration from the file  specified, but if the file does not exists
        a new one with the default configuration is created.

        Parameters

            path -- (optional) the location of the configuration
                file
        """
        # }}}

        # CODE {{{
        # the location of the configuration file
        self.path                                   = path

        # the configuration parser / configuration itself
        self.parser                                 = configparser.ConfigParser()

        # set the default configuration
        self.parser[Configuration.REGFILE_SECTION]  = Configuration.DEFAULT_CONFIGURATION

        # read the configuration from the file or write the default configuration
        self._readFromFile()
        # }}}

    def _readFromFile(self):
        # DOC {{{
        """Reads the configuration from the file or writes the default
        configuration if the file does not exist.
        """
        # }}}

        # CODE {{{
        # create a default config if the configuration file does not exist {{{
        if (not os.path.exists(self.path)):
            # open the file and save the default configuration {{{
            with open(self.path, 'w') as configurationFile:
                self.parser.write(configurationFile)
            # }}}

            # mark that this is the default configuration
            self["default"] = "True"
        # }}}
        # otherwise read the configuration {{{
        else:
            # check that the configuration location is a file
            assert (os.path.isfile(self.path))

            # read the configuration
            self.parser.read(self.path)

            # mark that this is not the default configuration
            self["default"] = "False"
        # }}}

        # sanitize and check the values
        self._sanitizeAndCheck()
        # }}


    def _sanitizeAndCheck(self):
        # DOC {{{
        """Sanitizes and checks the configuration values.
        """
        # }}}

        # CODE {{{
        # expand the user's path of the database file
        self["db"]     = os.path.expanduser(self["db"])

        # expand the user's path of the log file
        self["log"]    = os.path.expanduser(self["log"])

        # normalize the value of the commit configuration
        self["commit"] = self["commit"].strip().lower()

        # check that the commit value is supported {{{
        if (self["commit"] not in Configuration.SUPPORTED_COMMIT_VALUES):
            raise ValueError("Unknown entry commit={} in config {}".format(self["commit"], self.path))
        # }}}
        # }}}


    def __getitem__(self, key):
        # DOC {{{
        """Item getter for getting a value from the configuration.

        Parameters

            key -- the key of the value to return
        """
        # }}}

        # CODE {{{
        return self.parser[Configuration.REGFILE_SECTION][key]
        # }}}


    def __setitem__(self, key, value):
        # DOC {{{
        """Item setter for storing a value in the configuration.

        Parameters

            key -- the key of the value to set

            value -- the value
        """
        # }}}

        # CODE {{{
        self.parser[Configuration.REGFILE_SECTION][key] = value
        # }}}


    def __getattr__(self, name):
        # DOC {{{
        """Relays queries for any unknown attributes to the configuration
        parser.

        Parameters

            name -- name of the parameter
        """
        # }}}

        # CODE {{{
        return getattr(self.parser[Configuration.REGFILE_SECTION], name)
        # }}}



    # }}}
# }}}
