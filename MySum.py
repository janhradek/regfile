#!/usr/bin/env python
##
## mysum.py
##      - MYSUM is a custom made format for storing checksums of files.
##        Its string representation is: [MYSUM:FILENAME|SIZE|MD5|MD51|E2DK]
##        where:
##            MD5 is the MD5 of the whole file
##            MD51 is the MD5 of the first megabyte (1024*1024 bytes)
##            ED2K is the EDonkey 2000 hash sum (and crucial part of the ED2K
##              link)
##


# import of required modules {{{
import functools
import hashlib
import io
import os
import re
# }}}

# class MySum() {{{
class MySum(object):
    # DOC {{{
    """MYSUM is a custom made format for storing checksums of files. Its string
    representation is: [MYSUM:FILENAME|SIZE|MD5|MD51|E2DK]
    where:
        MD5 is the MD5 of the whole file
        MD51 is the MD5 of the first megabyte (1024*1024 bytes)
        ED2K is the EDonkey 2000 hash sum  (and crucial part of the ED2K
          link)
    """
    # }}}


    # STATIC VARIABLES {{{
    # MySum states {{{
    STATE_INITIALIZED   = 0 # MySum has only assigned file (a filename or a stream)
    STATE_SIZE_MD1      = 1 # size and MD5 of the first MB is determined
    STATE_COMPLETE      = 2 # MD5 and ED2K of the whole file is determined
    # }}}

    # the size of one part in ED2K sum
    # NOTE: ED2K is the MD4 of a string comprised of MD4 hashes of all the parts of the file
    ED2K_PART_SIZE      = 9728000

    # the format string of the string representation of MySum
    STRING_FORMAT       = "[MYSUM:{fileName}|{fileSize}|{md5}|{md1}|{ed2k}]"

    # regular expression to parse MySum string format {{{
    STRING_RE           = re.compile(
        r"\[MYSUM:" +
        r"(?P<file_>[^|]+)\|" +
        r"(?P<fileSize>\d+)\|" +
        r"(?P<md5>\w{32})\|" +
        r"(?P<md1>\w{32})\|" +
        r"(?P<ed2k>\w{32})\]"
    )
    # }}}
    # }}}


    # METHODS {{{
    def __init__(self, file_, fileSize = None, md1 = None, md5 = None, ed2k = None):
        # DOC {{{
        """Initializes an instance of MySum and stores the parameters. The
        state of the MySum is determined based on the arguments specified.

        Parameters

            file_ -- either the full path of the file or a readable and
                seekable stream-like object

            fileSize -- (optional) the fileSize of the file, if not specified it will
                be determined

            md1 -- (optional) the MD5 sum of the first megabyte of the file, if
                not specified it will be determined

            md5 -- (optional) the MD5 sum of the entire file, if not specified
                it will be determined

            ed2k -- (optional) the ED2K sum of the entire file, if not
                specified it will be determined
        """
        # }}}

        # CODE {{{
        # check that the file is either a string (with full path to the file) or
        # something like a stream object (having read and seek methods)
        assert (isinstance(file_, str) or (hasattr(file_, "read") and hasattr(file_, "seek")))

        # store the parameters {{{
        self.file_          = file_
        self.fileSize       = fileSize
        self.md1            = md1
        self.md5            = md5
        self.ed2k           = ed2k
         # }}}

        # initialize the rest of the attributes {{{
        # allows to stop the lenghty upgrade to the STATE_COMPLETE
        self._stopRequested  = False

        # number of bytes processed during the upgrade to the STATE_COMPLETE
        self.processedSize  = 0

        # the state of MySum (one of STATE_XX)
        self.state          = None
        # }}}

        # automatically determine the state from the set values
        self._determineStateFromAttributes()
        # }}}


    @staticmethod
    def fromString(mySumString):
        # DOC {{{
        """Turn a string in the MySum format to an instance of the MySum.
        """
        # }}}

        # CODE {{{
        # try to match the specified MySum string with the parsing regexp
        match = MySum.STRING_RE.match(mySumString.strip())

        # raise an exception if the string did not match {{{
        if (match is None):
            raise ValueError("{} is not a MySum string".format(mySumString))
        # }}}

        # get the matched groups as a dict
        matchGroups = match.groupdict()

        # convert the size in the dict to an integer
        matchGroups['fileSize'] = int(matchGroups['fileSize'])

        # create and return the MySum
        return MySum(**matchGroups)
        # }}}


    @property
    def fileName(self):
        # DOC {{{
        """Returns either a short filename of the associated file or a generic
        string indicating that the file is provided as an opened file like
        object.
        """
        # }}}

        # CODE {{{
        # return the basename of the full file path if the file is specified as a path {{{
        if (isinstance(self.file_, str)):
            return os.path.basename(self.file_)
        # }}}
        # otherwise return a generic string {{{
        else:
            return "<DATA>"
        # }}}
        # }}}


    @property
    def _fileIsStream(self):
        # DOC {{{
        """Returns True if the associated file is a stream.
        """
        # }}}

        # CODE {{{
        return (not isinstance(self.file_, str))
        # }}}


    def _determineStateFromAttributes(self):
        # DOC {{{
        """Determines the state of MySum from sum attributes.
        """
        # }}}

        # CODE {{{
        # weight each attribute differently (power of 2, like bits) {{{
        weightedAttributes = (
            (self.fileSize, 1),
            (self.md1,      2),
            (self.md5,      4),
            (self.ed2k,     8),
        )
        # }}}

        def addWeightIfNotNone(totalWeight, item):
            # DOC {{{
            """A utility function to add up weights of attributes if the
            attribute is set.

            Parameters

                totalWeight -- total accumulated weight of set attributes so
                    far

                item -- a tuple containing the attributes value and weight
            """
            # }}}

            # CODE {{{
            # unpack the item to the value of the attribute and its weight
            value, weight = item

            # add the weight to the total if the value is not None {{{
            if (value is not None):
                totalWeight += weight
            # }}}

            # return the total weight
            return totalWeight
            # }}}

        # determine the total weight of the set attributes
        totalWeight = functools.reduce(addWeightIfNotNone, weightedAttributes, 0)

        # set the state to 'initialized' if none of the sums nor the size is set {{{
        if (totalWeight == 0):
            self.state = MySum.STATE_INITIALIZED
        # }}}
        # or set the state to 'first mega' if only the size and the MD5 of the first mega is set {{{
        elif (totalWeight == 3):
            self.state = MySum.STATE_SIZE_MD1
        # }}}
        # or set the state to 'complete' if all sums and the size are not None {{{
        elif (totalWeight == 15):
            self.state = MySum.STATE_COMPLETE
        # }}}
        # otherwise raise an exception {{{
        else:
            raise ValueError("Unable to determine the state of MySum {0.fileName} " +
                             "with size:{0.size}, MD5(1MB):{0.md1}, MD5:{0.md5}, " +
                             "ED2K:{0.ed2k}".format(self))
        # }}}
        # }}}


    def upgrade(self, targetState=None):
        # DOC {{{
        """Upgrades the state of MySum to the next level orb to the specified
        target state.

        Parameters

            targetState -- (optional) target state to upgrade to. It must be
                higher than the current state if specified.
        """
        # }}}

        # CODE {{{
        # return if MySum is already complete {{{
        if (self.state == MySum.STATE_COMPLETE):
            return
        # }}}

        # determine the target state if it was not given (the next state) {{{
        if (targetState is None):
            targetState = self.state + 1
        # }}}

        # raise an error if an unknwon state is requested {{{
        if ((targetState < MySum.STATE_INITIALIZED) or
            (targetState > MySum.STATE_COMPLETE)):
            raise ValueError("Invalid target state " + targetState)
        # }}}

        # go over the known states and upgrade to them if necessary {{{
        for state, upgrader in ((MySum.STATE_SIZE_MD1, self.determineSizeAndMD1,),
                                (MySum.STATE_COMPLETE, self.determineMD5AndED2K,),):
            if ((targetState >= state) and (self.state < state)):
                upgrader()
        # }}}
        # }}}


    def determineSizeAndMD1(self):
        # DOC {{{
        """Determines the size and MD5 hash of the first megabyte.
        """
        # }}}

        # CODE {{{
        # return if the size and the MD5 hash of the first megabyte have been already determined {{{
        if (self.state >= MySum.STATE_SIZE_MD1):
            return
        # }}}

        # use seek to determine the size if the file is given as a stream {{{
        if (self._fileIsStream):
            # the stream is the file
            stream = self.file_

            # seek to the end of the stream
            stream.seek(0, os.SEEK_END)

            # get the size of the stream
            self.fileSize = stream.tell()

            # rewind the stream
            # NOTE: this might not work depending on the type of the stream
            stream.seek(0)

            # make sure the stream has been rewound
            assert (stream.tell() == 0)
        # }}}
        # otherwise determine the size of the file via system and open it {{{
        else:
            # determine the size of the file
            self.fileSize = os.stat(self.file_)[6]

            # open the file for reading (bytes)
            stream = open(self.file_, "rb")
        # }}}

        # try to determine the MD5 of the first megabyte of the file {{{
        try:
            # intialize the MD5 hasher
            md5Hasher = hashlib.md5()

            # read 1 MB from the stream into a buffer
            firstMega = stream.read(1024*1024)

            # compute the MD5 of the first megabyte
            md5Hasher.update(firstMega)

            # get the hex digest of the MD5 sum of the first megabyte
            self.md1 = md5Hasher.hexdigest()
        # }}}
        # always close the file if it was opened here {{{
        finally:
            if (not self._fileIsStream):
                stream.close()
        # }}}

        # set the new state
        self.state = MySum.STATE_SIZE_MD1
        # }}}


    def determineMD5AndED2K(self, progressCallback=None):
        # DOC {{{
        """Determines MD5 and ED2K sums of the entire file.

        Parameters

            progressCallback -- (optional) a function with a single parameter
                to use to report progress of the determination. The single
                parameter is the number of processed bytes so far.
        """
        # }}}

        # CODE {{{
        # determine MD5 of the first megabyte and size if it was not yet done {{{
        if (self.state == MySum.STATE_INITIALIZED):
            self.determineSizeAndMD1()
        # }}}
        # return if MySum is already complete {{{
        elif (self.state == MySum.STATE_COMPLETE):
            return
        # }}}

        # if the stream is the already in the file_ attribute, pick it and rewind it {{{
        if (self._fileIsStream):
            # the stream is the file
            stream = self.file_

            # rewind the stream
            stream.seek(0)

            # make sure the stream has been rewound
            assert(stream.tell() == 0)
        # }}}
        # otherwise open the file {{{
        else:
            stream = open(self.file_, "rb")
        # }}}

        # try to determine the MD5 and ED2K sums of the entire file {{{
        try:
            # reset the processedSize
            self.processedSize  = 0

            # initialize a prototype of the MD4 hasher for ED2K checksum
            md4HasherPrototype  = hashlib.new("md4")

            # initalize the MD5 hasher
            md5Hasher           = hashlib.md5()

            # initialize concatenated MD4 hashes of the file parts
            md4PartsDigests     = bytes()

            # MD4 hash of the first part
            md4FirstPartDigest  = None

            # mark whether the last part read has the ED2K_PART_SIZE
            partFull            = False

            # determine MD5 hash of the entire file and MD4 hashes of parts {{{
            while 1:
                # return immediately if stop has been requested {{{
                if self._stopRequested:
                    return
                # }}}

                # create an MD4 hasher from the prototype
                md4Hasher = md4HasherPrototype.copy()

                # read a part from the file
                # TODO: read smaller amounts of data
                part = stream.read(MySum.ED2K_PART_SIZE)

                # stop if the part is empty {{{
                if (not part):
                    break
                # }}}

                # determine whether the part is full
                partFull = (len(part) == MySum.ED2K_PART_SIZE)

                # compute the MD4 hash of the part
                md4Hasher.update(part)

                # add the MD4 hash to other MD4 part digests
                md4PartsDigests += md4Hasher.digest()

                # set the first part digest if it is not yet set {{{
                if (md4FirstPartDigest is None):
                    md4FirstPartDigest = md4Hasher.hexdigest()
                # }}}

                # update the MD5 hash of the file
                md5Hasher.update(part)

                # increase the processed size by the part size
                self.processedSize += len(part)

                # report the progress using the call back if it is specified {{{
                if (progressCallback):
                    progressCallback(self.processedSize)
                # }}}
            # }}}

            # If the size of the file is exactly N*ED2K_PART_SIZE bytes
            # a hash of an empty buffer must be appended, but only if N != 1 {{{
            if (partFull):
                # create an MD4 hasher from the prototype
                md4Hasher = md4HasherPrototype.copy()

                # define an empty part
                emptyPart = bytes([])

                # compute MD4 hash of an empty part
                md4Hasher.update(emptyPart)

                # add the MD4 hash of an empty part to the other MD4 part digests
                md4PartsDigests += md4Hasher.digest()
            # }}}

            # if the file has only one part, use the MD4 of the first part as ED2K sum {{{
            if (len(md4PartsDigests) == 16):
                self.ed2k = md4FirstPartDigest
            # }}}
            # otherwise compute the MD4 hash of all parts' MD4 hash digests {{{
            else:
                # create an MD4 hasher from the prototype
                m = md4Hasher.copy()

                # compute the MD4 hash of all parts' MD4  hash digests
                m.update(md4PartsDigests)

                # get the hex digest as the ED2K sum
                self.ed2k = m.hexdigest()
            # }}}

            # get the MD5 hex digest as the MD5 sum
            self.md5 = md5Hasher.hexdigest()
        # }}}
        # always close the file if it was opened here {{{
        finally:
            if (not self._fileIsStream):
                stream.close()
        # }}}

        # set the new state
        self.state = MySum.STATE_COMPLETE
        # }}}


    def requestStop(self):
        # DOC {{{
        """Requests stop of the determination of the MD5 and the ED2K
        checksums.
        """
        # }}}

        # CODE {{{
        self._stopRequested = True
        # }}}


    def __eq__(self, other):
        # DOC {{{
        """Equality operator. All sums, (short) filename and size must match.
        """
        # }}}

        # CODE {{{
        return ((self.fileName == other.fileName) and
                (self.fileSize == other.fileSize) and
                (self.md1 == other.md1) and
                (self.md5 == other.md5) and
                (self.ed2k == other.ed2k))
        # }}}


    def __str__(self):
        # DOC {{{
        """Returns the MySum string format representation of this instance.
        """
        # }}}

        # CODE {{{
        return MySum.format(self.fileName, self.fileSize, self.md5, self.md1, self.ed2k)
        # }}}


    @staticmethod
    def format(fileName, fileSize, md5, md1, ed2k):
        # DOC {{{
        """Returns the MySum string format representation of MySum represented
        by the parameters.

        Parameters

            fileName -- the name of the file

            fileSize --  the fileSize of the file

            md1 --  the MD5 sum of the first megabyte of the file

            md5 --  the MD5 sum of the entire file

            ed2k --  the ED2K sum of the entire file
        """
        # }}}

        # CODE {{{
        return MySum.STRING_FORMAT.format(**locals())
        # }}}


    # }}}
