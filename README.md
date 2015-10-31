regfile
=======

regfile is a commandline interface (CLI) tool to store checksums of files in a database to be later checked for possible errors.

It's a simple Python 3 project that uses SQLite.

Unlike other tools to check files, this one stores every data in a centralized database. Also it allows to assign each file to a group (currently only a simple string for each file) and give each file a comment. It is also possible to let the tool automatically decide group and comment for a file.

Features
--------

* every file is represented by filename, size, group, comment, md5 sum, md5 of the first 1MB and ED2K hash
* operations
    * -R register files
    * -C check files
    * -I import files (imports MYSUM sumlog.txt files)
    * -Q query files (by anything, -Q alone outputs all the files)
    * -RESETFROMLOG reset from log (log can serve as a backup)
    * -D make defaults (.regfiledefaults, _.regfiledefaults)
    * -S set details (comment, group, filename)
* switches
    * -a - dont guess comment and group automatically
    * -c - comment
    * -ca - commit automatically
    * -cc - confirm every commit
    * -cp - confirm only commits with problems
    * -d - dont read the defaults
    * -g - group
    * -i - id
    * -qm - query outputs MYSUM format
    * -qa - query outputs everything (query alone only prints id, name, size, group and comment)
    * -qe - query outputs ED2K links
* the database and the logfile location is stored in a configuration file ~/.regfile
    * there are also some other settings
    * to create a default config just run the program
* logfile can double as a database backup
* MYSUM is an old internal format for storing checksums, this program made it obsolete
* groups and comments may come from three sources: commandline parameters, defaults and autovalues
    * the arguments have the highest priority, defaults are next and autovalues have least weight
    * defaults is a small text file (either .regfiledefaults or _.regfiledefaults) in the same directory as the file to be registered and contains default group on the first line and default comment on the second one
* autovalues is a list of rules in config that configures a mechanism to automatically assign group and comment to files based on their location and filename
    * a search or match regular expression criteria
    * the group specification and the comment specification (both can refer to the criteria)
        * if this field is empty nothing is set
        * if it is of the referential form \\1 ... \\9 then the appropriate sequence that matched the regular expression will be used
        * also a plaintext can be used and then this value will be used verbatim
    * and options
        * match - the criteria has to match completely in order for the rule to take effect
        * search - the criteria has to match only part of the path
        * sanitize - replace some non alphanumeric characters with spaces
        * import - only allow processing this rule if importing
        * continue - even if this rule applies continue processing other criteria as well
    * order of the rules does matter, the first matching criteria ends the evaluation unless continue option has been specified
    * example: "sumlog.([^/]+).txt$", "", "\\1", "search sanitize continue import" specifies that if a files sumlog.\*.txt is encountered, part of its filename becomes a comment, it will be sanitized, but it will apply only during import and other rules may apply as well

Requirements
------------

* Python 3
* SQLite
* SQLAlchemy
