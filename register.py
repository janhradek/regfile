import os
import os.path
import glob
import fnmatch
import threading
import time
import sys
import datetime

import dbmodel
import dbfile
import mysum
from PathTemplates import PathTemplates

from config import CFG, CFGLOC
from progressbar import progressbar

class Register(object):

    DEFAULTFILES = ["_.regfiledefaults", ".regfiledefaults"]
    #DBFILE="~/ViTAL/dbfile.sqlite"
    #LOGFILE="~/ViTAL/dbfile.log"
    LOGCOMMENT="# "
    LOGADD="+  "
    LOGEXISTS="?  "
    LOGEXISTING="?@ "
    LOGUPDATE="!  "
    LOGUPDATED="!! "
    RULER=" - - - - - - - - - - - - - - - - - - - - - - - - - - - - - "

    def __init__(self, args):
        """
        initialize the register, read parsed arguments, set the desired operation (op)
        """
        # config
        self.dbfile = CFG["regfile"]["db"]
        self.logfile = CFG["regfile"]["log"]

        # arguments
        self.idno = args.idno
        self.group = args.group #if args.group != None else "" # set doesnt like it
        self.comment = args.comment #if args.comment != None else "" # set doesnt like it
        self.files = args.filenames
        self.queryasmysum = args.queryasmysum
        self.queryverbose = args.queryverbose
        self.queryed2k = args.queryed2k
        self.auto= args.auto
        self.defaults = args.defaults
        self.dryrun = args.dryrun
        self.determineconfirm(args)
        #self.confirmauto = args.confirmauto and not args.dryrun
        #self.confirm = args.confirm and not args.dryrun
        #self.confirmproblem = args.confirmproblem and not args.dryrun

        # defaults
        self.mm = None # database model
        self.op = None # operation function
        self.oplatecommit = [ self.register, self.batchimport ]
        self.logf = None # log file
        self.latelog = "" # log buffer for latecommit operations
        self.pathTemplates = None  # path templates
        self.totalsize = 0 # the size of all the files to register/check in bytes
        self.defaultcache = dict() # cache with default values
        self.cols = 80 # terminal columns (accurate where supported - Linux/Unix)

        #if CFG["regfile"]["default"] == "True":
        if CFG["regfile"].getboolean("default"):
            import textwrap as tw
            print(tw.fill(tw.dedent("""
                        The configuration file '{0}' didn't exist, so a default has been created!
                        That also means that a default location for the database '{1}' is being
                        used. Review and change the configuration if necessary! The requested
                        operation has been canceled. (This warning is displayed only once!)
                        """.format(CFGLOC, self.dbfile))
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
            #self.mm = dbmodel.Model(Register.DBFILE, self.dryrun)
            self.mm = dbmodel.Model(self.dbfile, self.dryrun)

        self.processfiles(thorough=dd[args.op][1])

        #if sys.platform == "linux" or sys.platform == "linux2":
        try:
            self.cols = int(os.popen('stty size', 'r').read().split()[1])
        except:
            pass

    def go(self, once=True):
        """
        just run the designed doperation
        """
        try:
            if self.dryrun:
                print("!!   D R Y   R U N   !!   D R Y   R U N   !!   D R Y   R U N   !!")
            if self.op:
                self.op()
        finally:
            if once:
                if self.latelog:
                    self.op = None
                    self.log(None)
                if self.logf:
                    self.logf.close()
                if self.mm:
                    self.mm.close()
            if self.dryrun:
                print("!!   D R Y   R U N   !!   D R Y   R U N   !!   D R Y   R U N   !!")

    def determineconfirm(self, args):
        """arguments take precedence over configuration, dry run disables any confirmation"""
        self.confirm = self.confirmproblem = False
        if args.dryrun:
            return
        if args.commit: # specified on command line
            cc = args.commit
        else: # get value from config instead
            cc = CFG["regfile"]["commit"]

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
        for ff in self.files:
            ii = ii + 1
            dupe = False
            cdir = os.path.dirname(ff) # directory
            sff = os.path.basename(ff) # short filename
            try:
                if cdir != pdir:
                    print("Directory [{}]".format(cdir))
                    pdir = cdir

                dbf = dbfile.DBFile(ff)
                if register: # group and comment
                    gr, com = self.getgroupcomment(ff)
                    if gr != pgr or com != pcom:
                        print("Using group:'{}' comment:'{}'".format(gr, com))
                        pgr, pcom = gr, com
                    dbf.group, dbf.comment = gr, com
                self.printstatus(ii, sff, "Quick")
                # stage 1 - silent
                ms = mysum.MySum(ff)
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
                        ms.stopnow = True
                        self.printstatus(ii, sff, "Interrupted")
                        #fail = fail+1
                        failfiles.append(ff + "    (Interrupted)")
                        tt.join()
                        #break
                        raise
                tt.join()
                #if ms.stopnow:
                #    print()
                #    break
                psize = psize + ms.size
                dbf.update(ms)
                dbfs = self.mm.querydata(dbf)
                if register:
                    if dbfs is None:
                        #self.mm.insert(dbf)
                        self.mm.insert(dbf, commit=False)
                        self.log(Register.LOGADD + dbf.logstr())
                        self.printstatus(ii, sff, "New entry " + str(dbf.idno))
                    else:
                        if dbf.match(dbfs[0], nametoo=True):
                            self.log(Register.LOGEXISTS + dbfs[0].logstr())
                            self.printstatus(ii, sff, "Already registered (full match) as " + str(dbfs[0].idno))
                        else:
                            self.log(Register.LOGEXISTS + dbf.logstr())
                            self.log(Register.LOGEXISTING + dbfs[0].logstr())
                            self.printstatus(ii, sff, "Already registered (data match) as " + str(dbfs[0].idno))
                        #fail = fail+1
                        failfiles.append(ff)
                else:
                    if dbfs is None:
                        self.printstatus(ii, sff, "FAIL")
                        #fail = fail+1
                        failfiles.append(ff)
                    else:
                        stat = "OK"
                        if dbfs[0].name.lower() != dbf.name.lower():
                            stat = "(as " + dbfs[0].name + ") OK"
                        stat = "id:" + str(dbfs[0].idno) + " " + stat
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
                print("Done.")
            else:
                self.latelog = ""
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
        for ff in self.files:
            ii = ii + 1
            cdir = os.path.dirname(ff) # directory
            sff = os.path.basename(ff) # short filename
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
                for line in fsum:
                    ll = ll + 1
                    self.printstatus(ii, ff, "L" + str(ll))
                    try:
                        ms = mysum.MySum.fromstring(line)
                    except ValueError:
                        self.printstatus(ii, ff, "not a MYSUM!")
                        print()
                        fail = True
                        break
                    self.printstatus(ii, ff, ms.filename + " L" + str(ll))

                    dbf = dbfile.DBFile.fromMySum(ms, gr, com)
                    if dbf in self.mm:
                        warn = warn + 1
                        dbfs = self.mm.querydata(dbf)
                        if dbf.match(dbfs[0], nametoo=True):
                            self.log(Register.LOGEXISTS + dbfs[0].logstr())
                            self.printstatus(ii, ff, "Already registered (full match) as {} L{}".format(dbfs[0].idno, ll))
                        else:
                            self.log(Register.LOGEXISTS + dbf.logstr())
                            self.log(Register.LOGEXISTING + dbfs[0].logstr())
                            self.printstatus(ii, ff, "Already registered (data match) as {} L{}".format(dbfs[0].idno, ll))
                        print()
                        continue
                    jj = jj + 1
                    self.mm.insert(dbf, commit=False)
                    self.log(Register.LOGADD + dbf.logstr())
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
                print()
        print(self.RULER)
        print("About to import {} entries ({} warnings) from {} files out of {}".format(jj, warn, len(self.files) - len(self.failfiles), len(self.files)))
        if len(failfiles) > 0:
            print("A list of files that failed:")
            for ff in failfiles:
                print("    " + ff)
        if self.docommit(failfiles):
            self.mm.commit()
            print("Done.")
        else:
            self.latelog = ""
            print("Aborted!")

    def setdata(self):
        """
        Change some details of the entries given by IDs. IDs are required.

        Only filename, comment and group can be changed.
        """
        ff = None
        if type(self.files) is list:
            if len(self.files) > 1:
                print("Please provide just one name or none ar all!")
                return
            elif len(self.files) == 1:
                ff = self.files[0]

        dbf = dbfile.DBFile(idno=self.idno, name=ff, group=self.group, comment=self.comment)
        self.log(Register.LOGUPDATE + dbf.logstr())
        dbf = self.mm.update(dbf)
        if not dbf:
            print("Error updating the entry!")
        else:
            self.log(Register.LOGUPDATED + dbf.logstr())

    def query(self):
        """
        Query the register for any entry matching the parameters.

        Only parts of the entry have to match the given parameters (ilike)
        """
        ff = None
        if type(self.files) is list:
            if len(self.files) > 1:
                print("Please provide just one name or none ar all!")
                return
            elif len(self.files) == 1:
                ff = self.files[0]

        dbf = dbfile.DBFile(idno=self.idno, name=ff, group=self.group, comment=self.comment)
        ll = self.mm.queryinfo(dbf)
        if ll == None:
            print("No record matches the query!")
        else:
            for dbf in ll:
                if self.queryasmysum:
                    print(mysum.MySum.fromdbfile(dbf).asstring())
                elif self.queryverbose:
                    print(dbf.prettystr(True))
                elif self.queryed2k:
                    print(dbf.ed2klink())
                else:
                    print(dbf.prettystr(False))

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
        self.mm = dbmodel.Model(self.dbfile, self.dryrun)
        with open(self.logfile, "r") as self.logf:
            for ll in self.logf:
                if ll.startswith(Register.LOGADD):
                    dbf = dbfile.DBFile.fromlogstr(ll[len(Register.LOGADD):])
                    self.mm.insert(dbf, commit=False)
                elif ll.startswith(Register.LOGUPDATED):
                    #dbf = dbfile.DBFile.fromlogstr(ll[len(Register.LOGUPDATE):])
                    dbf = dbfile.DBFile.fromlogstr(ll[len(Register.LOGUPDATED):])
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
        if self.op in self.oplatecommit and not self.dryrun:
            self.latelog += line + "\n"
            return # store for later, just set op to something safe and call this again
        if self.dryrun and line:
            line = "#DRYRUN " + line
        if not self.logf:
            self.logfile = os.path.expanduser(self.logfile)
            if not os.path.exists(self.logfile):
                self.logf = open(self.logfile, "w")
            else:
                self.logf = open(self.logfile, "a")
            self.logf.write("# "+datetime.datetime.now().ctime()+"\n")
        if self.latelog:
            self.logf.write(self.latelog)
            self.latelog = ""
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
        pgs = ms.pgs
        size = ms.size
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
        if type(self.files) is str:
            self.files = [ self.files ]
        elif self.files is None:
            return
        elif not type(self.files) is list:
            print(self.files, type(self.files))
            raise ValueError("The files is not a list nor a string")

        if not thorough:
            return

        rf = [] # real files
        ts = 0 # total size
        for ff in self.files:
            # the file could be: a file, a directory (then add everything recursively), or a wildcard
            ff = os.path.expanduser(ff)

            if os.path.exists(ff) and os.path.isdir(ff):
                matches = []
                for root, dirnames, filenames in os.walk(ff):
                    for filename in fnmatch.filter(filenames, '*'):
                        fn = os.path.join(root, filename)
                        ts = ts + os.stat(fn)[6]
                        rf.append(fn)
            else:
                root = os.getcwd()
                for fn in glob.iglob(ff):
                    fn = os.path.join(root, fn)
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
        with open(self.DEFAULTFILES[0], "w") as f: pass
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
                self.pathTemplates = PathTemplates.fromConfig(CFG["regfile"]["pathtemplates"])

            gr, com = self.pathTemplates.apply(ff, self.group, self.comment, gr, com, imp)

        return (gr,com)

def runop(args):
    Register(args).go()

if __name__ == "__main__":
    print("This is a library, please run regfile. (There's no unittest yet.)")
