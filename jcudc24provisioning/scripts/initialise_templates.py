import transaction
from jcudc24provisioning.models.project import MethodSchema, MethodSchemaField, DBSession
from jcudc24ingesterapi.schemas.data_types import Double

__author__ = 'Casey Bajema'


class InitialiseData(object):
    def __init__(self):
        self.session = DBSession
        self.initialise_offset_locations_schema()

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
            transaction.commit()

            # TODO: Add the offset schema to CC-DAM as well
