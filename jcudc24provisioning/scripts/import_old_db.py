from jcudc24provisioning.models import DBSession
from sqlalchemy import create_engine

__author__ = 'Casey Bajema'
import sys
sys.path[0:0] = [
    'c:\\dc24\\src\\jcu.dc24.ingesterapi',
    'c:\\dc24\\src\\jcu.dc24.provisioning',
    'c:\\dc24\\src\\jcu.dc24.ingesterplatform',
    'c:\\dc24\\src\\python-simplesos',
    'c:\\dc24\\src\\colanderalchemy',
    'c:\\dc24\\src\\deform',
    'c:\\dc24\\eggs\\zope.deprecation-4.0.2-py2.7.egg',
    'c:\\dc24\\eggs\\translationstring-1.1-py2.7.egg',
    'c:\\dc24\\eggs\\peppercorn-0.4-py2.7.egg',
    'c:\\dc24\\eggs\\colander-1.0a2-py2.7.egg',
    'c:\\dc24\\eggs\\chameleon-2.11-py2.7.egg',
    'c:\\dc24\\eggs\\sqlalchemy-0.8.0-py2.7-win32.egg',
    'c:\\dc24\\eggs\\requests-1.1.0-py2.7.egg',
    'c:\\dc24\\eggs\\pysqlite-2.6.3-py2.7-win32.egg',
    'c:\\dc24\\eggs\\ipython-0.13.1-py2.7.egg',
    'c:\\dc24\\eggs\\twisted-12.3.0-py2.7-win32.egg',
    'c:\\dc24\\eggs\\pysandbox-1.5-py2.7-win32.egg',
    'c:\\dc24\\eggs\\hashlib-20081119-py2.7-win32.egg',
    'c:\\dc24\\eggs\\paramiko-1.10.0-py2.7.egg',
    'c:\\dc24\\eggs\\webob-1.2.3-py2.7.egg',
    'c:\\dc24\\eggs\\mysql_python-1.2.4-py2.7-win32.egg',
    'c:\\dc24\\eggs\\pyramid_beaker-0.7-py2.7.egg',
    'c:\\dc24\\eggs\\pyramid_deform-0.2a5-py2.7.egg',
    'c:\\dc24\\eggs\\waitress-0.8.2-py2.7.egg',
    'c:\\dc24\\eggs\\zope.sqlalchemy-0.7.2-py2.7.egg',
    'c:\\dc24\\eggs\\pyramid_debugtoolbar-1.0.4-py2.7.egg',
    'c:\\dc24\\eggs\\pyramid_tm-0.7-py2.7.egg',
    'c:\\dc24\\eggs\\transaction-1.4.1-py2.7.egg',
    'c:\\dc24\\eggs\\pyramid-1.4-py2.7.egg',
    'c:\\dc24\\eggs\\zope.interface-4.0.5-py2.7-win32.egg',
    'c:\\dc24\\eggs\\pycrypto-2.6-py2.7-win32.egg',
    'c:\\dc24\\eggs\\beaker-1.6.4-py2.7.egg',
    'c:\\dc24\\eggs\\pygments-1.6-py2.7.egg',
    'c:\\dc24\\eggs\\pastedeploy-1.5.0-py2.7.egg',
    'c:\\dc24\\eggs\\venusian-1.0a7-py2.7.egg',
    'c:\\dc24\\eggs\\repoze.lru-0.6-py2.7.egg',
    'c:\\dc24\\eggs\\mako-0.7.3-py2.7.egg',
    'c:\\dc24\\eggs\\markupsafe-0.15-py2.7-win32.egg',
    'c:\\dc24\\eggs',
    'c:\\dc24\\venv\\lib\\site-packages\\distribute-0.6.35-py2.7.egg',
    'c:\\dc24\\venv\\lib\\site-packages\\lxml-2.3-py2.7-win32.egg',
    ]

def import_old_db():
    OLD_DB = "mysql://root:@localhost/dc24devel"
    NEW_DB = "mysql://root:@localhost/dc24"

    old_engine = create_engine(OLD_DB)
    old_connection = old_engine.connect()

    new_engine = create_engine(NEW_DB)
    new_connection = new_engine.connect()

    try:
        old_tables = old_connection.execute("SHOW TABLES").fetchall()

        for table in old_tables:
            rows = old_connection.execute("SELECT * FROM `%s`" % table).fetchall()
            table_structure = old_connection.execute("DESCRIBE `%s`" % table).fetchall()

            for row in rows:
                for j in range(len(row)):
                    row_result[structure[j][0]] = str(row[j])


    finally:
        old_connection.close()
        new_connection.close()
