##
## pathTemplates.py
##      -
##
# the array contains the instructions for the AutoValues class
# each entry contains: re, group, comment, options
# the most important part is re - the regular expression
# the group and comment values determine the respective output, the following special values are possible
#   "" (empty string) - nothing will be set
#   \1 - get first match from re (other numbers are possible)
# the options can have the following strings (separated by spaces)
#   match - (the default) re.match
#   search - re.search (vs the match)
#   sanitize - replace some non-alnum characters with space from the group and comment (see SANITIZE)
#   import - only process this when importing
#   continue - normaly the AutoValues stop if a match is found, continue will allow other matches as well
# the following is only an unimplemented proposal:
#   g+ - instead of replacing the group value, append a space and the output (append group)
#   +g - preprend to group
#   c+ - instead of replacing the comment value, append a space and the output (append comment)
#   +c - prepend to comment
# order does matter - the items are processed one by one and the first to match is applied, unless continue is specified


# import of required modules {{{
import csv
import functools
import os
import os.path
import re
# }}}


# class PathTemplates() {{{
class PathTemplates(object):
    # DOC {{{
    """Allows to determine groups and comments from the filename.
    """
    # }}}


    # STATIC VARIABLES {{{
    # }}}


    # METHODS {{{
    @staticmethod
    def fromConfig(pathTemplatesConfig):
        # DOC {{{
        # }}}

        # CODE {{{
        pathTemplates = PathTemplates();

        for pathTemplateConfig in pathTemplatesConfig.split("\n"):
            pathTemplates.append(PathTemplate.fromConfig(pathTemplateConfig))

        return pathTemplates
        # }}}


    def __init__(self):
        # DOC {{{
        # }}}

        # CODE {{{
        self.pathTemplates = []
        # }}}


    def append(self, pathTemplate):
        # DOC {{{
        # }}}

        # CODE {{{
        self.pathTemplates.append(pathTemplate)
        # }}}


    def apply(self, fullFilename, argumentGroup, argumentComment, defaultGroup, defaultComment, import_):
        # DOC {{{
        # }}}

        # CODE {{{
        # initialize lists of groups and comments determined from the templates {{{
        templatesGroups = []
        templatesComments = []
        # }}}

        # try to match and apply each template {{{
        for pathTemplate in self.pathTemplates:
            # try to match and apply the current template
            (matched, templateGroup, templateComment,) = pathTemplate.apply(fullFilename, import_)

            # continue with the next template if the current one was not matched {{{
            #
            if (matched):
                # append the group if applying the template yielded a group {{{
                if (templateGroup):
                    templatesGroups.append(templateGroup)
                # }}}
                # append the comment if applying the template yielded a comment {{{
                if (templateComment):
                    templatesComments.append(templateComment)
                # }}}

                # continue only if the continue option is set in the template {{{
                if (not pathTemplate.options[PathTemplate.CONTINUE_OPTION]):
                    break
                # }}}
            # }}}
        # }}}

        # join the groups and comments determined from templates to strings {{{
        templatesGroup      = " ".join(templatesGroups)
        templatesComment    = " ".join(templatesComments)
        # }}}

        # the priority is argument, automatic (self) and default
        group = functools.reduce(lambda x, y: x or y, [argumentGroup, templatesGroup, defaultGroup])
        comment = functools.reduce(lambda x, y: x or y, [argumentComment, templatesComment, defaultComment])

        # return the determine group and comment as a tuple
        return (group, comment)
        # }}}


    # }}}
# }}}


