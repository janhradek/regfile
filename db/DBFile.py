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
        if (not isinstance(self.fileSize, int)):
            raise TypeError("dbfile.fileSize must be an int! (self)")
        if (not isinstance(other.fileSize, int)):
            raise TypeError("dbfile.fileSize must be an int! (other)")

        if self.fileSize == other.fileSize and self.md1 == other.md1 and self.md5 == other.md5 and self.ed2k == other.ed2k:
            rr = True
        if nametoo and self.fileName != other.fileName:
            rr = False
        return rr


    @staticmethod
    def fromMySum(ms, group, comment):
        return DBFile(ms.fileName, group, comment, ms.fileSize, ms.md1, ms.md5, ms.ed2k)
