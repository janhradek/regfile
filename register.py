import datetime
import fnmatch
import functools
import glob
import os
import os.path
import re
import threading
import time

from MySum import MySum
from PathTemplates import PathTemplates
from RegfileConfiguration import RegfileConfiguration
from db.DBFile import DBFile
from db.DBModel import DBModel
from progressbar import progressbar

class Register(object):

    DEFAULTFILES = ["_.regfiledefaults", ".regfiledefaults"]
    LOGCOMMENT="# "
    LOGADD="+  "
    LOGUPDATE="!  "
    LOGUPDATED="!! "
    RULER=" - - - - - - - - - - - - - - - - - - - - - - - - - - - - - "

    LOG_DBFILE_RE = re.compile(
                r"^DBF(?P<fileId>\d*)\|" +
                r"n:(?P<fileName>.*)\|" +
                r"g:(?P<group>.*)\|" +
                r"c:(?P<comment>.*)\|" +
                r"s:(?P<fileSize>\d*)\|" +
                r"md1:(?P<md1>.*)\|" +
                r"md5:(?P<md5>.*)\|" +
                r"ed2k:(?P<ed2k>.*)\|$"
    )

    def __init__(self, args):
        """
        initialize the register, read parsed arguments, set the desired operation (op)
        """
        # setup configuration {{{
        self.configuration  = RegfileConfiguration()
        self.dbfile         = self.configuration[RegfileConfiguration.DB]
        self.logfile        = self.configuration[RegfileConfiguration.LOG]
        # }}}

        # arguments
        self.fileId = args.fileId
        self.group = args.group #if args.group != None else "" # set doesnt like it
        self.comment = args.comment #if args.comment != None else "" # set doesnt like it
        self.files = args.filenames
        self.queryasmysum = args.queryasmysum
        self.queryverbose = args.queryverbose
        self.queryed2k = args.queryed2k
        self.auto= args.auto
        self.defaults = args.defaults
        self.determineconfirm(args)

        # defaults
        self.mm = None # database model
        self.op = None # operation function
        self.logf = None # log file
        self.pathTemplates = None  # path templates
        self.totalsize = 0 # the size of all the files to register/check in bytes
        self.defaultcache = dict() # cache with default values
        self.cols = 80 # terminal columns (accurate where supported - Linux/Unix)

        if (not self.configuration.fromConfigFile):
            import textwrap as tw
            print(tw.fill(tw.dedent("""
                        The configuration file '{0}' didn't exist, so a default has been created!
                        That also means that a default location for the database '{1}' is being
                        used. Review and change the configuration if necessary! The requested
                        operation has been canceled. (This warning is displayed only once!)
                        """.format(self.configuration.path, self.dbfile))
                , initial_indent="!!!   ", subsequent_indent="!!!   "))
            return

        # key: the op code, value: op function, thorough for processfiles
        dd = { \
                "r" : (self.register, True),\
                "c" : (self.check, True),\
                "i": (self.batchimport, True),\
                "s" : (self.setdata, False),\
                "q" : (self.query, False),\
                "l" : (self.resetfromlog, False),\
                "d" : (self.makedefaults, False),\
                }
        if not args.op in dd:
            raise ValueError(
                    "Operation '{}' is not supported!"
                    .format(args.op))

        self.op = dd[args.op][0]

        if self.op != self.resetfromlog:
            self.mm = DBModel(self.dbfile)

        self.processfiles(thorough=dd[args.op][1])

        #if sys.platform == "linux" or sys.platform == "linux2":
        try:
            self.cols = int(os.popen('stty size', 'r').read().split()[1])
        except:
            pass

    def go(self):
        """
        just run the designed doperation
        """
        try:
            if self.op:
                self.op()
        finally:
            if self.logf:
                self.logf.close()
            if self.mm:
                self.mm.close()

    def determineconfirm(self, args):
        """arguments take precedence over configuration"""
        self.confirm = self.confirmproblem = False
        if args.commit: # specified on command line
            cc = args.commit
        else: # get value from config instead
            cc = self.configuration[RegfileConfiguration.COMMIT]

        self.confirm = (cc == "confirm")
        self.confirmproblem = (cc == "problem")

    def docommit(self, problems):
        if self.confirm or (self.confirmproblem and problems):
            while True:
                response = input("Do you wish to commit these changes? [YES/no] ").lower().strip()
                if (response not in ["", "yes", "y", "no", "n"]):
                    print("Only yes or no (or just Enter) is a valid choice.")
                    continue
                return (response in ["", "yes", "y"])
        return True

    def register(self):
        return self.registercheck(True)

    def check(self):
        return self.registercheck(False)

    def registercheck(self, register):
        """
        register (or check) the given files
        """
        pgr, pcom, pdir, psize = "", "", "", 0 # previous group, comment, directory and size
        tstart = time.time()
        ii = 0
        #fail = 0
        failfiles = []
        dbFilesToStore = []
        for ff in self.files:
            ii = ii + 1
            dupe = False
            cdir = os.path.dirname(ff) # directory
            sff = os.path.basename(ff) # short filename
            try:
                if cdir != pdir:
                    print("Directory [{}]".format(cdir))
                    pdir = cdir

                dbf = DBFile(ff)
                if register: # group and comment
                    gr, com = self.getgroupcomment(ff)
                    if gr != pgr or com != pcom:
                        print("Using group:'{}' comment:'{}'".format(gr, com))
                        pgr, pcom = gr, com
                    dbf.group, dbf.comment = gr, com
                self.printstatus(ii, sff, "Quick")
                # stage 1 - silent
                ms = MySum(ff)
                ms.upgrade(1)
                dbf.update(ms)
                dbfs = self.mm.querydata(dbf, quick=True)
                if register:
                    if not dbfs is None:
                        #self.printstatus(ii, sff, "Already registered?")
                        dupe = True
                        #print("Warning! The file " + sff + " might already be registered (quick check).")
                else: # check
                    if dbfs is None:
                        self.printstatus(ii, sff, "FAIL")
                        #fail = fail+1
                        failfiles.append(ff)
                        print() # newline
                        continue
                #ms.upgrade(2)
                tt = threading.Thread(target=ms.upgrade,args=[2])
                tt.start()
                while tt.is_alive():
                    try:
                        self.printstatus(ii, sff, self.msgpgs(ms,psize,tstart,dupe))
                        time.sleep(0.25)
                    except KeyboardInterrupt:
                        ms.requestStop()
                        self.printstatus(ii, sff, "Interrupted")
                        #fail = fail+1
                        failfiles.append(ff + "    (Interrupted)")
                        tt.join()
                        #break
                        raise
                tt.join()
                #if ms.stopRequested:
                #    print()
                #    break
                psize = psize + ms.fileSize
                dbf.update(ms)
                dbfs = self.mm.querydata(dbf)
                if register:
                    if dbfs is None:
                        self.mm.insert(dbf, commit=False)
                        self.printstatus(ii, sff, "New entry " + str(dbf.fileId))
                        dbFilesToStore.append(dbf)
                    else:
                        if dbf.match(dbfs[0], nametoo=True):
                            self.printstatus(ii, sff, "Already registered (full match) as " + str(dbfs[0].fileId))
                        else:
                            self.printstatus(ii, sff, "Already registered (data match) as " + str(dbfs[0].fileId))
                        failfiles.append(ff)
                else:
                    if dbfs is None:
                        self.printstatus(ii, sff, "FAIL")
                        failfiles.append(ff)
                    else:
                        stat = "OK"
                        if dbfs[0].fileName.lower() != dbf.fileName.lower():
                            stat = "(as " + dbfs[0].fileName + ") OK"
                        stat = "id:" + str(dbfs[0].fileId) + " " + stat
                        self.printstatus(ii, sff, stat)
                print()
            except KeyboardInterrupt:
                fail = ff + "    (Interrupted)"
                if failfiles[-1] != fail: # very likely to happen if interrupted in thread
                    self.printstatus(ii, sff, "Interrupted")
                    failfiles.append(fail)
                print()
                break

        print(self.RULER)
        if register:
            print("About to register {} files out of {}".format(ii-len(failfiles),ii))
        else:
            print("Passed {} files out of {}.{}".format(ii-len(failfiles), ii, "ALL OK" if not len(failfiles) else "" ))
        if len(failfiles) > 0:
            print("A list of files that failed:")
            for ff in failfiles:
                print("    " + ff)
        if register:
            if len(failfiles) == ii:
                print("No files were registered!")
            elif self.docommit(failfiles):
                self.mm.commit()
                for storedDBFile in dbFilesToStore:
                    self.log(Register.LOGADD + self._formatDBFileForLog(storedDBFile))
                print("Done.")
            else:
                print("Aborted!")

    def batchimport(self):
        """
        store all data stored in the provided files (usually named like sumlog.txt)

        Only [MYSUM...] entries are valid.
        """
        pgr, pcom, pdir = "", "", "" # previous group, comment and directory
        ii = 0 # file no
        jj = 0 # successfully imported entries
        warn = 0 # number of warnings (duplicities)
        failfiles = [] # a list of files that failed to import
        allDBFilesToStore = []

        for ff in self.files:
            ii = ii + 1
            cdir = os.path.dirname(ff) # directory
            if cdir != pdir:
                print("Directory [{}]".format(cdir))
                pdir = cdir

            gr, com = self.getgroupcomment(ff, imp=True)
            if gr != pgr or com != pcom:
                print("Using group:{} comment:{}".format(gr, com))
                pgr, pcom = gr, com

            self.printstatus(ii, ff, "")

            with open(ff, "r") as fsum:
                ll = 0
                fail = False

                dbFilesToStoreFromImportFile = []
                for line in fsum:
                    ll = ll + 1
                    self.printstatus(ii, ff, "L" + str(ll))
                    try:
                        ms = MySum.fromString(line)
                    except ValueError:
                        self.printstatus(ii, ff, "not a MYSUM!")
                        print()
                        fail = True
                        break
                    self.printstatus(ii, ff, ms.fileName + " L" + str(ll))

                    dbf = DBFile.fromMySum(ms, gr, com)
                    if dbf in self.mm:
                        warn = warn + 1
                        dbfs = self.mm.querydata(dbf)
                        if dbf.match(dbfs[0], nametoo=True):
                            self.printstatus(ii, ff, "Already registered (full match) as {} L{}".format(dbfs[0].fileId, ll))
                        else:
                            self.printstatus(ii, ff, "Already registered (data match) as {} L{}".format(dbfs[0].fileId, ll))
                        print()
                        continue
                    jj = jj + 1
                    dbFilesToStoreFromImportFile.append(dbf)
                if fail:
                    if ll == 1:
                        self.printstatus(ii, ff, "FAIL")
                        failfiles.append(ff)
                        print()
                    else:
                        sll = "after " + str(ll) + " lines"
                        self.printstatus(ii, ff, "FAIL " + sll)
                        failfiles.append(ff + "       (" + sll + ")")
                        print()
                else:
                    for dbf in dbFilesToStoreFromImportFile:
                        self.mm.insert(dbf, commit=False)
                    allDBFilesToStore.extend(dbFilesToStoreFromImportFile)
                print()
        print(self.RULER)
        print("About to import {} entries ({} warnings) from {} files out of {}".format(jj, warn, len(self.files) - len(failfiles), len(self.files)))
        if len(failfiles) > 0:
            print("A list of files that failed:")
            for ff in failfiles:
                print("    " + ff)
        if self.docommit(failfiles):
            self.mm.commit()
            for storedDBFile in allDBFilesToStore:
                self.log(Register.LOGADD + self._formatDBFileForLog(storedDBFile))
            print("Done.")
        else:
            print("Aborted!")

    def setdata(self):
        """
        Change some details of the entries given by IDs. IDs are required.

        Only filename, comment and group can be changed.
        """
        ff = None
        if (isinstance(self.files, list)):
            if len(self.files) > 1:
                print("Please provide just one name or none ar all!")
                return
            elif len(self.files) == 1:
                ff = self.files[0]

        dbf = DBFile(fileId=self.fileId, fileName=ff, group=self.group, comment=self.comment)
        self.log(Register.LOGUPDATE + self._formatDBFileForLog(dbf))
        dbf = self.mm.update(dbf)
        if not dbf:
            print("Error updating the entry!")
        else:
            self.log(Register.LOGUPDATED + self._formatDBFileForLog(dbf))

    def query(self):
        """
        Query the register for any entry matching the parameters.

        Only parts of the entry have to match the given parameters (ilike)
        """
        ff = None
        if (isinstance(self.files, list)):
            if len(self.files) > 1:
                print("Please provide just one name or none ar all!")
                return
            elif len(self.files) == 1:
                ff = self.files[0]

        dbf = DBFile(fileId=self.fileId, fileName=ff, group=self.group, comment=self.comment)
        ll = self.mm.queryinfo(dbf)
        if ll == None:
            print("No record matches the query!")
        else:
            formatDBFileMethod = self._formatDBFile
            if self.queryasmysum:
                formatDBFileMethod = self._formatDBFileAsMysum
            elif self.queryed2k:
                formatDBFileMethod = self._formatDBFileAsED2K
            elif self.queryverbose:
                formatDBFileMethod = functools.partial(self._formatDBFile, verbose = True)

            for dbf in ll:
                print(formatDBFileMethod(dbf))


    def resetfromlog(self):
        """
        drop the db and reinsert (and update) all the entries from log to the empty db
        """
        #Register.LOGFILE = os.path.expanduser(Register.LOGFILE)
        #Register.DBFILE = os.path.expanduser(Register.DBFILE)
        if not os.path.exists(self.logfile):
            print("The logfile " + self.logfile + " doesn't exist!")
            return
        # backup the old one
        if os.path.exists(self.dbfile):
            bak = self.dbfile + "~"
            if os.path.exists(bak):
                if input("A backup already exists. Remove it (only Yes is accepted)? ") != "Yes":
                    return
                os.remove(bak)
            os.rename(self.dbfile, bak)
        # read new one
        print("This might take a while depending on the log size. Please wait ...")
        self.mm = DBModel(self.dbfile)
        with open(self.logfile, "r") as self.logf:
            for ll in self.logf:
                if ll.startswith(Register.LOGADD):
                    dbf = self._dbFileFromLog(ll[len(Register.LOGADD):])
                    self.mm.insert(dbf, commit=False)
                elif ll.startswith(Register.LOGUPDATED):
                    dbf = self._dbFileFromLog(ll[len(Register.LOGUPDATED):])
                    self.mm.commit()
                    self.mm.update(dbf, setall=True)
        self.mm.commit()
        print("Done")

    def log(self, line):
        """
        log the line to log file
        if this is late commit op, store line for later (in self.latelog buffer)
        to write stored lines set op to eg. None and call it again
        """
        if not self.logf:
            self.logfile = os.path.expanduser(self.logfile)
            if not os.path.exists(self.logfile):
                self.logf = open(self.logfile, "w")
            else:
                self.logf = open(self.logfile, "a")
            self.logf.write(self.LOGCOMMENT+datetime.datetime.now().ctime()+"\n")
        if line:
            self.logf.write(line+"\n")

    def printstatus(self, no, ff, msg):
        """
        print the provided information so it fits on one line of the terminal

        self.cols holds the maximum line size
        everything will fit to fill the linelike this
        |[no/total] filenamefilename~filenamefilename   message |
        |[no/total] filenamefi~mefilename   veryverylongmessage |
        """
        stat = str(len(self.files))
        stat = "[{}/{}] ".format(str(no).rjust(len(stat)), len(self.files))
        # filename has all the space that's left by message and current stat
        lff = self.cols - len(msg) - len(stat) - 5 # 1 (before) + 3 (after) + 1 (end)
        if lff < len(ff):  # not enough space - construct file~name
            hff = int((lff-1)/2)
            ff = ff[:hff]+"~"+ff[-hff:]
        ff = ff.ljust(lff)
        print("\r{} {}   {}".format(stat, ff, msg), end="")

    def msgpgs(self, ms, psize, tstart, dupe=False):
        """
        create a progress message from the given info
        """
        pgs = ms.processedSize
        size = ms.fileSize
        tnow = time.time()
        if pgs == None:
            pgs = 0
        if size == 0:
            percent = 100
        else:
            percent = int(pgs * 100 / size)
        tdif = tnow - tstart
        if tdif == 0:
            speed = 0
        else:
            speed = (psize + pgs) / (1024*1024*tdif)
        if speed == 0:
            speed = 0
            eta = " --:--"
        else:
            eta = int((self.totalsize - psize - pgs) / (1024*1024*speed))
            speed = int(speed)
            if eta != 0:
                eta = " {:02d}:{:02d}".format(int(eta/60), eta % 60)
            else:
                eta = " 00:00"
        #return "{}{:3d}% {:3d}MB/s{}".format("*" if dupe else "", percent, speed, eta)
        return "{}{} {:3d}MB/s{}".format("* " if dupe else "", progressbar(percent,size=21), speed, eta)

    def processfiles(self, thorough=True):
        """
        parse the files from arguments to a useable list

        if thorough is True the list of directories, files and wildcards is turned into a list of real filenames (and total size is computed)
        """
        if (isinstance(self.files, str)):
            self.files = [ self.files ]
        elif self.files is None:
            return
        elif (not isinstance(self.files, list)):
            raise ValueError("The files is not a list nor a string")

        if not thorough:
            return

        rf = [] # real files
        ts = 0 # total size
        if (os.name == 'posix'):
            cwd = os.popen('pwd').read().strip('\n')
        else:
            cwd = os.getcwd()

        for ff in self.files:
            # the file could be: a file, a directory (then add everything recursively), or a wildcard
            ff = os.path.expanduser(ff)

            if (not os.path.isabs(ff)):
                ff = os.path.normpath(os.path.join(cwd, ff))

            if (os.path.exists(ff) and os.path.isdir(ff)):
                for root, dirnames, filenames in os.walk(ff):
                    for filename in fnmatch.filter(filenames, '*'):
                        fn = os.path.join(root, filename)
                        ts = ts + os.stat(fn)[6]
                        rf.append(fn)
            else:
                for fn in glob.iglob(ff):
                    fn = os.path.join(cwd, fn)
                    ts = ts + os.stat(fn)[6]
                    rf.append(fn)
        self.totalsize = ts
        self.files = rf
        #print(rf)

    def makedefaults(self):
        """
        create a defaults file that can be edited to change default group and comment
        the file is created in the current directory
        """
        if os.path.exists(self.DEFAULTFILES[0]):
            print("The file " + self.DEFAULTFILES[1] + " already exists!")
            return
        elif os.path.exists(self.DEFAULTFILES[1]):
            print("Warning the file " + self.DEFAULTFILES[1] + " exists!")
        with open(self.DEFAULTFILES[0], "w"):
            pass
        print("File " + self.DEFAULTFILES[0] + " created. You can rename it to "+ self.DEFAULTFILES[1] + " if you want.")

    def getgroupcomment(self, ff, imp=False):
        """
        determine group and comment for the given file
        the sources for both of these values are (in this order, lowest to highest prio):
        - the defaults files (the first of .regfiledefaults or _.regfiledefaults )
            - the first line is the default group (if not empty)
            - the second line is the default comment (if not empty)
        - path templates (group and comment for certain directories)
        - command arguments

        returns (group, comment) tuple
        to be used with register and import only
        set imp to True if importing
        """
        gr = self.group # if self.group != None else "" # bad idea - the values are compared later
        com = self.comment # if self.comment != None else ""
        #if gr != "" and gr != None and com != "" and com != None:
        if gr and com:
            return gr, com

        if self.defaults:
            # first look in the cache
            dirname = os.path.dirname(ff)
            if dirname in self.defaultcache:
                grcom = self.defaultcache[dirname]
                if grcom != None: # None means "use arg values"
                    gr, com = grcom
            else:
                # not in cache - read the defaults file
                for df in self.DEFAULTFILES:
                    fdf = os.path.join(dirname, df)
                    if not os.path.exists(fdf) or not os.path.isfile(fdf):
                        continue
                    try:
                        dd = open(fdf, 'r')
                    except:
                        print("Error trying to open the file '{}'".format(fdf))
                        continue
                    ll = dd.readlines()
                    dd.close()
                    if len(ll) >= 1 and not gr:#( gr == "" or gr == None ):
                        gr = ll[0].strip()
                    if len(ll) >= 2 and not com:#( com == "" or com == None):
                        com = ll[1].strip()
                    break

                # store result in cache for further use
                if gr == self.group and com == self.comment:
                    self.defaultcache[dirname] = None
                else:
                    #print("Using defaults: group='{}' comment='{}'".format(dgr, dcom))
                    self.defaultcache[dirname] = (gr, com)

        if self.auto:
            # now the magic
            # ff can be relative to os.getcwd or absolute, absolute path is needed
            if not os.path.isabs(ff):
                ff = os.path.join(os.getcwd(), ff)

            if self.pathTemplates == None:
                self.pathTemplates = PathTemplates.fromConfig(self.configuration[RegfileConfiguration.PATH_TEMPLATES])

            gr, com = self.pathTemplates.apply(ff, self.group, self.comment, gr, com, imp)

        return (gr,com)


    @staticmethod
    def _formatDBFileAsMysum(dbFile):
        # DOC {{{
        """Returns a string with the specified DBFile()'s properties in
        the MySum format.

        Parameters

            dbFile -- a DBFile() to format
        """
        # }}}

        # CODE {{{
        return MySum.format(
            fileName    = dbFile.fileName,
            fileSize    = dbFile.fileSize,
            md5         = dbFile.md5,
            md1         = dbFile.md1,
            ed2k        = dbFile.ed2k,
        )
        # }}}


    @staticmethod
    def _formatDBFileAsED2K(dbFile):
        # DOC {{{
        """Returns a string containing the specified DBFile()'s as an
        ED2K link.

        Parameters

            dbFile -- a DBFile() to format
        """
        # }}}

        # CODE {{{
        return "ed2k://|file|{fileName}|{fileSize}|{ed2k}|/".format(
            fileName    = dbFile.fileName,
            fileSize    = dbFile.fileSize,
            ed2k        = dbFile.ed2k,
        )
        # }}}


    @staticmethod
    def _formatDBFile(dbFile, verbose = False):
        # DOC {{{
        """Formats the specified DBFile()'s properties to a string and
        returns it.

        Parameters

            dbFile -- a DBFile() to format

            verbose -- (optional) if True checksums are included
        """
        # }}}

        # CODE {{{
        # a list of lines of formated DBFile()'s properties
        formatedLines = []

        # print file's ID, name and size {{{
        formatedLines.append("[{fileId:5d}] '{fileName}' s:{fileSize}".format(
            fileId      = dbFile.fileId,
            fileName    = dbFile.fileName,
            fileSize    = dbFile.fileSize,
        ))
        # }}}

        # print the file's group if it is not empty {{{
        if (dbFile.group):
            formatedLines.append("        group: {}".format(dbFile.group))
        # }}}

        # print the file's comment if it is not empty {{{
        if (dbFile.comment):
            formatedLines.append("        comment: {}".format(dbFile.comment))
        # }}}

        # print file's checksums if verbosity is set {{{
        if (verbose):
            formatedLines.append("        md1:{md1}  md5:{md5}  ed2k:{ed2k}".format(
                md1     = dbFile.md1,
                md5     = dbFile.md5,
                ed2k    = dbFile.ed2k
            ))
        # }}}

        # join all the lines and return the resulting string for formated DBFile()'s properties
        return "\n".join(formatedLines)
        # }}}


    @staticmethod
    def _formatDBFileForLog(dbFile):
        # DOC {{{
        """Returns a string representation of the specified dbFile for the log.

        Parameters

            dbFile -- a DBFile() to format
        """
        # }}}

        # CODE {{{
        return ("DBF{fileId:06d}|n:{fileName}|" +
                "g:{group}|c:{comment}|s:{fileSize}|" +
                "md1:{md1}|md5:{md5}|ed2k:{ed2k}|").format(
                    fileId      = dbFile.fileId if (dbFile.fileId is not None) else 0,
                    fileName    = dbFile.fileName,
                    group       = dbFile.group if (dbFile.group is not None) else "",
                    comment     = dbFile.comment if (dbFile.comment is not None) else "",
                    fileSize    = dbFile.fileSize,
                    md1         = dbFile.md1,
                    md5         = dbFile.md5,
                    ed2k        = dbFile.ed2k,
        )
        # }}}


    @staticmethod
    def _dbFileFromLog(ls):
        rr = Register.LOG_DBFILE_RE.match(ls)
        if not rr:
            raise ValueError("The string " + ls + " doesnt match the logline!")

        matchGroups = rr.groupdict()

        dbf = DBFile(
                fileId      = int(matchGroups['fileId']),
                fileName    = matchGroups['fileName'],
                fileSize    = int(matchGroups['fileSize']),
                group       = matchGroups['group'],
                comment     = matchGroups['comment'],
                md1         = matchGroups['md1'],
                md5         = matchGroups['md5'],
                ed2k        = matchGroups['ed2k'],
        )

        assert (Register._formatDBFileForLog(dbf).strip() == ls.strip())

        return dbf


def runop(args):
    Register(args).go()

if __name__ == "__main__":
    print("This is a library, please run regfile. (There's no unittest yet.)")