# }}}


if (__name__ == "__main__"):
    import random
    print("MySum unittest")
    print("Generating random sample data (always the same, may take some time) ...")
    random.seed(0)
    b = bytes(random.randint(0, 255) for i in range(1024*1024))
    b = bytes().join(b for i in range(64))
    print("{} bytes generated.".format(len(b)))

    # this is an array of size, md5, md1, e2dk - size is the input, the rest is the valid output
    ltest = [
        [0,         "d41d8cd98f00b204e9800998ecf8427e", "d41d8cd98f00b204e9800998ecf8427e", "31d6cfe0d16ae931b73c59d7e0c089c0"],
        [9728000,   "ce3cd52a835724497f650257b66ea2f1", "7684306b69a563fd5db77311d4a15fdd", "3cbc0bbaacc8fac677a7032579eda4a2"],
        [19456000,  "9cd33d3c799676733466c1ac19d9b565", "7684306b69a563fd5db77311d4a15fdd", "a119aaeb87f8fc56cedc4e33b788aeab"],
        [38912000,  "97ffedd10feb9df932e5c089ee52d7ba", "7684306b69a563fd5db77311d4a15fdd", "fdf2ef87ac2b6f69c20a897397690067"],
        [67108864,  "01dde5d665fb2ed685ffe50d231ae263", "7684306b69a563fd5db77311d4a15fdd", "175cefe7b23344274adf476201340743"],
    ]

    rt = True
    for test in ltest:
        print("Testing data size {:12} ...     ".format(test[0]), end='')
        mm = MySum(io.BytesIO(b[0:test[0]]))
        mm.upgrade(MySum.STATE_COMPLETE)
        mm2 = MySum.fromString(str(mm))
        r = [mm.size == test[0], mm.md5 == test[1], mm.md1 == test[2], mm.ed2k == test[3]]
        rt = (rt and r[0] and r[1] and r[2] and r[3])
        print("SIZE {}  ".format("OK" if r[0] else "FAIL" ), end='')
        print("MD5 {}  ".format("OK" if r[1] else "FAIL" ), end='')
        print("MD1 {}  ".format("OK" if r[2] else "FAIL" ), end='')
        print("ED2K {}  ".format("OK" if r[3] else "FAIL" ), end='')
        print("STRING {}".format("OK" if (mm2 == mm) else "FAIL"), end='')
        print()

    if rt:
        print("All OK")
    else:
        print("MySum unittest failed!")
