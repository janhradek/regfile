##
## ConfigurationBase.py
##      ConfigurationBase() - Maintains configuration. It is set up using a
##          collection of ConfigurationOption()s.
##      ConfigurationOption() - Represents a configuration option specified by
##          the configuration section, the option's name (key in configparser's
##          terminology) and optionaly the default value. It also provides an
##          optional facility to check the configuration option's value.
##      ConfigurationUtils - Static utility methods for ConfigurationBase() and
##          its subclasses. It contains mostly helper methods for sanitizing
##          and checking configuration values.
##      ConfigurationError() - Raised in case of any problem with the
##          configuration or configuration's options. Options' sanitizing and
##          checking functions should raise this exception in case of any
##          problem.
##


# import of required modules {{{
import configparser
import os.path
# }}}


# class ConfigurationBase() {{{
class ConfigurationBase(object):
    # DOC {{{
    """Maintains configuration. It is set up using a collection of
    ConfigurationOption()s.
    """
    # }}}


    # STATIC VARIABLES {{{
    # bitwise restrictions {{{
    # no restriction on any option
    RESTRICT_NOTHING        = 0x00

    # no unknown surplus values are allowed
    RESTRICT_SURPLUS        = 0x01

    # no missing values are allowed
    RESTRICT_MISSING        = 0x02

    # values must be specified in a way that sanitizing them does not change them
    RESTRICT_SANE_VALUES    = 0x04
    # }}}

    # an alias for all restrictions
    RESTRICT_ALL        = (RESTRICT_SURPLUS | RESTRICT_MISSING | RESTRICT_SANE_VALUES)
    # }}}


    # METHODS {{{
    def __init__(self, *configurationOptions, configurationPath, restrictions = RESTRICT_NOTHING):
        # DOC {{{
        """Initializes the instance, stores the configuration path, read or
        creates the configuration file depending on whether it exists or not.

        Parameters

            *configurationOptions -- all positional arguments are
                ConfigurationOption()s

            configurationPath -- the location of the configuration file

            restrictions -- (optional) a bitwise combination of STRICT_XXX that
                describes how to handle missing, surplus or non-sane values
        """
        # }}}

        # CODE {{{
        # store the configuration path
        self.path = configurationPath

        # check and create a dictionary of all specified configuration options
        self._configurationOptions = self._checkAndMapConfigurationOptions(configurationOptions)

        # create the ConfigParser()
        self._parser = configparser.ConfigParser()

        # a dictionary of sanitized values of existing options by configuration options
        self._sanitizedExistingValuesByOption = {}

        # a dictionary of values of options that were missing and a sanitized
        # default value had to be used by option
        self._sanitizedDefaultValuesByOption = {}

        # a dictionary of values that does not represent a registered option by (a new) option
        self._surplusValuesByOption = {}

        # a mark whether this configuration has been compacted or not
        # NOTE: compacting the configuration deletes the dictionaries of
        # NOTE: sanitized existing, default and surplus values
        self._compacted = False

        # read the configuration from the file or write the default
        # configuration and mark whether or not the configuration originates
        # from the configuration file
        self.fromConfigFile = self._readOrCreateFile(restrictions)
        # }}}


    def _checkAndMapConfigurationOptions(self, configurationOptions):
        # DOC {{{
        """Returns a dictionary of specified configuration options by their
        keys, checked for duplicaties and for being of ConfigurationOption()
        class.

        Parameters

            configurationOptions -- an iterable of ConfigurationOption()s
        """
        # }}}

        # CODE {{{
        # a resulting dictionary of configuration options by their key
        configurationOptionsByKey = {}

        # go over all specified configuration options, check them and add them to the dictionary {{{
        for configurationOption in configurationOptions:
            # check that the configurartion option is an instance of ConfigurationOption()
            assert (isinstance(configurationOption, ConfigurationOption))

            # check that the ConfigurationOption() of that same key is not already stored
            assert (configurationOption.key not in configurationOptionsByKey)

            # add the ConfigurationOption() to the map
            configurationOptionsByKey[configurationOption.key] = configurationOption
        # }}}

        # return the dictionary of configuration options by their key
        return configurationOptionsByKey
        # }}}


    def _readOrCreateFile(self, restrictions):
        # DOC {{{
        """Reads the configuration from the file or writes the default
        configuration in a new one if the file does not exist. Returns True if
        the configuration was read from the config file, False otherwise.

        Parameters

            restrictions -- a bitwise combination of STRICT_XXX that describes
                how to handle missing, surplus or non-sane values
        """
        # }}}

        # CODE {{{
        # determine whether the file exists
        fileExists = os.path.exists(self.path)

        # read the configuration from the file if it exists {{{
        if (fileExists):
            self._readFromFile()
        # }}}

        # replace sentinels with defaults and sanitize and check all values
        self._useDefaultAndSanitizeAndCheckAllValues(restrictions, fileExists)

        # create the configuration file if it does not exist {{{
        if (not fileExists):
            self._createFile()
        # }}}

        # return whether or not the file existed at the begining
        return fileExists
        # }}}


    def _readFromFile(self):
        # DOC {{{
        """Reads the configuration from the file.
        """
        # }}}

        # CODE {{{
        # check that the  configuration file exists
        assert (os.path.exists(self.path))

        # raise an exception if the configuration path is not a file {{{
        if (not os.path.isfile(self.path)):
            raise ConfigurationError("{} is not a file and cannot be read as a configuration!".format(self.path))
        # }}}

        # read the configuration
        self._parser.read(self.path)
        # }}}


    def _useDefaultAndSanitizeAndCheckAllValues(self, restrictions, fileExists):
        # DOC {{{
        """Stores default values for all missing options and sanitizes and
        checks all options.

        Parameters

            restrictions -- a bitwise combination of STRICT_XXX that describes
                how to handle missing, surplus or non-sane values

            fileExists -- if False than missing values restriction is ignored
        """
        # }}}

        # CODE {{{
        # go over all configuration sections and sanitize and check all values in them {{{
        for section in self._parser.sections():
            # go over all configuration options in the section and sanitize and check all values in it {{{
            for name, value in self._parser.items(section):
                # determine the key of the option that would represent this name/value in the section
                optionKey = ConfigurationOption.determineKey(section, name)

                # raise an exception or remember the option for removal if
                # there is no option registered by that key {{{
                if (optionKey not in self._configurationOptions):
                    # raise an exception if strict handling of surplus values is required {{{
                    if ((restrictions & ConfigurationBase.RESTRICT_SURPLUS) != 0):
                        raise ConfigurationError("Unknown configuration option '[{section}].{name} = {value}'!".format(**locals()))
                    # }}}
                    # otherwise remember this surplus value {{{
                    else:
                        self._surplusValuesByOption[ConfigurationOption(section = section, name = name)] = value
                    # }}}
                # }}}

                # get the configuration option associated with this name/value and section
                option = self._configurationOptions[optionKey]

                # sanitize and check the value
                sanitizedValue = option.sanitizeAndCheck(value)

                # raise an exception or remember the sanitized value to store
                # it later if it differs from the original value {{{
                if (sanitizedValue != value):
                    # raise an exception if strict interpretation of values is required {{{
                    if ((restrictions & ConfigurationBase.RESTRICT_SANE_VALUES) != 0):
                        raise ConfigurationError("Configuration option's '[{section}].{name} = {value}' would have to be sanitized to '{sanitizedValue}'!".format(**locals()))
                    # }}}
                    # otherwise remember the sanitized value to set it later {{{
                    else:
                        self._sanitizedExistingValuesByOption[option] = sanitizedValue
                    # }}}
                # }}}
            # }}}
        # }}}

        # find options that do not exist in the parser and sanitize and store their default values {{{
        for option in self._configurationOptions.values():
            # create the section if it does not exist {{{
            if (not self._parser.has_section(option.section)):
                self._parser[option.section] = {}
            # }}}
            # otherwise continue if the option already exists {{{
            elif (self._parser.has_option(option.section, option.name)):
                continue
            # }}}

            # raise an exception if the file exists and strict handling of missing values is required {{{
            if ((fileExists) and (restrictions & ConfigurationBase.RESTRICT_MISSING) != 0):
                raise ConfigurationError("Configuration option '[{0.section}].{0.name}' is missing in the config file!".format(option))
            # }}}

            # sanitize the option's default value
            sanitizedDefaultValue = option.sanitizeAndCheck(option.defaultValue)

            # store the default value in the dictionary by options for reference
            # of what was not specified in the config file and to set it later
            self._sanitizedDefaultValuesByOption[option] = sanitizedDefaultValue
        # }}}

        # remove all surplus options {{{
        for surplusOption in self._surplusValuesByOption:
            self._parser.remove_option(surplusOption.section, surplusOption.name)
        # }}}

        # store the sanitized exitisting values in the parser {{{
        for option, sanitizedValue in self._sanitizedExistingValuesByOption.items():
            self._parser[option.section][option.name] = sanitizedValue
        # }}}

        # store the sanitized default values in the parser {{{
        for option, sanitizedDefaultValue in self._sanitizedDefaultValuesByOption.items():
            self._parser[option.section][option.name] = sanitizedDefaultValue
        # }}}
        # }}}


    def _createFile(self):
        # DOC {{{
        """Writes the current (default) configuration to the file.
        """
        # }}}

        # CODE {{{
        # check that the file does not exist
        assert (not os.path.exists(self.path))

        # open the file and save the default configuration {{{
        with open(self.path, 'w') as configurationFile:
            self._parser.write(configurationFile)
        # }}}
        # }}}


    def makeReportOfIssues(self, compact = True):
        # DOC {{{
        """Returns a tuple in the format (missingOptionsReport,
        surplusOptionsReport, sanitizedOptionsReport,) where each item is
        either None if there are no corresponding options to report or a string
        with a list of options that have the corresponding issue.

        NOTE: If compact == True then the configuration is compacted and this
        method cannot be called again.

        Parameters

            compact -- (optional) if True the configuration is compacted, i.e.
                the dictionaries with missing, surplus and sanitized options
                are deleted.
        """
        # }}}

        # CODE {{{
        # raise an exception if the configuration is already compacted {{{
        if (self._compacted):
            raise ConfigurationError("The configuration is already compacted!")
        # }}}

        # a function to yield sorted and formated options with values {{{
        def formatedSortedOptionsWithValuesGenerator(valuesByOptions, prefix = "    "):
            # DOC {{{
            """Returns a generator of string representations of specified
            values by ConfigurationOption()s, sorted by the options' section
            and name.

            Parameters

                valuesByOptions -- a dictionary of option values by
                    ConfigurationOption()s

                prefix -- (optional) a string to put before each output
            """
            # }}}

            # CODE {{{
            # return a generator of sorted formated options with values {{{
            return (
                prefix + option.formatWithValue(value)
                for option, value in sorted(
                    valuesByOptions.items(),
                    key = lambda option, value: (option.section, option.name,),
                )
            )
            # }}}
            # }}}
        # }}}

        # format missing configuration options with default values if there are any {{{
        if (len(self._sanitizedDefaultValuesByOption) > 0):
            missingOptionsReport = "\n".join(formatedSortedOptionsWithValuesGenerator(
                    valuesByOptions = self._sanitizedDefaultValuesByOption,
            ))
        # }}}
        # otherwise mark that there are no missing options to report {{{
        else:
            missingOptionsReport = None
        # }}}

        # format unknown configuration options with their values if there are any {{{
        if (len(self._surplusValuesByOption) > 0):
            surplusOptionsReport = "\n".join(formatedSortedOptionsWithValuesGenerator(
                    valuesByOptions = self._surplusValuesByOption,
            ))
        # }}}
        # otherwise mark that there are no surplus options to report {{{
        else:
            surplusOptionsReport = None
        # }}}

        # format configuration options that had to be sanitized with those
        # sanitized  values if there are any {{{
        if (len(self._sanitizedExistingValuesByOption) > 0):
            sanitizedOptionsReport = "\n".join(formatedSortedOptionsWithValuesGenerator(
                    valuesByOptions = self._sanitizedExistingValuesByOption,
            ))
        # }}}
        # otherwise mark that there are no sanitized options to report {{{
        else:
            sanitizedOptionsReport = None
        # }}}

        # compact the configuration if requested {{{
        if (compact):
            self.compact()
        # }}}

        # return a tuple in the format (missingOptionsReport, surplusOptionsReport,
        # sanitizedOptionsReport,) where each item is either None or a string with
        # a list of options with the corresponding ssues
        return (missingOptionsReport, surplusOptionsReport, sanitizedOptionsReport,)
        # }}}


    def compact(self):
        # DOC {{{
        """Compacts the configuration by removing dictionaries of surplus,
        missing and sanitized existing values.
        """
        # }}}

        # CODE {{{
        # raise an exception if the configuration is already compacted {{{
        if (self._compacted):
            raise ConfigurationError("The configuration is already compacted!")
        # }}}

        # delete the dictionary of surplus values
        del self._surplusValuesByOption

        # delete the dictionary of sanitized existing values
        del self._sanitizedExistingValuesByOption

        # delete the dictionary of missing values filled with default values
        del self._sanitizedDefaultValuesByOption

        # mark that the configuration was compacted
        self._compacted = True
        # }}}


    def __getitem__(self, key):
        # DOC {{{
        """Returns the value specified by the ConfigurationOption() given as
        key.

        Parameters

            key -- an instance of ConfigurationOption()
        """
        # }}}

        # CODE {{{
        # raise an exception if the specified key is not a ConfigurationOption() {{{
        if (not isinstance(key, ConfigurationOption)):
            raise ConfigurationError("The key '{}' is not an ConfigurationOption()!".format(str(key)))
        # }}}

        # reference the key as an option for clarity
        option = key

        # raise an exception if the option is not known {{{
        if (option.key not in self._configurationOptions):
            raise ConfigurationError("The option '{}' is not registered!".format(str(option)))
        # }}}

        # return the configuration value by the option
        return self._parser[option.section][option.name]
        # }}}


    def __setitem__(self, key, value):
        # DOC {{{
        """Sets the value specified by the ConfigurationOption() given as key.

        Parameters

            key -- an instance of ConfigurationOption()

            value -- a value to set to the configuration value specified by the
                key
        """
        # }}}

        # CODE {{{
        # raise an exception if the specified key is not a ConfigurationOption() {{{
        if (not isinstance(key, ConfigurationOption)):
            raise ConfigurationError("The key '{}' is not an ConfigurationOption()!".format(str(key)))
        # }}}

        # reference the key as an option for clarity
        option = key

        # raise an exception if the option is not known {{{
        if (option.key not in self._configurationOptions):
            raise ConfigurationError("The option '{}' is not registered!".format(str(option)))
        # }}}

        # sanitize, check and set the value
        self._parser[option.section][option.name] = option.sanitizeAndCheck(value)
        # }}}


    # }}}
