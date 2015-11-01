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

    @staticmethod
    def fromMySum(ms, group, comment):
        return DBFile(ms.fileName, group, comment, ms.fileSize, ms.md1, ms.md5, ms.ed2k)
