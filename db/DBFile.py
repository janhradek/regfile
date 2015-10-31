import sqlalchemy
import sqlalchemy.orm

from .DBBase import DBBase

class DBFile(DBBase):
    __tablename__ = "file"

    fileId = sqlalchemy.Column(name = 'idno', type_ = sqlalchemy.Integer, primary_key = True)

    # info data
    fileName = sqlalchemy.Column(name = 'name', type_ = sqlalchemy.String)
    group = sqlalchemy.Column(sqlalchemy.String)
    comment = sqlalchemy.Column(sqlalchemy.String)

    # hash data
    fileSize = sqlalchemy.Column(name = 'size', type_ = sqlalchemy.Integer)
    md1 = sqlalchemy.Column(sqlalchemy.String)
    md5 = sqlalchemy.Column(sqlalchemy.String)
    ed2k = sqlalchemy.Column(sqlalchemy.String)

    logre = None

    def __init__(self, fileName=None, group=None, comment=None, fileSize=None, md1=None, md5=None, ed2k=None, fileId=None):
        if fileId == 0:
            fileId = None
        self.fileName, self.group, self.comment, self.fileSize, self.md1, self.md5, self.ed2k, self.fileId = \
            fileName, group, comment, fileSize, md1, md5, ed2k, fileId

    def prettystr(self, verbose):
        ss = "[{:5d}] '{}' s:{}\n".format(self.fileId, self.fileName, self.fileSize)
        if self.group != None:
            ss = ss + "{:7} g:{}\n".format("", self.group)
        if self.comment != None:
            ss = ss + "{:7} c:{}\n".format("", self.comment)
        if verbose:
            ss = ss + "{:7} md1:{}  md5:{}  ed2k:{}\n".format("", self.md1, self.md5, self.ed2k)
        return ss

    def ed2klink(self):
        """return ed2k link"""
        # ed2k://|file|register.py|25201|2e8949873370c9af2fc8c1a1e01d83ec|/
        return "ed2k://|file|{}|{}|{}|/".format(self.fileName, self.fileSize, self.ed2k)

    def logstr(self):
        fileId = 0 if self.fileId is None else int(self.fileId)
        return "DBF{:06d}|n:{}|g:{}|c:{}|s:{}|md1:{}|md5:{}|ed2k:{}|".format(fileId, self.fileName, \
                self.group if self.group else "", \
                self.comment if self.comment else "", \
                self.fileSize, self.md1, self.md5, self.ed2k)

    @staticmethod
    def fromlogstr(ls):
        import re
        if DBFile.logre == None:
            DBFile.logre = re.compile(r"^DBF(\d*)\|n:(.*)\|g:(.*)\|c:(.*)\|s:(.*)\|md1:(.*)\|md5:(.*)\|ed2k:(.*)\|$")
        rr = DBFile.logre.match(ls)
        if not rr:
            raise ValueError("The string " + ls + " doesnt match the logline!")
        dbf = DBFile(rr.group(2),rr.group(3),rr.group(4),rr.group(5),rr.group(6),rr.group(7),rr.group(8),int(rr.group(1)))
        if dbf.logstr().strip() != ls.strip():
            print(dbf.logstr().strip())
            print(ls.strip())
        return dbf

    def update(self, ms):
        """
        update from mysum

        only items with valid (not None) values will be updated
        work by the state
        """
        self.fileName = ms.fileName
        if ms.state >= 1:
            self.fileSize = ms.fileSize
            self.md1 = ms.md1
        if ms.state == 2:
            self.md5 = ms.md5
            self.ed2k = ms.ed2k

    def match(self, other, nametoo=False):
        rr = False
        if not type(self.fileSize) is int:
            raise TypeError("dbfile.fileSize must be an int! (self)")
        if not type(other.fileSize) is int:
            raise TypeError("dbfile.fileSize must be an int! (other)")

        if self.fileSize == other.fileSize and self.md1 == other.md1 and self.md5 == other.md5 and self.ed2k == other.ed2k:
            rr = True
        if nametoo and self.fileName != other.fileName:
            rr = False
        return rr


    @staticmethod
    def fromMySum(ms, group, comment):
        return DBFile(ms.fileName, group, comment, ms.fileSize, ms.md1, ms.md5, ms.ed2k)


