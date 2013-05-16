"""
Create database tables and initialise the database with default values on the first run.
"""

import os
import os
import sys
import transaction

import random
from jcudc24provisioning.controllers.authentication import DefaultPermissions, DefaultRoles
from jcudc24provisioning.models import DBSession, Base
from jcudc24provisioning.models.project import Location, ProjectTemplate, Project, Dataset, MethodSchema, MethodSchemaField, Project, MethodTemplate, Method, PullDataSource, DatasetDataSource
from jcudc24ingesterapi.schemas.data_types import Double
from jcudc24provisioning.models import website

from sqlalchemy import engine_from_config

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
    initialise_all_db(settings)

def initialise_all_db(settings):
    """
    Initialise the database connection, create all tables if they don't exist then initialise default data if it hasn't
    already been.

    :param settings:
    :return:
    """

    # Initialise the database connection.
    engine = engine_from_config(settings, 'sqlalchemy.', pool_recycle=3600)
    DBSession.configure(bind=engine)

    # Test if the database has already been initialised with default data (is this the first time its run?)
    initialised = engine.dialect.has_table(engine.connect(), "project")

    # Create all database tables if they don't exist (on first run)
    Base.metadata.create_all(engine)

    # If this is the first run, initialise all default database data.
    if not initialised:
        with transaction.manager:
            session = DBSession
            initialise_default_schemas(session)
            initialise_project_templates(session)
            initialise_method_templates(session)
            initialise_security(session)
            transaction.commit()

def initialise_security(session):
    """
    Initialise the default permissions, roles and users.

    :param session: Database session to add new data to.
    :return: None
    """

    # Loop through all permissions in the DefaultPermissions class and add them to the database
    defaults = DefaultPermissions()
    for name in dir(defaults):
        if name.startswith("_"):
            continue
        name, description = getattr(defaults, name)
        permission = Permission(name, description)
        session.add(permission)

    # Loop through all roles in the DefaultPermissions class and add them to the database
    defaults = DefaultRoles()
    for name in dir(defaults):
        if name.startswith("_") or name == 'name':
            continue
        name, description, permissions = getattr(defaults, name)

        permission_objects = session.query(Permission).filter(Permission.name.in_([permission_name for (permission_name, permission_description) in permissions])).all()
        role = Role(name, description, permission_objects)
        session.add(role)

    # Add the default/testing users.
    session.flush()
    user = User("A User", "user", "user", "user@host.com")
    session.add(user)
    admin = User("Administrator", "admin", "admin", "admin@host.com", roles=session.query(Role).filter(Role.name==DefaultRoles().ADMIN[0]).all())
    session.add(admin)


