#!/usr/bin/env python

"""
MYSUM is a custom made format of storing hash values of files
It goes like this: [MYSUM:FILENAME|SIZE|MD5|MD51|E2DK]
where:
    MD5 is the md5 of the whole file
    MD51 is the md5 of the first megabyte (1024*1024 bytes)
    ED2K is the edonkey 2000 hash sum  (and crucial part of the ed2k link)
"""

import sys
import os
import os.path
import hashlib
import io

class MySum(object):
    """
    provides means to compute sums of a file and store it in a nice string
    """

    def __init__(self, filename, data=None):
        self.state = 0 # 0 - just the filename ; 1 - size, md51 ; 2 - the whole thing
        self.fullfilename = filename
        if type(self.fullfilename) is str:
            self.filename = os.path.basename(filename)
        else:
            self.filename = self.fullfilename
        self.size = None
        self.md1 = None
        self.md5 = None
        self.ed2k = None
        self.pgs = None # here be total size read
        self.stopnow = False

        # if filename == None or empty use data instead of file content
        if data != None and type(data) != bytes:
            raise ValueError("Provided data must be a bytes object!")
        self.data = data

    @staticmethod
    def fromdbfile(dbfile):
        ms = MySum(dbfile.name)
        ms.size = dbfile.size
        ms.md1 = dbfile.md1
        ms.md5 = dbfile.md5
        ms.ed2k = dbfile.ed2k
        ms.state = 2
        ms.fullfilename = ""
        return ms

    @staticmethod
    def fromstring(sumstr):
        """
        Turn a string of format [MYSUM:FILENAME|SIZE|MD5|MD51|E2DK] to MySum object
        """
        if sumstr[-1] == "\n": # imported sumstrings may come with eol character, strip it
            sumstr = sumstr[:-1]
        # routine checks
        if sumstr[0:7] != "[MYSUM:" or sumstr[-1] != "]" or sumstr[-34] != "|" or sumstr[-67] != "|" or sumstr[-100] != "|" or not "|" in sumstr[7:-100]:

            raise ValueError("{} isnt a MySum string".format(sumstr))
        sumstr = sumstr[7:-1].split('|')

        mysum = MySum(sumstr[0])
        mysum.state = 2
        mysum.size = int(sumstr[1])
        mysum.md5 = sumstr[2]
        mysum.md1 = sumstr[3]
        mysum.ed2k = sumstr[4]
        return mysum

    def asstring(self):
        return("[MYSUM:{}|{}|{}|{}|{}]".format(self.filename, self.size, self.md5, self.md1, self.ed2k))

    def upgrade(self, target=-1):
        """
        target is the target state, if not provided next state is assumed

        """
        if target == -1:
            target = self.state + 1
            if target == 3:
                target = 2

        if target == 0:
            return
        elif target == 1:
            self.getsizemd51()
        elif target == 2:
            self.getmd5ed2k()
        else:
            raise ValueError("Invalid target state " + target)

    def getsizemd51(self):
        """
        get size amd md5 hash of the first megabyte
        """
        if self.state > 1:
            return

        usedata = self.fullfilename == None or self.fullfilename == ""
        if not usedata and not os.path.exists(self.fullfilename):
            raise Exception("File " + self.filename + " doesn't exist!")

        # md51 & size
        if usedata:
            self.size = len(self.data)
            f = io.BytesIO(self.data)
        else:
            self.size = os.stat(self.fullfilename)[6]
            f = open(self.fullfilename, "rb")
        m5 = hashlib.md5() # md5 master object
        buf = f.read(1024*1024)
        m5.update(buf)
        self.md1 = m5.hexdigest()
        f.close()

        self.state = 1

    def getmd5ed2k(self):
        """
        get md5 hash and ed2k hash (hash of md4 hashes of parts)
        """
        # this is the size of the part in ed2k
        PARTSIZE=9728000

        if self.state == 0:
            self.getsizemd51()
        if self.state == 2:
            return

        usedata = self.fullfilename == None or self.fullfilename == ""
        if not usedata and not os.path.exists(self.fullfilename):
            raise Exception("File " + self.fullfilename + " doesn't exist!")

        if usedata:
            f = io.BytesIO(self.data)
        else:
            f = open(self.fullfilename, "rb")

        self.pgs = 0

        m4 = hashlib.new("md4") # md4 master object
        m5 = hashlib.md5() # md5 master object
        ht = bytes() # hash total
        ht1 = "" # hash of the first PARTSIZE
        buffull = False # the last buffer was read completely
        # part hashes
        while 1:
            if self.stopnow:
                f.close()
                return
            # ed2k is a hash of a string comprised of all the md4 hashes
            # of all the parts (PARTSIZE bytes long) of the file
            # this is the first part - construting the string of hashes ht1
            m = m4.copy()
            buf = f.read(PARTSIZE)
            if not buf: break
            if len(buf) == PARTSIZE:
                buffull = True
            else:
                buffull = False
            m.update(buf)
            ht += m.digest()
            if ht1 == "":
                ht1 = m.hexdigest()
            m5.update(buf)
            self.pgs = self.pgs + PARTSIZE
        # compute output
        # The following is somewhat confusing: if the size of the file is exactly N*PARTSIZE bytes
        # a hash of an empty buffer must be appended, but only if N != 1
        if buffull:
            m = m4.copy()
            buf = bytes([])
            m.update(buf)
            ht += m.digest()
        self.ed2k = ""
        if len(ht) == 16:
            self.ed2k = ht1
        else:
            m = m4.copy()
            m.update(ht)
            self.ed2k = m.hexdigest()
        self.md5 = m5.hexdigest()
        f.close()

        self.state = 2