# class PathTemplate() {{{
class PathTemplate(object):
    # DOC {{{
    """Represents one template to determine group and comment from the
    filename.
    """
    # }}}


    # STATIC VARIABLES {{{
    # all these characters will be replaced with spacces
    SANITIZED_CHARACTERS = "._/"

    # options {{{
    MATCH_OPTION        = "match"       # the entire pattern must match (the default)
    SEARCH_OPTION       = "search"      # look for the pattern in anywhere in the filename instead of matching the whole path
    IMPORT_OPTION       = "import"      # match the pattern only during import
    SANITIZE_OPTION     = "sanitize"    # replace all characters from SANITIZED_CHARACTERS in filename with spaces
    CONTINUE_OPTION     = "continue"    # if set another template may match, resulting values will be added
    # }}}

    # a dictionary of default options and their values
    DEFAULT_OPTIONS = {
            MATCH_OPTION    : True,
            SEARCH_OPTION   : False,
            IMPORT_OPTION   : False,
            SANITIZE_OPTION : False,
            CONTINUE_OPTION : False,
    }
    # }}}


    # METHODS {{{
    @staticmethod
    def fromConfig(pathTemplateConfig):
        # DOC {{{
        # }}}

        # CODE {{{
        # remove surrounding spaces
        pathTemplateConfig = pathTemplateConfig.strip()

        # remove comma at the end of the specification if present {{{
        if pathTemplateConfig.endswith(","):
            pathTemplateConfig = pathTemplateConfig[:-1]
        # }}}

        # parse the specification as one line in CSV file into a list
        specificationEntries = csv.reader([pathTemplateConfig], skipinitialspace=True).__next__()

        # unpack the specification entries
        pattern, groupTemplate, commentTemplate, optionSpecification = specificationEntries

        # compile pattern
        pattern = re.compile(pattern)

        # copy the default options
        options = dict(PathTemplate.DEFAULT_OPTIONS)

        # determine options {{{
        for option in (option.strip().lower() for option in optionSpecification.replace(",", " ").split()):
            # skip the option if it is an empty string {{{
            if (option == ""):
                continue
            # }}}

            # check that the option is supported {{{
            if (option not in options):
                raise ValueError("Unsupported option '{}' in '{}'".format(option, pathTemplateConfig))
            # }}}

            # set the option
            options[option] = True
        # }}}

        # create and return the new path template
        return PathTemplate(pattern, groupTemplate, commentTemplate, options)
        # }}}


    def __init__(self, pattern, groupTemplate, commentTemplate, options):
        # DOC {{{
        # }}}

        # CODE {{{
        # save the specified attributes {{{
        self.pattern            = pattern
        self.groupTemplate      = groupTemplate
        self.commentTemplate    = commentTemplate
        self.options            = options
        # }}}
        # }}}


    def apply(self, fullFilename, import_):
        # DOC {{{
        """Tries to apply the template on the specified filename and returns a
        tuple in the format (matched, group, comment,) where matched is True if
        the template has been matched successfuly. Group and comment are the
        resulting group and comment for the given file and this template.

        Parameters

            fullFilename -- full path of the file which the template should
                be matched to

            import_ -- whether or not the file is being imported or not
        """
        # }}}

        # CODE {{{
        # initialize the returned values {{{
        group = None
        comment = None
        # }}}

        # return None if the pattern should be matched only during import but the file is being imported {{{
        if ((self.options[PathTemplate.IMPORT_OPTION]) and (not import_)):
            return (False, None, None)
        # }}}

        # search for the pattern anywhere in the filename if the option is set {{{
        if (self.options[PathTemplate.SEARCH_OPTION]):
            res = self.pattern.search(fullFilename)
        # }}}
        # or use full match (the default) {{{
        else:
            res = self.pattern.match(fullFilename)
        # }}}

        # return if the pattern did not match {{{
        if (res is None):
            return (False, None, None)
        # }}}

        # set the group if the group template is specified {{{
        if (self.groupTemplate):
            group = res.expand(self.groupTemplate)
        # }}}

        # set the comment if the group template is specified {{{
        if (self.commentTemplate):
            comment = res.expand(self.commentTemplate)
        # }}}

        # sanitize the group and comment if the option is set {{{
        if (self.options[PathTemplate.SANITIZE_OPTION]):
            # replace every occurance of the each sanitized character with a space {{{
            for char in PathTemplate.SANITIZED_CHARACTERS:
                if (group):
                    group = group.replace(char, " ")
                if (comment):
                    comment = comment.replace(char, " ")
            # }}}

            # remove white spaces from both ends of the resulting group and comment {{{
            if (group):
                group = group.strip()
            if (comment):
                comment = comment.strip()
            # }}}
        # }}}

        # return the resulting groyp and comment
        return (True, group, comment)
        # }}}

    # }}}
# }}}
