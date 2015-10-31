import os
import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.sql.expression

from .DBBase import DBBase
from .DBFile import DBFile

class DBModel(object):
    def __init__(self, dbfile):
        '''
        (constructor) initialize the mode
        dbfile is optional
        '''
        self.SessionMaker = None
        self.session = None
        self.engine = None

        self.init(dbfile)


    def init(self,dbfile, echoSQLCommands = False):
        '''
        Initialize the Model
        '''
        self.close()
        #if dbfile==None:
        # default location for the lst (sqlite) ~/ViTAL/dbfile.sqlite
        dbfile = os.path.expanduser(dbfile)
        self.engine = sqlalchemy.create_engine('sqlite:///' + dbfile, echo = echoSQLCommands)
        self.SessionMaker = sqlalchemy.orm.sessionmaker(bind=self.engine)

        if not os.path.exists(dbfile):
            DBBase.metadata.create_all(self.engine)
            self.insertExampleData()

        self.session = self.SessionMaker()

    def insertExampleData(self):
        pass

    def close(self):
        '''
        close database connection
        '''
        if not self.SessionMaker == None:
            self.SessionMaker.close_all()
        del(self.SessionMaker)
        self.SessionMaker = None
        del(self.engine)

        self.engine = None
        self.session = None

    def commit(self):
        if self.session != None:
            self.session.commit()

    def queryinfo(self, dbf):
        """
        return all the records (ordered by id?) which matches queried dbf

        properties set to None will be ignored (and not part of the search)
        only filename, group and comment can be queried
        """
        q = self.session.query(DBFile).order_by(DBFile.fileId)
        if dbf.fileId != None:
            q = q.filter(DBFile.fileId.ilike(dbf.fileId))
        if dbf.fileName != None and dbf.fileName != "":
            q = q.filter(DBFile.fileName.ilike(self.strtoqstr(dbf.fileName)))
        if dbf.group != None and dbf.group != "":
            q = q.filter(DBFile.group.ilike(self.strtoqstr(dbf.group)))
        if dbf.comment != None and dbf.comment != "":
            q = q.filter(DBFile.comment.ilike(self.strtoqstr(dbf.comment)))

        res = list(q.all())
        if len(res) == 0:
            return None
        return res

    def querydata(self, dbf, quick=False):
        """
        return all the records (ordered by id?) which matches queried dbf

        query is done only on data properties: fileSize, md1, md5, ed2k
        if quick is True only fileSize and md1 is queried
        """
        q = self.session.query(DBFile).order_by(DBFile.fileId)
        q = q.filter(DBFile.fileSize == dbf.fileSize)
        q = q.filter(DBFile.md1.ilike(dbf.md1))
        if not quick:
            q = q.filter(DBFile.md5.ilike(dbf.md5))
            q = q.filter(DBFile.ed2k.ilike(dbf.ed2k))

        res = list(q.all())
        if len(res) == 0:
            return None
        return res

    def strtoqstr(self, ss):
        """
        converts a normal string to a query string

        "hello world" -> "%hello%world%"
        """
        ss = "%" + ss + "%"
        ss.replace(' ', '%')
        return ss

    def __contains__(self, dbf):
        """
        return true if the database contains the specified dbfile (fileSize, md1, md5, ed2k is checked)
        """
        q = self.session.query(DBFile)
        q = q.filter(DBFile.fileSize == dbf.fileSize)
        q = q.filter(DBFile.md1 == dbf.md1)
        q = q.filter(DBFile.md5 == dbf.md5)
        q = q.filter(DBFile.ed2k == dbf.ed2k)
        return (q.count() != 0)

    def insert(self, dbfs, commit=True):
        """
        insert the specified dbf (which might be a list of files) into the database
        """
        if (not isinstance(dbfs, list)):
            dbfs = [ dbfs ]

        ins = False # at least something was instered
        for dbf in dbfs:
            if dbf in self:
                # TODO should we display a warning?
                continue
            ins = True
            self.session.add(dbf)
            self.session.merge(dbf) # this magic will refresh the fileId

        if ins and commit:
            self.session.commit()

    def update(self, dbf, setall=False):
        """
        update the entry given by dbf.fileId with the info from that dbf

        only filename, group and comment can be changed
        returns True if the update was successfull
        returns False if the record doesnt exists or nothing was set
        """
        q = self.session.query(DBFile).filter(DBFile.fileId == dbf.fileId)
        dbft = None
        try:
            dbft = q.one()
        except:
            return None

        com = False
        if dbf.fileName or setall: #!= None:
            dbft.fileName = dbf.fileName if dbf.fileName != "" else None
            com = True
        if dbf.group or setall: #!= None:
            dbft.group = dbf.group if dbf.group != "" else None
            com = True
        if dbf.comment or setall: #!= None:
            dbft.comment = dbf.comment if dbf.comment != "" else None
            com = True

        if com:
            self.session.add(dbft)
            self.session.commit()
        else:
            return None

        return dbft

