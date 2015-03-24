import os
import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.sql.expression

import dbbase
import dbfile

class Model(object):
    def __init__(self, dbfile, dryrun):
        '''
        (constructor) initialize the mode
        dbfile is optional
        '''
        self.SessionMaker = None
        self.session = None
        self.engine = None
        self.dryrun = dryrun

        self.init(dbfile)


    def init(self,dbfile):
        '''
        Initialize the Model
        dbfile is optional
        '''
        self.close()
        #if dbfile==None:
        # default location for the lst (sqlite) ~/ViTAL/dbfile.sqlite
        dbfile = os.path.expanduser(dbfile)
        self.engine = sqlalchemy.create_engine('sqlite:///' + dbfile)#, echo=True)
        self.SessionMaker = sqlalchemy.orm.sessionmaker(bind=self.engine)

        if not os.path.exists(dbfile):
            dbbase.Base.metadata.create_all(self.engine)
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
        if self.session != None and not self.dryrun:
            self.session.commit()

    def queryinfo(self, dbf):
        """
        return all the records (ordered by id?) which matches queried dbf

        properties set to None will be ignored (and not part of the search)
        only filename, group and comment can be queried
        """
        q = self.session.query(dbfile.DBFile).order_by(dbfile.DBFile.idno)
        if dbf.idno != None:
            q = q.filter(dbfile.DBFile.idno.ilike(dbf.idno))
        if dbf.name != None and dbf.name != "":
            q = q.filter(dbfile.DBFile.name.ilike(self.strtoqstr(dbf.name)))
        if dbf.group != None and dbf.group != "":
            q = q.filter(dbfile.DBFile.group.ilike(self.strtoqstr(dbf.group)))
        if dbf.comment != None and dbf.comment != "":
            q = q.filter(dbfile.DBFile.comment.ilike(self.strtoqstr(dbf.comment)))

        res = list(q.all())
        if len(res) == 0:
            return None
        return res

    def querydata(self, dbf, quick=False):
        """
        return all the records (ordered by id?) which matches queried dbf

        query is done only on data properties: size, md1, md5, ed2k
        if quick is True only size and md1 is queried
        """
        q = self.session.query(dbfile.DBFile).order_by(dbfile.DBFile.idno)
        q = q.filter(dbfile.DBFile.size == dbf.size)
        q = q.filter(dbfile.DBFile.md1.ilike(dbf.md1))
        if not quick:
            q = q.filter(dbfile.DBFile.md5.ilike(dbf.md5))
            q = q.filter(dbfile.DBFile.ed2k.ilike(dbf.ed2k))

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
        return true if the database contains the specified dbfile (size, md1, md5, ed2k is checked)
        """
        q = self.session.query(dbfile.DBFile)
        q = q.filter(dbfile.DBFile.size == dbf.size)
        q = q.filter(dbfile.DBFile.md1 == dbf.md1)
        q = q.filter(dbfile.DBFile.md5 == dbf.md5)
        q = q.filter(dbfile.DBFile.ed2k == dbf.ed2k)
        return (q.count() != 0)

    def insert(self, dbfs, commit=True):
        """
        insert the specified dbf (which might be a list of files) into the database
        """
        if not type(dbfs) is list:
            dbfs = [ dbfs ]

        ins = False # at least something was instered
        for dbf in dbfs:
            if dbf in self:
                # TODO should we display a warning?
                continue
            ins = True
            self.session.add(dbf)
            self.session.merge(dbf) # this magic will refresh the idno

        if ins and commit and not self.dryrun:
            self.session.commit()

    def update(self, dbf, setall=False):
        """
        update the entry given by dbf.idno with the info from that dbf

        only filename, group and comment can be changed
        returns True if the update was successfull
        returns False if the record doesnt exists or nothing was set
        """
        q = self.session.query(dbfile.DBFile).filter(dbfile.DBFile.idno == dbf.idno)
        dbft = None
        try:
            dbft = q.one()
        except:
            return None

        com = False
        if dbf.name or setall: #!= None:
            dbft.name = dbf.name if dbf.name != "" else None
            com = True
        if dbf.group or setall: #!= None:
            dbft.group = dbf.group if dbf.group != "" else None
            com = True
        if dbf.comment or setall: #!= None:
            dbft.comment = dbf.comment if dbf.comment != "" else None
            com = True

        if com and not self.dryrun:
            self.session.add(dbft)
            self.session.commit()
        else:
            return None

        return dbft