def initialise_default_schemas(session):
    """
    Initialise all default MethodSchema standardised fields (parent schemas).

    :param session: Session to add the created schemas to the database with.
    :return: None
    """

    #-----------------Location Offset Schema----------------------
    location_offsets_schema = MethodSchema()
    location_offsets_schema.name = "XYZ Location Offsets"
    location_offsets_schema.template_schema = True

    x_offset_field = MethodSchemaField()
    x_offset_field.type = Double.__xmlrpc_class__
    x_offset_field.units = "meters"
    x_offset_field.name = "X Offset"
    x_offset_field.placeholder = "eg. 23.4"
    x_offset_field.default = 0
    location_offsets_schema.custom_fields.append(x_offset_field)

    y_offset_field = MethodSchemaField()
    y_offset_field.type = Double.__xmlrpc_class__
    y_offset_field.units = "meters"
    y_offset_field.name = "Z Offset"
    y_offset_field.placeholder = "eg. 23.4"
    y_offset_field.default = 0
    location_offsets_schema.custom_fields.append(y_offset_field)

    z_offset_field = MethodSchemaField()
    z_offset_field.type = Double.__xmlrpc_class__
    z_offset_field.units = "meters"
    z_offset_field.name = "Z Offset"
    z_offset_field.placeholder = "eg. 23.4"
    z_offset_field.default = 0
    location_offsets_schema.custom_fields.append(z_offset_field)

    session.add(location_offsets_schema)
    session.flush()

    #----------Temperature schema--------------
    temp_schema = MethodSchema()
    temp_schema.name = "Temperature"
    temp_schema.template_schema = True
    temp_schema.schema_type = "DataEntryMetadataSchema"

    temp_field = MethodSchemaField()
    temp_field.type = "decimal"
    temp_field.units = "Celcius"
    temp_field.name = "Temperature"
    temp_schema.custom_fields.append(temp_field)
    session.add(temp_schema)

    #----------Humidity schema--------------
    humidity_schema = MethodSchema()
    humidity_schema.name = "Humidity"
    humidity_schema.template_schema = True
    humidity_schema.schema_type = "DataEntryMetadataSchema"

    humidity_field = MethodSchemaField()
    humidity_field.type = "decimal"
    humidity_field.units = "%"
    humidity_field.name = "Humidity"
    humidity_schema.custom_fields.append(humidity_field)
    session.add(humidity_schema)

    #----------Moisture schema--------------
    moisture_schema = MethodSchema()
    moisture_schema.name = "Moisture"
    moisture_schema.template_schema = True
    moisture_schema.schema_type = "DataEntryMetadataSchema"

    moisture_field = MethodSchemaField()
    moisture_field.type = "decimal"
    moisture_field.units = "%"
    moisture_field.name = "Moisture"
    moisture_schema.custom_fields.append(moisture_field)
    session.add(moisture_schema)

    #----------Altitude schema--------------
    altitude_schema = MethodSchema()
    altitude_schema.name = "Altitude"
    altitude_schema.template_schema = True
    altitude_schema.schema_type = "DataEntryMetadataSchema"

    altitude_field = MethodSchemaField()
    altitude_field.type = "decimal"
    altitude_field.units = "Meters above Mean Sea Level (MSL)"
    altitude_field.name = "Altitude"
    altitude_schema.custom_fields.append(altitude_field)
    session.add(altitude_schema)

    #----------Distance schema--------------
    distance_schema = MethodSchema()
    distance_schema.name = "Distance"
    distance_schema.template_schema = True
    distance_schema.schema_type = "DataEntryMetadataSchema"

    distance_field = MethodSchemaField()
    distance_field.type = "decimal"
    distance_field.units = "Meters"
    distance_field.name = "Distance"
    distance_schema.custom_fields.append(distance_field)
    session.add(distance_schema)


    #----------Light Intensity schema--------------
    luminosity_schema = MethodSchema()
    luminosity_schema.name = "Luminosity"
    luminosity_schema.template_schema = True
    luminosity_schema.schema_type = "DataEntryMetadataSchema"

    luminosity_field = MethodSchemaField()
    luminosity_field.type = "decimal"
    luminosity_field.units = "candela (cd)"
    luminosity_field.name = "Luminosity"
    luminosity_schema.custom_fields.append(luminosity_field)
    session.add(luminosity_schema)


    #----------Weight schema--------------
    weight_schema = MethodSchema()
    weight_schema.name = "Weight"
    weight_schema.template_schema = True
    weight_schema.schema_type = "DataEntryMetadataSchema"

    weight_field = MethodSchemaField()
    weight_field.type = "decimal"
    weight_field.units = "kg"
    weight_field.name = "Weight"
    weight_schema.custom_fields.append(weight_field)
    session.add(weight_schema)


    #----------Density schema--------------
    density_schema = MethodSchema()
    density_schema.name = "Density"
    density_schema.template_schema = True
    density_schema.schema_type = "DataEntryMetadataSchema"

    density_field = MethodSchemaField()
    density_field.type = "decimal"
    density_field.units = "kg/m^3"
    density_field.name = "Density"
    density_schema.custom_fields.append(density_field)
    session.add(density_schema)

    session.flush()

def initialise_project_templates(session):
    """
    Initialise the default project templates, this could be updated to be organisation specific.

    :param session: Database connection to add the created templates to.
    :return: None
    """

    blank_project = Project()
    blank_project.template_only = True
    session.add(blank_project) # Add an empty project as a blank template
    session.flush()

    blank_template = ProjectTemplate()
    blank_template.template_id = blank_project.id
    blank_template.category = "Blank (No auto-fill)"
    blank_template.name = "Blank Template"
    blank_template.description = "An empty template that allows you to start from scratch (only for advanced "\
                                 "users or if no other template is relevent)."
    session.add(blank_template) # Add an empty project as a blank template


    #       add blank templates for testing, delete when production ready
    placeholder_template_names = [
        "DRO",
        "Australian Wet Tropics",
        "TERN Supersite",
        "The Wallace Initiative",
        "Tropical Futures",
        ]

    count = 0
    for name in placeholder_template_names:
        for i in range(random.randint(2, 5)):
            template = ProjectTemplate()
            template.template_id = blank_project.id
            template.category = name
            template.name = name + " Placeholder Template " + str(count) + " (Testing Only)"
            count += 1
            template.description = "An empty template that allows you to start from scratch (only for advanced "\
                                   "users or if no other template is relevent)."
            session.add(template) # Add an empty project as a blank template


