from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension

__author__ = 'Casey Bajema'

# DBSession is the SQLAlchemy session used throughout the EnMaSSe provisioning interface for all database usage.
DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))

# Base SQLAlchemy model for all database models to extend.
Base = declarative_base()

