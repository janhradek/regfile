"""
implements the handling of the config file

config file is always in ~/.regfile - CFGLOC
configuration instance is stored in CFG

configuration contains only one section - [regfile]
configuration values:
    db - location of the database file (default: ~/dbfile.sqlite)
    log - location of the log file (default: ~/dbfile.log)
    commit - either "auto", "confirm" or "problem" (default: auto)

commit specifies when and how to commit changes to db:
    auto - always commit all the changes immediately
    confirm - always confirm any changes to be commited
    problem - confirm changes only in case of a problem
"""
import configparser

import os.path

CFGLOC = "~/.regfile"
CFGLOC = os.path.expanduser(CFGLOC)

CFG = configparser.ConfigParser()
CFG["regfile"] = {
    "db" : "~/dbfile.sqlite", # location of the database
    "log" : "~/dbfile.log" , # location of the logfile
    "commit" : "auto" , # other values may be: confirm, problem
    "autovalues" : "", # an autovalues configuration array
    }

def readcfg():
    global CFG

    if not os.path.exists(CFGLOC) or not os.path.isfile(CFGLOC):
        if not os.path.exists(CFGLOC): # really doesnt exist
            with open(CFGLOC, 'w') as cf:
                CFG.write(cf)
        CFG["regfile"]["default"] = "True"
    else:
        CFG.read(CFGLOC)
        CFG["regfile"]["default"] = "False"

    # sanitize value
    CFG["regfile"]["db"] = os.path.expanduser(CFG["regfile"]["db"])
    CFG["regfile"]["log"] = os.path.expanduser(CFG["regfile"]["log"])
    CFG["regfile"]["commit"] = CFG["regfile"]["commit"].strip().lower()

    if not CFG["regfile"]["commit"] in ["auto", "confirm", "problem"]:
        raise ValueError("Unknown entry commit={} in config {}".format(CFG["regfile"]["commit"], CFGLOC))

def cfgvaltolistlist(val, extend=False, strip=False):
    """a,b,c, \\n d,e,f -> [ [a, b, c] , [d,e,f] ] (extend: [ a,b,c,d,e,f ] )"""
    ll = []
    import csv
    for cc in val.split("\n"): # by end of lines
        cc = cc.strip()
        if cc.endswith(","): # remove last comma if present
            cc = cc[:-1]
        llcsv = csv.reader([cc], skipinitialspace=True)
        if strip:
            llcsv = [x for x in llcsv.__next__() if x.strip()] #list(llcsv)[0]
        else:
            llcsv = [x for x in llcsv.__next__()]
        if not extend:
            ll.append(llcsv)
        else:
            ll.extend(llcsv)
    return ll

readcfg()