def initialise_method_templates(session):
    """
    Initialise the default method templates.

    :param session: Database connection to add the created templates to
    :return: None
    """
    blank_template = session.query(MethodTemplate).filter_by(name="Blank Template").first()
    if not blank_template:
        blank_method = Method()
        #            blank_method.method_description = "Test description"
        session.add(blank_method) # Add an empty project as a blank template

        blank_dataset = Dataset()
        blank_dataset.name = "Test Title"
        session.add(blank_dataset) # Add an empty project as a blank template
        session.flush()

        blank_template = MethodTemplate()
        blank_template.template_id = blank_method.id
        blank_template.dataset_id = blank_dataset.id
        blank_template.category = "Blank (No pre-fill)"
        blank_template.name = "Blank Template"
        blank_template.description = "An empty template that allows you to start from scratch (only for advanced "\
                                     "users or if no other template is relevent)."
        session.add(blank_template) # Add an empty project as a blank template

    tree_template = session.query(MethodTemplate).filter_by(name="Artificial Tree").first()
    if not tree_template:
        tree_method = Method()
        tree_method.method_name = "Artificial Sensor Tree"
        tree_method.method_description = "Collection method for ingesting aggregated tree sensor data from an external file server."
        tree_method.data_source = PullDataSource.__tablename__

        tree_schema = MethodSchema()
        tree_schema.name = "ArtificialTree"
        tree_data_field = MethodSchemaField()
        tree_data_field.type = "file"
        tree_data_field.units = "text"
        tree_data_field.name = "TreeData"
        tree_data_field.description = "Aggregated data of all sensors for an artificial tree."
        tree_schema.custom_fields = [tree_data_field]
        tree_method.data_type = tree_schema
        #            blank_method.method_description = "Test description"
        session.add(tree_method) # Add an empty project as a blank template

        tree_dataset = Dataset()
        tree_dataset.name = "Raw Artificial Tree Data"
        tree_datasource = PullDataSource()
        tree_datasource.uri = "http://emu.hpc.jcu.edu.au/tree/split/"
        tree_datasource.filename_pattern = ""
        tree_datasource.selected_sampling = PullDataSource.periodic_sampling.key
        tree_datasource.periodic_sampling = "1"
        tree_dataset.pull_data_source = tree_datasource
        session.add(tree_dataset) # Add an empty project as a blank template
        session.flush()

        tree_template = MethodTemplate()
        tree_template.template_id = tree_method.id
        tree_template.dataset_id = tree_dataset.id
        tree_template.category = "Artificial Tree"
        tree_template.name = "Artificial Tree"
        tree_template.description = "Template for setting up ingestion from an artificial tree."
        session.add(tree_template) # Add an empty project as a blank template

    sensor_template = session.query(MethodTemplate).filter_by(name="Artificial Tree Sensor").first()
    if not sensor_template:
        sensor_method = Method()
        sensor_method.method_name = "Artificial Tree Sensor"
        sensor_method.method_description = "Filter and index one sensor station from the aggregated artificial tree data."
        sensor_method.data_source = DatasetDataSource.__tablename__

        sensor_method.data_type = session.query(MethodSchema).filter_by(name="Temperature").first()
        #            blank_method.method_description = "Test description"
        session.add(sensor_method) # Add an empty project as a blank template

        sensor_dataset = Dataset()
        sensor_dataset.name = "Artificial Tree Sensor"
        sensor_datasource = DatasetDataSource()
        sensor_datasource.custom_processing_parameters = "file_field=TreeData, temp_field=Temperature, sensor_id=28180E08030000BE"
        sensor_dataset.dataset_data_source = sensor_datasource
        session.add(sensor_dataset) # Add an empty project as a blank template
        session.flush()

        sensor_template = MethodTemplate()
        sensor_template.template_id = sensor_method.id
        sensor_template.dataset_id = sensor_dataset.id
        sensor_template.category = "Artificial Tree"
        sensor_template.name = "Artificial Tree Sensor"
        sensor_template.description = "Templates setting up post-processing and indexing of one artificial tree sensor from the aggregated artificial tree data."
        session.add(sensor_template) # Add an empty project as a blank template


    placeholder_template_names = [
        "DRO",
        "Australian Wet Tropics",
        "TERN Supersite",
        "The Wallace Initiative",
        "Tropical Futures",
        ]

    templates = session.query(MethodTemplate).all()
    print len(templates)
    if len(templates) <= 1:
        count = 0
        for name in placeholder_template_names:
            for i in range(random.randint(2, 5)):
                template = MethodTemplate()
                template.template_id = blank_template.id
                template.dataset_id = blank_template.dataset_id
                template.category = name
                template.name = name + " Placeholder Template " + str(count) + " (Testing Only)"
                count += 1
                template.description = "An empty template that allows you to start from scratch (only for advanced "\
                                       "users or if no other template is relevent)."
                session.add(template) # Add an empty project as a blank template
