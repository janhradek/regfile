import sqlalchemy
import sqlalchemy.orm

import dbbase

class DBFile(dbbase.Base):
    __tablename__ = "file"

    idno = sqlalchemy.Column(sqlalchemy.Integer, primary_key = True)

    # info data
    name = sqlalchemy.Column(sqlalchemy.String)
    group = sqlalchemy.Column(sqlalchemy.String)
    comment = sqlalchemy.Column(sqlalchemy.String)

    # hash data
    size = sqlalchemy.Column(sqlalchemy.Integer)
    md1 = sqlalchemy.Column(sqlalchemy.String)
    md5 = sqlalchemy.Column(sqlalchemy.String)
    ed2k = sqlalchemy.Column(sqlalchemy.String)

    logre = None

    def __init__(self, name=None, group=None, comment=None, size=None, md1=None, md5=None, ed2k=None, idno=None):
        if idno == 0:
            idno = None
        self.name, self.group, self.comment, self.size, self.md1, self.md5, self.ed2k, self.idno = \
            name, group, comment, size, md1, md5, ed2k, idno

    def prettystr(self, verbose):
        ss = "[{:5d}] '{}' s:{}\n".format(self.idno, self.name, self.size)
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
        return "ed2k://|file|{}|{}|{}|/".format(name, size, ed2k)

    def logstr(self):
        idno = 0 if self.idno is None else int(self.idno)
        return "DBF{:06d}|n:{}|g:{}|c:{}|s:{}|md1:{}|md5:{}|ed2k:{}|".format(idno, self.name, \
                self.group if self.group else "", \
                self.comment if self.comment else "", \
                self.size, self.md1, self.md5, self.ed2k)

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
        self.name = ms.fileName
        if ms.state >= 1:
            self.size = ms.size
            self.md1 = ms.md1
        if ms.state == 2:
            self.md5 = ms.md5
            self.ed2k = ms.ed2k

    def match(self, other, nametoo=False):
        rr = False
        sizematch = False
        if not type(self.size) is int:
            raise TypeError("dbfile.size must be an int! (self)")
        if not type(other.size) is int:
            raise TypeError("dbfile.size must be an int! (other)")

        if self.size == other.size and self.md1 == other.md1 and self.md5 == other.md5 and self.ed2k == other.ed2k:
            rr = True
        if nametoo and self.name != other.name:
            rr = False
        return rr


    @staticmethod
    def fromMySum(ms, group, comment):
        return DBFile(ms.filename, group, comment, ms.size, ms.md1, ms.md5, ms.ed2k)


