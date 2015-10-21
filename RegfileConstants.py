##
## RegfileConstants.py
##      - General regfile constants.
##


# class RegfileConstants() {{{
class RegfileConstants(object):
    # DOC {{{
    """General regfile constants.
    """
    # }}}


    # STATIC VARIABLES {{{
    # the section where regfile's configuration is stored in the configparser
    CONFIGURATION_SECTION   = "regfile"

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
# }}}
