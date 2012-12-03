from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.types import Integer
from colanderalchemy.declarative import Column
import deform
from zope.sqlalchemy.datamanager import ZopeTransactionExtension

__author__ = 'Casey Bajema'

#
#DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
#Base = declarative_base()


