import os
import sys
import transaction

import random
from jcudc24provisioning.models.project import Base, Dataset, MethodSchema,ProjectTemplate, MethodSchemaField, DBSession, Project, MethodTemplate, Method, PullDataSource, DatasetDataSource
from jcudc24ingesterapi.schemas.data_types import Double

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

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
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)

    with transaction.manager:
        session = DBSession
        #        self.initialise_offset_locations_schema()
        initialise_temperature_schema(session)
        initialise_project_templates(session)
        initialise_method_templates(session)
        transaction.commit()

def initialise_offset_locations_schema(session):

    location_offsets_schema = session.query(MethodSchema).filter_by(name="XYZ Location Offsets").first()
    if not location_offsets_schema:
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

        # TODO: Add the offset schema to CC-DAM as well

def initialise_temperature_schema(session):
    temp_schema = session.query(MethodSchema).filter_by(name="Temperature").first()
    if not temp_schema:
        temp_schema = MethodSchema()
        temp_schema.name = "Temperature"
        temp_schema.template_schema = True
        temp_schema.schema_type = "DataEntryMetadataSchema"

        temp_field = MethodSchemaField()
        temp_field.type = "decimal"
        temp_field.units = "Celcius"
        temp_field.name = "Temperature"
        temp_field.validators = "decimal" # TODO: Auto schema validators
        temp_schema.custom_fields.append(temp_field)

        session.add(temp_schema)
        session.flush()

def initialise_project_templates(session):
    blank_template = session.query(ProjectTemplate).filter_by(name="Blank Template").first()
    blank_project = Project()
    if not blank_template:
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

    templates = session.query(ProjectTemplate).all()
    print len(templates)
    if len(templates) <= 1:
        count = 0
        for name in placeholder_template_names:
            for i in range(random.randint(2, 10)):
                template = ProjectTemplate()
                template.template_id = blank_project.id
                template.category = name
                template.name = name + " Placeholder Template " + str(count) + " (Testing Only)"
                count += 1
                template.description = "An empty template that allows you to start from scratch (only for advanced "\
                                       "users or if no other template is relevent)."
                session.add(template) # Add an empty project as a blank template


def initialise_method_templates(session):
    blank_template = session.query(MethodTemplate).filter_by(name="Blank Template").first()
    if not blank_template:
        blank_method = Method()
        #            blank_method.method_description = "Test description"
        session.add(blank_method) # Add an empty project as a blank template

        blank_dataset = Dataset()
        blank_dataset.title = "Test Title"
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
        tree_dataset.title = "Raw Artificial Tree Data"
        tree_datasource = PullDataSource()
        tree_datasource.uri = "http://emu.hpc.jcu.edu.au/tree/split/"
        tree_datasource.filename_pattern = "\\.*\\"
        tree_datasource.selected_sampling = PullDataSource.periodic_sampling.key
        tree_datasource.periodic_sampling = "60000"
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
        sensor_dataset.title = "Artificial Tree Sensor"
        sensor_datasource = DatasetDataSource()
        sensor_datasource.custom_processing_parameters = "28180E08030000BE"
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
            for i in range(random.randint(2, 10)):
                template = MethodTemplate()
                template.template_id = blank_template.id
                template.dataset_id = blank_template.dataset_id
                template.category = name
                template.name = name + " Placeholder Template " + str(count) + " (Testing Only)"
                count += 1
                template.description = "An empty template that allows you to start from scratch (only for advanced "\
                                       "users or if no other template is relevent)."
                session.add(template) # Add an empty project as a blank template