if __name__ == "__main__":
    import random
    print("MySum unittest")
    print("Generating random sample data (always the same) ...")
    random.seed(0)
    b = bytes(random.randint(0, 255) for i in range(1024*1024))
    b = bytes().join(b for i in range(64))
    print("{} bytes generated.".format(len(b)))

    # this is an array of size, md5, md1, e2dk - size is the input, the rest is the valid output
    ltest = [ \
            [0,"d41d8cd98f00b204e9800998ecf8427e","d41d8cd98f00b204e9800998ecf8427e","31d6cfe0d16ae931b73c59d7e0c089c0"], \
            [9728000, "ce3cd52a835724497f650257b66ea2f1","7684306b69a563fd5db77311d4a15fdd","3cbc0bbaacc8fac677a7032579eda4a2"], \
            [19456000, "9cd33d3c799676733466c1ac19d9b565","7684306b69a563fd5db77311d4a15fdd","a119aaeb87f8fc56cedc4e33b788aeab"], \
            [38912000, "97ffedd10feb9df932e5c089ee52d7ba","7684306b69a563fd5db77311d4a15fdd","fdf2ef87ac2b6f69c20a897397690067"], \
            [67108864, "01dde5d665fb2ed685ffe50d231ae263", "7684306b69a563fd5db77311d4a15fdd", "175cefe7b23344274adf476201340743"], \
            ]

    rt = True
    for test in ltest:
        print("Testing data size {:12} ...     ".format(test[0]), end='')
        mm = MySum(None,b[0:test[0]])
        mm.upgrade(2)
        r = [mm.md5 == test[1], mm.md1 == test[2], mm.ed2k == test[3]]
        rt = rt and r[0] and r[1] and r[2]
        print("MD5 {}  ".format("OK" if r[0] else "FAIL" ), end='')
        print("MD1 {}  ".format("OK" if r[1] else "FAIL" ), end='')
        print("ED2K {}  ".format("OK" if r[2] else "FAIL" ), end='')
        print()

    if rt:
        print("All OK")
    else:
        print("MySum unittest failed!")

    #ff = open("./randdata", "wb")
    #ff.write(b)
    #ff.close()
