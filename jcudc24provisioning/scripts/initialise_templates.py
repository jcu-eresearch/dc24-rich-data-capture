
import transaction
from jcudc24provisioning.models.project import MethodSchema,ProjectTemplate, MethodSchemaField, DBSession, Project, MethodTemplate, Method
from jcudc24ingesterapi.schemas.data_types import Double

__author__ = 'Casey Bajema'


class InitialiseSchemas(object):
    def __init__(self):
        self.session = DBSession
#        self.initialise_offset_locations_schema()
        self.initialise_temperature_schema()
        self.initialise_project_templates()
        self.initialise_method_templates()
        transaction.commit()

    def initialise_offset_locations_schema(self):

        location_offsets_schema = self.session.query(MethodSchema).filter_by(name="XYZ Location Offsets").first()
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

            self.session.add(location_offsets_schema)
            self.session.flush()

            # TODO: Add the offset schema to CC-DAM as well

    def initialise_temperature_schema(self):
        temp_schema = self.session.query(MethodSchema).filter_by(name="Temperature").first()
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

            self.session.add(temp_schema)
            self.session.flush()

    def initialise_project_templates(self):
        blank_template = self.session.query(ProjectTemplate).filter_by(name="Blank Template").first()
        if not blank_template:
            blank_project = Project()
            self.session.add(blank_project) # Add an empty project as a blank template
            self.session.flush()

            blank_template = ProjectTemplate()
            blank_template.template_id = blank_project.id
            blank_template.category = "General"
            blank_template.name = "Blank Template"
            blank_template.description = "An empty template that allows you to start from scratch (only for advanced " \
                                         "users or if no other template is relevent)."
            self.session.add(blank_template) # Add an empty project as a blank template

    def initialise_method_templates(self):
        blank_template = self.session.query(MethodTemplate).filter_by(name="Blank Template").first()
        if not blank_template:
            blank_method = Method()
            self.session.add(blank_method) # Add an empty project as a blank template
            self.session.flush()

            blank_template = MethodTemplate()
            blank_template.template_id = blank_method.id
            blank_template.category = "General"
            blank_template.name = "Blank Template"
            blank_template.description = "An empty template that allows you to start from scratch (only for advanced " \
                                         "users or if no other template is relevent)."
            self.session.add(blank_template) # Add an empty project as a blank template


