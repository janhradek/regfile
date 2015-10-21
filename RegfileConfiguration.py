##
## RegfileConfiguration.py
##      - Maintains regfile's configuration.
##


# import of required modules {{{
import functools
import os.path

from ConfigurationBase import ConfigurationBase
from ConfigurationBase import ConfigurationOption
from ConfigurationBase import ConfigurationUtils
from RegfileConstants import RegfileConstants
# }}}


# class RegfileConfiguration() {{{
class RegfileConfiguration(ConfigurationBase):
    # DOC {{{
    """Maintains regfile's configuration.
    """
    # }}}


    # STATIC VARIABLES {{{
    # the default location of the configuration
    DEFAULT_PATH                        = os.path.expanduser("~/.regfile")

    # alias for 'regfile' section's ConfigurationOption() {{{
    _RegfileConfigurationOption = functools.partial(
            ConfigurationOption,
            section                     = RegfileConstants.CONFIGURATION_SECTION,
    )
    # }}}

    # configuration options {{{
    # SQLite database location option {{{
    DB = _RegfileConfigurationOption(
            name                        = 'db',
            defaultValue                = '~/dbfile.sqlite',
            sanitizeAndCheckFunction    = lambda option, value: os.path.expanduser(value),
    )
    # }}}

    # log location option {{{
    LOG = _RegfileConfigurationOption(
            name                        = 'log',
            defaultValue                = '~/dbfile.log',
            sanitizeAndCheckFunction    = lambda option, value: os.path.expanduser(value),
    )
    # }}}

    # commit option {{{
    COMMIT = _RegfileConfigurationOption(
            name                        = 'commit',
            defaultValue                = 'auto',
            sanitizeAndCheckFunction    = lambda option, value : ConfigurationUtils.stripSpacesMakeLowerCaseAndCheckSupport(
                option          = option,
                value           = value,
                supportedValues = RegfileConstants.SUPPORTED_COMMIT_VALUES,
            ),
    )
    # }}}

    # path templates option {{{
    PATH_TEMPLATES = _RegfileConfigurationOption(
            name                        = 'pathtemplates',
    )
    # }}}

    # a tuple of all general configuration options {{{
    GENERAL_CONFIGURATION_OPTIONS = (
            DB,
            LOG,
            PATH_TEMPLATES,
            COMMIT,
    )
    # }}}
    # }}}
    # }}}


    # METHODS {{{
    def __init__(self, configurationPath = DEFAULT_PATH):
        # DOC {{{
        """Initializes the instance, calls the superclass initializer to
        register predefined options and pass the provided configuration file
        path.

        Parameters

            configurationPath -- (optional) the location of the configuration
                file
        """
        # }}}

        # CODE {{{
        # call the superclass' initialized to register the options and set the configuration path {{{
        super().__init__(
                *RegfileConfiguration.GENERAL_CONFIGURATION_OPTIONS,
                configurationPath   = configurationPath,
                restrictions        = (ConfigurationBase.RESTRICT_SURPLUS | ConfigurationBase.RESTRICT_MISSING),
        )
        # }}}
        # }}}


    # }}}
# }}}