# }}}


# class ConfigurationOption() {{{
class ConfigurationOption(object):
    # DOC {{{
    """Represents a configuration option specified by the configuration
    section, the option's name (key in configparser's terminology) and
    optionaly the default value. It also provides an optional facility to check
    the configuration option's value.
    """
    # }}}


    # STATIC VARIABLES {{{
    KEY_FORMAT = "{section}///{name}"
    # }}}


    # METHODS {{{
    def __init__(self, *, section, name, defaultValue = '',
                 sanitizeAndCheckFunction = None):
        # DOC {{{
        """Initializes the instance, stores the parameters and determines the
        option's key.

        Paramaters

            section -- the name of the section where this option goes

            name -- the name of the option

            defaultValue -- the default value of the configuration option

            sanitizeAndCheckFunction -- (optional) if specified it is a
                function that sanitizes and checks the option's value and
                returns it. The function is called with two parameters like:

                sanitizedValue = someSanitizingAndCheckFunction(option, value)

                where option is this ConfigurationOption() and value is the
                value to sanitize and check. The function should raise
                ConfigurationError() on check failure.
        """
        # }}}

        # CODE {{{
        # store the parameters {{{
        self.section                    = section
        self.name                       = name
        self.defaultValue               = defaultValue
        self._sanitizeAndCheckFunction  = sanitizeAndCheckFunction
        # }}}

        # determine the option's key
        self.key                        = self.determineKey(self.section, self.name)
        # }}}


    @staticmethod
    def determineKey(section, name):
        # DOC {{{
        """Returns the key of the ConfigurationOption() specified as section
        and name.

        Parameter

            section -- the name of the section where the option is

            name -- the name of the option
        """
        # }}}

        # CODE {{{
        return ConfigurationOption.KEY_FORMAT.format(section = section, name = name)
        # }}}


    def sanitizeAndCheck(self, value):
        # DOC {{{
        """Sanitizes and checks the value if the sanitizing and checking
        function is provided and returns it.

        NOTE: Raise ConfigurationError() in the sanitization and checking
        function as needed.

        Parameters

            value -- the value to sanitize and check
        """
        # }}}

        # CODE {{{
        # return the value unchanged if the sanitizing and checking function is not specified {{{
        if (self._sanitizeAndCheckFunction is None):
            return value
        # }}}

        # sanitize and check the value using the provided function and return it
        return self._sanitizeAndCheckFunction(self, value)
        # }}}


    def __str__(self):
        # DOC {{{
        """Returns the string representation of the ConfigurationOption().
        """
        # }}}

        # CODE {{{
        return "[{section}].{name}".format(
                section = self.section,
                name    = self.name,
        )
        # }}}


    def formatWithValue(self, value):
        # DOC {{{
        """Returns a string containing the configuration option's section, name
        and the specified value.

        Parameters

            value -- the value to format the configuration option with
        """
        # }}}

        # CODE {{{
        return "{option} = {value}".format(
                option  = str(self),
                value   = value,
        )
        # }}}


    # }}}
