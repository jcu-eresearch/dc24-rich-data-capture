"""
Deletes all tables from the database, this is a development script and should never be called in a production envitonment.
"""

import os
import os
import sys
from sqlalchemy.engine import reflection
from sqlalchemy.schema import DropConstraint, DropTable
import transaction

import random
from jcudc24provisioning.controllers.authentication import DefaultPermissions, DefaultRoles
from jcudc24provisioning.models import DBSession, Base
from jcudc24provisioning.models.project import Location, ProjectTemplate, Project, Dataset, MethodSchema, MethodSchemaField, Project, MethodTemplate, Method, PullDataSource, DatasetDataSource
from jcudc24ingesterapi.schemas.data_types import Double
from jcudc24provisioning.models import website

from sqlalchemy import engine_from_config, MetaData, ForeignKeyConstraint, Table

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )
from jcudc24provisioning.models.website import User, Role, Permission

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd)) 
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    delete_all_tables(settings)

def delete_all_tables(settings):
    """
    Initialise the database connection and delete all data base tables.

    :param settings:
    :return:
    """

    # Initialise the database connection.
    engine = engine_from_config(settings, 'sqlalchemy.', pool_recycle=3600)

    conn = engine.connect()
    # the transaction only applies if the DB supports
    # transactional DDL, i.e. Postgresql, MS SQL Server
    trans = conn.begin()

    inspector = reflection.Inspector.from_engine(engine)

    # gather all data first before dropping anything.
    # some DBs lock after things have been dropped in
    # a transaction.

    metadata = MetaData()

    tbs = []
    all_fks = []

    for table_name in inspector.get_table_names():
        fks = []
        for fk in inspector.get_foreign_keys(table_name):
            if not fk['name']:
                continue
            fks.append(
                ForeignKeyConstraint((),(),name=fk['name'])
            )
        t = Table(table_name,metadata,*fks)
        tbs.append(t)
        all_fks.extend(fks)

    for fkc in all_fks:
        conn.execute(DropConstraint(fkc))

    for table in tbs:
        conn.execute(DropTable(table))

    trans.commit()