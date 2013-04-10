from collections import namedtuple
from deform.form import Form
import random
import string
import colander
import deform
from jcudc24provisioning.models import DBSession
from jcudc24provisioning.models.project import MethodSchema, field_types
from jcudc24provisioning.views.file_upload import upload_widget

__author__ = 'xjc01266'

# Indexes of custom_field's, field_types.
INTEGER_INDEX = 0
DECIMAL_INDEX = 1
TEXT_INPUT_INDEX = 2
TEXT_AREA_INDEX = 3
CHECKBOX_INDEX = 4
SELECT_INDEX = 5
RADIO_INDEX = 6
FILE_INDEX = 7
WEBSITE_INDEX = 8
EMAIL_INDEX = 9
PHONE_INDEX = 10
DATE_INDEX = 11
HIDDEN_INDEX = 12

class DummySession(object):
    def setdefault(self, arg1, arg2):
        pass

    def changed(self):
        pass

def get_method_schema_preview(method_schema_id):
    method_schema = DBSession.query(MethodSchema).filter_by(id=method_schema_id).first()
    model_schema = DataTypeSchema(method_schema)

    # Create a dummy request object to make file upload widgets display properly for preview purposes.
    settings = {'workflows.files': "./"}
    Registry = namedtuple('registry', 'settings')
    Request = namedtuple('registry', ['registry', 'session'])
    dummy_request = Request(registry=Registry(settings=settings), session=DummySession())

    model_schema._bind({'request': dummy_request})   # Use _bind instead of bind so the schema isn't cloned
    form = Form(model_schema, action="")
    display = form.render({})
    display = display[display.index(">")+1:].replace("</form>", "").strip()
    return display

class DataTypeSchema(colander.SchemaNode):
    def __init__(self, method_schema):
        params = {}
        self.__dict__['params'] = params
        super(DataTypeSchema, self).__init__(colander.Mapping('ignore'), **params)

        fields = get_schema_fields(method_schema)

        for field in fields:
            self.add(field)

def method_schema_to_model(method_schema):
    fields = get_schema_fields(method_schema)
    model_schema = colander._SchemaMeta(str(method_schema.name), (colander._SchemaNode,), fields)
    return model_schema

def get_schema_fields(method_schema):
    fields = []

    for parent in method_schema.parents:
        fields.extend(get_schema_fields(parent))

    for field in method_schema.custom_fields:
        field_type = field.type == field_types[CHECKBOX_INDEX][0] and colander.Boolean() or \
               field.type == field_types[DATE_INDEX][0] and colander.DateTime() or \
               colander.String()

        if field.values is not None:
            value_items = field.values.split(",")
            values = ()
            for value in value_items:
                values = values + ((value.strip(", ").lower().replace(" ", "_"), value),)

        #TODO: Website regex is basic but should validate blatant mistakes such as user misinterpreting the field for email
        widget = field.type == field_types[INTEGER_INDEX][0] and deform.widget.TextInputWidget(regex_mask="^\\\\d*$", strip=False) or\
                 field.type == field_types[DECIMAL_INDEX][0] and deform.widget.TextInputWidget(regex_mask="^(((\\\\.\\\\d*)?)|(\\\\d+(\\\\.\\\\d*)?))$", strip=False) or\
                 field.type == field_types[TEXT_AREA_INDEX][0] and deform.widget.TextAreaWidget() or\
                 field.type == field_types[CHECKBOX_INDEX][0] and deform.widget.CheckboxWidget() or\
                 field.type == field_types[SELECT_INDEX][0] and deform.widget.SelectWidget(values=values) or\
                 field.type == field_types[RADIO_INDEX][0] and deform.widget.RadioChoiceWidget(values=values) or\
                 field.type == field_types[FILE_INDEX][0] and upload_widget or\
                 field.type == field_types[WEBSITE_INDEX][0] and deform.widget.TextInputWidget(
                     regex_mask="(http://)?(www\.)?([^@. ]+)(\.[^.@ ]+)(\.[^@. ]+)?(\.[^@. ]+)?(\.[^@. ]+)?", strip=False) or \
                 field.type == field_types[EMAIL_INDEX][0] and deform.widget.TextInputWidget(
                     regex_mask="[^@ ]+@[^@ ]+\.[^@ ]+", strip=False) or\
                 field.type == field_types[PHONE_INDEX][0] and deform.widget.TextInputWidget(
                     regex_mask="(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})", strip=False) or\
                 field.type == field_types[DATE_INDEX][0] and deform.widget.DateInputWidget() or\
                 field.type == field_types[HIDDEN_INDEX][0] and deform.widget.HiddenWidget() or\
                 deform.widget.TextInputWidget()

        children = []
        params = {
            'name': field.name,
            'widget': widget,
            'description': field.description,
            'placeholder': field.placeholder,
            'default': field.default
        }

        fields.append(colander.SchemaNode(field_type, *children, **params))


    return fields
