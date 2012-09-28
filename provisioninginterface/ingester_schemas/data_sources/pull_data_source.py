from sqlalchemy.dialects.mysql.base import VARCHAR
from sqlalchemy.engine.url import URL

__author__ = 'Casey Bajema'

class PullDataSource():
    pull_server = URL()