# }}}


# class ConfigurationUtils() {{{
class ConfigurationUtils(object):
    # DOC {{{
    """Static utility methods for ConfigurationBase() and its subclasses. It
    contains mostly helper methods for sanitizing and checking configuration
    values.
    """
    # }}}


    # METHODS {{{
    @staticmethod
    def stripSpacesMakeLowerCaseAndCheckSupport(option, value, supportedValues):
        # DOC {{{
        """Returns the lowercased and striped string value or raises an
        exception if the sanitized value is not one of the specified supported
        values.

        Parameters

            option -- an instance of ConfigurationOption()

            value -- configuration option's value to sanitize and check

            supportedValues -- a collection of supported values
        """
        # }}}

        # CODE {{{
        # strip surrounding spaces from the value and make it lowercase
        value = value.strip().lower()

        # raise an exception if the value is not supported {{{
        if (value not in supportedValues):
            raise ConfigurationError("Configuration option's '{option}' value must be one of '{supportedValues}' not '{value}'!".format(
                option          = str(option),
                value           = value,
                supportedValues = str(supportedValues),
            ))
        # }}}

        # return the sanitized and checked value
        return value
        # }}}


    @staticmethod
    def checkPositiveIntegerValue(option, value):
        # DOC {{{
        """Returns the value converted to an integer or raises an exception if
        the value could not be converted or is not positive or zero.

        Parameters

            option -- an instance of ConfigurationOption()

            value -- confirmation configuration option value to sanitize and
                check
        """
        # }}}

        # CODE {{{
        # try to convert the value to an integer {{{
        try:
            value = int(value)
        # }}}
        # raise an exception if the value could not be converted {{{
        except Exception as error:
            raise ConfigurationError(
                    "The configuration option's '{option}' value '{value}' is not an integer!".format(
                        option  = str(option),
                        value   = value
                    ),
                    error,
            )
        # }}}

        # raise an exception if the value is not positive or zero {{{
        if (value < 0):
            raise ConfigurationError(
                    "The configuration option's '{option}' value '{value}' is not a positive integer!".format(
                        option  = str(option),
                        value   = value,
            ))
        # }}}

        # return the sanitized and checked value
        return value
        # }}}


    # }}}
# }}}


# class ConfigurationError() {{{
class ConfigurationError(Exception):
    # DOC {{{
    """Raised in case of any problem with the configuration or configuration's
    options. Options' sanitizing and checking functions should raise this
    exception in case of any problem.
    """
    # }}}

    # no methods need to be defined
    pass
# }}}
