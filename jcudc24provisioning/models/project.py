import ConfigParser
from collections import OrderedDict
import itertools
import colander
from sqlalchemy.engine import create_engine
from sqlalchemy.schema import ForeignKey, Table
from colanderalchemy.declarative import Column, relationship
import deform
from sqlalchemy import (
    Integer,
    Text,
    )
from sqlalchemy.types import String, Boolean, Date
from jcudc24provisioning.models.common_schemas import OneOfDict
from jcudc24provisioning.models.common_schemas import upload_widget


from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    mapper)
from views.widgets import MethodSchemaWidget

config = ConfigParser.RawConfigParser()
config.read('../../development.ini')
db_engine = create_engine(config.get("app:main", "sqlalchemy.url"), echo=True)
#db_engine.connect()
DBSession = scoped_session(sessionmaker(bind=db_engine))
Base = declarative_base()

def research_theme_validator(form, value):
    if not value['ecosystems_conservation_climate'] and not value['industries_economies']\
       and not value['peoples_societies'] and not value['health_medicine_biosecurity']\
    and not value['not_aligned']:
        exc = colander.Invalid(
            form) # Uncomment to add a block message: , 'At least 1 research theme or Not aligned needs to be selected')
        exc['ecosystems_conservation_climate'] = 'At least 1 research theme needs to be selected'
        exc['industries_economies'] = 'At least 1 research theme needs to be selected'
        exc['peoples_societies'] = 'At least 1 research theme needs to be selected'
        exc['health_medicine_biosecurity'] = 'At least 1 research theme needs to be selected'
        exc['not_aligned'] = 'Select this if the none above are applicable'
        raise exc

#@cache_region('long_term')
def getFORCodes():
    FOR_CODES_FILE = "for_codes.csv"

    for_codes_file = open(FOR_CODES_FILE).read()
    data = OrderedDict()
    data['---Select One---'] = OrderedDict()

    item1 = ""
    item2 = ""
    for code in for_codes_file.split("\n"):
        if code.count(",") <= 0: continue

        num, name = code.split(",", 1)
        num = num.replace("\"", "")
        name = name.replace("\"", "")

        index1 = num[:2]
        index2 = num[2:4]
        index3 = num[4:6]

        if int(index3):
            if not item2 or not item2 in data[item1]:
                item2 = item1
                data[item1][item2] = list()
                data[item1][item2].append('---Select One---')
            data[item1][item2].append(num + ' ' + name)
        elif int(index2):
            item2 = num[0:4] + " " + name
            data[item1][item2] = list()
            data[item1][item2].append('---Select One---')
        else:
            item1 = num[0:2] + " " + name
            data[item1] = OrderedDict()
            data[item1]['---Select One---'] = OrderedDict()

    return data


#@cache_region('long_term')
def getSEOCodes():
    SEO_CODES_FILE = "seo_codes.csv"

    seo_codes_file = open(SEO_CODES_FILE).read()
    data = OrderedDict()
    data['---Select One---'] = OrderedDict()

    item1 = ""
    item2 = ""
    for code in seo_codes_file.split("\n"):
        if code.count(",") <= 0: continue

        num, name = code.split(",", 1)
        num = num.replace("\"", "")
        name = name.replace("\"", "")

        index1 = num[:2]
        index2 = num[2:4]
        index3 = num[4:6]

        if int(index3):
            if not item2 or not item2 in data[item1]:
                item2 = item1
                data[item1][item2] = list()
                data[item1][item2].append('---Select One---')
            data[item1][item2].append(num + ' ' + name)
        elif int(index2):
            item2 = num[0:4] + " " + name
            data[item1][item2] = list()
            data[item1][item2].append('---Select One---')
        else:
            item1 = num[0:2] + " " + name
            data[item1] = OrderedDict()
            data[item1]['---Select One---'] = OrderedDict()

    return data


class FieldOfResearch(Base):
    order_counter = itertools.count()

    __tablename__ = 'field_of_research'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())

    field_of_research = Column(String(50), ca_title="Field Of Research", ca_widget=deform.widget.TextInputWidget(template="readonly/textinput"),
    ca_data=getFORCodes())


class SocioEconomicObjective(Base):
    order_counter = itertools.count()

    __tablename__ = 'socio_economic_objective'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())

    socio_economic_objective = Column(String(50), ca_title="Socio-Economic Objective", ca_widget=deform.widget.TextInputWidget(template="readonly/textinput"),
    ca_data=getSEOCodes())

class Person(Base):
    order_counter = itertools.count()

    __tablename__ = 'person'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())

    title = Column(String(5), ca_title="Title", ca_placeholder="eg. Mr, Mrs, Dr",)
    given_name = Column(String(256), ca_title="Given name")
    family_name = Column(String(256), ca_title="Family name")
    email = Column(String(256), ca_missing="", ca_validator=colander.Email())

relationship_types = (
        (colander.null, "---Select One---"), ("owner", "Owned by"), ("manager", "Managed by"), ("associated", "Associated with"),
        ("aggregated", "Aggregated by")
        , ("enriched", "Enriched by"))

class Party(Base):
    order_counter = itertools.count()

    __tablename__ = 'party'
    person_id = Column(Integer, ForeignKey('person.id'), ca_order=next(order_counter), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'), ca_order=next(order_counter), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())

    party_relationship = Column(String(100), ca_order=next(order_counter), ca_title="This project is",
        ca_widget=deform.widget.SelectWidget(values=relationship_types),
        ca_validator=OneOfDict(relationship_types[1:]))

    person = relationship('Person', ca_order=next(order_counter), uselist=False)

class Creator(Base):
    order_counter = itertools.count()

    __tablename__ = 'creator'
    person_id = Column(Integer, ForeignKey('person.id'), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())

    person = relationship('Person', uselist=False)

class Keyword(Base):
    order_counter = itertools.count()

    __tablename__ = 'keyword'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())

    keyword = Column(String(512), )


class Collaborator(Base):
    order_counter = itertools.count()

    __tablename__ = 'collaborator'
    id = Column(Integer, ForeignKey('person.id'), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())

    collaborator = Column(String(256), ca_title="Collaborator",
        ca_placeholder="eg. CSIRO, University of X, Prof. Jim Bloggs, etc.")


class CitationDate(Base):
    order_counter = itertools.count()

    __tablename__ = 'citation_date'
    id = Column(Integer, ForeignKey('person.id'), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())

    dateType = Column(String(100), ca_title="Date type",
        ca_widget=deform.widget.TextInputWidget(size="40", css_class="full_width"))
    archivalDate = Column(Date(), ca_title="Date")


attachment_types = (("data", "Data file"), ("supporting", "Supporting material"), ("readme", "Readme"))
class Attachment(Base):
    order_counter = itertools.count()

    __tablename__ = 'attachment'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())

    type = Column(String(100), ca_widget=deform.widget.SelectWidget(values=attachment_types),
        ca_validator=colander.OneOf(
            [attachment_types[0][0], attachment_types[1][0], attachment_types[2][0]]),
        ca_title="Attachment type", ca_css_class="inline")
    attachment = Column(String(512),  ca_widget=upload_widget)
#    ca_params={'widget' : deform.widget.HiddenWidget()}


class Note(Base):
    order_counter = itertools.count()

    __tablename__ = 'note'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())

    note = Column(Text(), ca_widget=deform.widget.TextAreaWidget())

    def __init__(self, note):
        self.note = note

map_location_types = (
    ("none", "---Select One---"),
    ("gml", "OpenGIS Geography Markup Language"),
    ("kml", "Keyhole Markup Language"),
    ("iso19139dcmiBox", "DCMI Box notation (iso19139)"),
    ("dcmiPoint", "DCMI Point notation"),
    ("gpx", "GPS Exchange Format"),
    ("iso31661", "Country code (iso31661)"),
    ("iso31662", "Country subdivision code (iso31662)"),
    ("kmlPolyCoords", "KML long/lat co-ordinates"),
    ("gmlKmlPolyCoords", "KML long/lat co-ordinates derived from GML"),
    ("text", "Free text"),
    )
class Location(Base):
    order_counter = itertools.count()

    __tablename__ = 'location'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'), nullable=True, ca_widget=deform.widget.HiddenWidget())
    dataset_id = Column(Integer, ForeignKey('dataset.id'), nullable=True, ca_widget=deform.widget.HiddenWidget())

    location_type = Column(String(100), ca_widget=deform.widget.SelectWidget(values=map_location_types),
        ca_title="Location Type", ca_missing="")
    location = Column(String(512))

class WebResource(Base):
    order_counter = itertools.count()

    __tablename__ = 'web_resource'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())

    title = Column(String(512), ca_title="Title", ca_placeholder="eg. Great Project Website", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40))
    url = Column(String(512), ca_title="URL", ca_placeholder="eg. http://www.somewhere.com.au", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40))
    notes = Column(String(512), ca_title="Note", ca_missing="", ca_placeholder="eg. This article provides additional information on xyz", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40))

data_types = (
    ('video', 'Video'),
    ('audio', 'Audio'),
    ('temperature', 'Temperature'),
    ('humidity', 'Humidity'),
    ('rain_fall', 'Rain fall'),
    ('moisture', 'Moisture'),
    ('wind', 'Wind (direction & speed)'),
    ('weight', 'Weight'),
    ('light_intensity', 'Light intensity'),
#    ('file', 'File (Generic file that doesn\'t have a type defined)'),
    ('custom', '(Advanced) No defined type'),
)

data_sources = (
    ('manual', 'Web Form/Manual (Add data using this website only)'),
    ('pull', 'Poll external file system'),
    ('push', '(Advanced) Push to this website through the API'),
    ('sos', 'Sensor Observation Service (SOS)'),
    ('dataset', '(Advanced) Output from other dataset'),
)

field_types = (
    ('integer', 'Integer number'),
    ('decimal', 'Decimal number'),
    ('text_input', 'Single line text'),
    ('text_area', 'Multi-line text'),
    ('checkbox', 'Checkbox'),
    ('select', 'Select/Dropdown box'),
    ('select', 'Radio buttons/Multiple choice'),
    ('file', 'File upload'),
    ('website', 'Website'),
    ('email', 'Email'),
    ('phone', 'Phone'),
    ('address', 'Address'),
    ('person', 'Person'),
    ('hidden', 'Hidden (Used by custom processing only)'),
)

class MethodAttachment(Base):
    order_counter = itertools.count()

    __tablename__ = 'method_attachment'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('method.id'), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())

    attachment = Column(String(512),  ca_widget=upload_widget)
    note = colander.SchemaNode(colander.String(), placeholder="eg. data sheet", widget=deform.widget.TextInputWidget(css_class="full_width"))

class MethodSchemaField(Base):
    order_counter = itertools.count()

    __tablename__ = 'method_schema_field'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    method_schema_id = Column(Integer, ForeignKey('method_schema.id'),  nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    type = Column(String(100), ca_title="Field Type",
        ca_widget=deform.widget.SelectWidget(values=field_types),
        ca_description="",
        ca_placeholder="Type of field that should be shown.")
    name = Column(String(256), ca_title="Name", ca_placeholder="eg. Temperature", ca_widget=deform.widget.TextInputWidget(css_class="full_width"))
    description = Column(Text(), ca_title="Description", ca_placeholder="eg. Calibrated temperature reading", ca_widget=deform.widget.TextInputWidget(css_class="full_width"))
    placeholder = Column(String(256), ca_title="Example", ca_placeholder="eg. 26.3", ca_widget=deform.widget.TextInputWidget(css_class="full_width"))
    default = Column(String(256), ca_title="Default Value.", ca_placeholder="Use appropriately where the user will usually enter the same value.", ca_widget=deform.widget.TextInputWidget(css_class="full_width"))
    validators = Column(String(256), ca_title="Validator", ca_placeholder="eg. Numerical value with decimal places or what values are expected such as for a dropdown box", ca_widget=deform.widget.TextInputWidget(css_class="full_width"))
    notes = Column(String(256), ca_title="Admin Notes", ca_placeholder="eg. Please read this field from the uploaded files, it will follow a pattern like temp:xxx.xx", ca_widget=deform.widget.TextAreaWidget(css_class="full_width"))

class MethodWebsite(Base):
    order_counter = itertools.count()

    __tablename__ = 'method_website'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('method.id'), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())

    title = Column(String(256), ca_title="Title", ca_placeholder="eg. Great Project Website", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40))
    url = Column(String(256), ca_title="URL", ca_placeholder="eg. http://www.somewhere.com.au", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40))
    notes = Column(Text(), ca_title="Notes", ca_missing="", ca_placeholder="eg. This article provides additional information on xyz", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40))

method_schema_to_schema = Table("schema_to_schema", Base.metadata,
    Column("child_id", Integer, ForeignKey("method_schema.id"), primary_key=True),
    Column("parent_id", Integer, ForeignKey("method_schema.id"), primary_key=True)
)

class MethodSchema(Base):
    order_counter = itertools.count()

    __tablename__ = 'method_schema'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    method_id = Column(Integer, ForeignKey('method.id'),  nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    template_schema = Column(Boolean, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter)) # These are system schemas that users are encouraged to extend.

    name = Column(String(256), ca_order=next(order_counter), ca_title="Schema Name", ca_placeholder="eg. Temperature with sensor XYZ calibration data", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40))
    share_schema = Column(Boolean, ca_order=next(order_counter), ca_default=False) # These are system schemas that users are encouraged to extend.
    parents = relationship("MethodSchema",ca_order=next(order_counter),
        secondary=method_schema_to_schema,
        primaryjoin=id==method_schema_to_schema.c.child_id,
        secondaryjoin=id==method_schema_to_schema.c.parent_id,
        ca_widget=deform.widget.SequenceWidget(template="method_schema_parents_sequence"),
        ca_child_widget=deform.widget.MappingWidget(template="ca_sequence_mapping", item_template="method_schema_parents_item"),
        ca_description="TODO: This is where the default and shared schemas will be selectable from")
    custom_fields = relationship("MethodSchemaField", ca_order=next(order_counter), ca_child_title="Custom Field",
        ca_description="Provide details of the schema field and how it should be displayed.<br /><br />TODO:  This needs to be displayed better - I'm thinking a custom template that has a sidebar for options and the fields are displayed 1 per line.  All fields will be shown here (including fields from parent/extended schemas selected above).")

class Method(Base):
    order_counter = itertools.count()

    __tablename__ = 'method'
    id = Column(Integer, ca_order=next(order_counter), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())


    copy_previous_method = Column(String(256), ca_order=next(order_counter), ca_title="Use a previously created method as a template",
        ca_widget=deform.widget.AutocompleteInputWidget(size=250, min_length=1, values=('Method A','Method B'), template="template_autocomplete_input"),
        ca_description="Use a previously created method as a template, <b>this will overwrite all fields on this page</b> " \
                           "with the content in the selected method.<br />" \
                           "Usage: If the same method (eg. sensor) is used for 2 projects you don't need to recreate the same method twice!" \
                           "<br /><br /><b>TODO: Rework this into a list of admin provided templates.</b>")

    data_type = relationship("MethodSchema", ca_order=next(order_counter), uselist=False, ca_widget=MethodSchemaWidget(),
        ca_description="<b>Under Development - Needs a new widget to provide required functionality!</b><br/><br/>The type of data that is being collected - <b>Please extend the provided schemas where possible only use the custom fields for additional information</b> (eg. specific calibration data).</br></br>" \
                    "Extending the provided schemas allows your data to be found in a generic search (eg. if you use the temperature schema then users will find your data " \
                    "when searching for temperatures, but if you make the schema using custom fields (even if it is the same), then it won't show up in the temperature search results).")

    data_sources=(
        ("form_data_source","<b>Web Form/Manual:</b> Only use an online form accessible through this interface to manually upload data (Other data sources also include this option)."),
        ("poll_data_source","<b>Poll external file system:</b> Setup automatic polling of an external file system from a URL location, when new files of the correct type and naming convention are found they are ingested."),
        ("push_data_source","<b><i>(Advanced)</i> Push to this website through the API:</b> Use the XMLRPC API to directly push data into persistent storage, on project acceptance you will be emailed your API key and instructions."),
        ("sos_data_source","<b>Sensor Observation Service:</b> Set-up a sensor that implements the Sensor Observation Service (SOS) to push data into this systems SOS server."),
        ("dataset_data_source","<b><i>(Advanced)</i> Output from other dataset:</b> Output from other dataset: </b>This allows for advanced/chained processing of data, where the results of another dataset can be further processed and stored as required."),
    )

    data_source =  Column(String(50), ca_order = next(order_counter), ca_widget=deform.widget.RadioChoiceWidget(values=data_sources),
        ca_description="How does the data get transferred into this system",
        ca_placeholder="Select the easiest method for your project.  If all else fails, manual file uploads will work for all data types.")

    method_name = Column(String(256), ca_order=next(order_counter),
        ca_placeholder="Searchable identifier for this input method (eg. Invertebrate observations)",
        ca_description="Descriptive, human readable name for this input method.  The name will be used to select this method in the <i>Datasets</i> step and will also be searchable within the database.")
    method_description = Column(Text(), ca_order=next(order_counter), ca_title="Description", ca_widget=deform.widget.TextAreaWidget(),
        ca_description="Provide a description of this method, this should include what, why and how the data is being collected but <b>Don\'t enter where or when</b> as this is information relevant to the dataset, not the method.",
        ca_placeholder="Enter specific details for this method, users of your data will need to know how reliable your data is and how it was collected.")
    method_url = relationship("MethodWebsite", ca_order=next(order_counter), ca_missing=colander.null, ca_title="Further information (URL)",
        ca_child_widget=deform.widget.MappingWidget(template="inline_mapping"), ca_child_title="Website",
        ca_description="If there are web addresses that can provide more information on your data collection method, add them here.  Examples may include manufacturers of your equipment or an article on the calibration methods used.")
    method_attachments = relationship('MethodAttachment', ca_order=next(order_counter), ca_missing=colander.null, ca_child_title="Attachment",
        ca_description="Attach information about this method, this is preferred to external URLs as it is persistent.  Example attachments would be sensor datasheets, documentation describing your file/data storage schema or calibration data.")

class FormDataSource(Base):
    order_counter = itertools.count()

    __tablename__ = 'form_data_source'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'),  nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

class PollDataSource(Base):
    order_counter = itertools.count()

    __tablename__ = 'poll_data_source'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'),  nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    poll_data_source_url = Column(Text(), ca_order=next(order_counter),
        ca_placeholder="eg. http://example.com.au/folder/",
        ca_description="Provide the url that should be polled for data - files will be ingested that follow the name convention of <i>TODO</i>")

class PushDataSource(Base):
    order_counter = itertools.count()

    __tablename__ = 'push_data_source'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'),  nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    api_key = Column(Text(), ca_title="API Key (Password to use this functionality)", ca_order=next(order_counter),
        ca_default="TODO: Auto-generate key",
        ca_description="The password that is needed to push your data into to this system.")

class SOSDataSource(Base):
    order_counter = itertools.count()

    __tablename__ = 'sos_data_source'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'),  nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    sos_data_source_url = Column(Text(), ca_title="Sensor Observation Service (SOS) Data Source", ca_order=next(order_counter),
        ca_placeholder="eg. http://example.com.au/sos/",
        ca_description="Provide the url of the Sensor Observation Service to pull data from.")

    sensor_id = Column(Text(), ca_title="Sensor ID", ca_order=next(order_counter),
        ca_placeholder="eg. 22",
        ca_description="The ID of the sensor that data should be extracted for (leave blank to extract all data).")

class DatasetDataSource(Base):
    order_counter = itertools.count()

    __tablename__ = 'dataset_data_source'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'),  nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    # TODO: Selection of datasets
    dataset_data_source_id = Column(Text(), ca_title="Dataset", ca_order=next(order_counter), ca_widget=deform.widget.SelectWidget(),
        ca_placeholder="eg. 2",
        ca_description="The dataset to retrieve processed data from.")

class Dataset(Base):
    order_counter = itertools.count()

    __tablename__ = 'dataset'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter),
#        ca_group_start="method", ca_group_title="Method", ca_group_schema=SelectMappingSchema,
        )
    project_id = Column(Integer, ForeignKey('project.id'),  nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter),
#        ca_group_start="test_method", ca_group_title="Test Method",
        )
    method_id = Column(Integer, ForeignKey('method.id'), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    description = Column(Text(),ca_order=next(order_counter), ca_widget=deform.widget.TextAreaWidget(),
        ca_placeholder="Provide a textual description of the dataset being collected.",
        ca_description="Provide a dataset specific description that will be appended to the project description in metadata records.")

    form_data_source = relationship("FormDataSource", ca_order=next(order_counter), uselist=False,
        ca_group_start="data_source_configuration", ca_group_collapsed=False, ca_group_widget=deform.widget.MappingWidget(template="data_source_config_mapping"), ca_group_description="<b>TODO: Specialised template/widget to display the data source configuration correctly</b><br/><br/>Configure how this dataset will ingest data.")
    poll_data_source = relationship("PollDataSource", ca_order=next(order_counter), uselist=False,)
    push_data_source = relationship("PushDataSource", ca_order=next(order_counter), uselist=False,)
    sos_data_source = relationship("SOSDataSource", ca_order=next(order_counter), uselist=False,)
    dataset_data_source = relationship("DatasetDataSource", ca_order=next(order_counter), uselist=False,
        ca_group_end="data_source_configuration")

    publish_dataset = Column(Boolean, ca_title="Publish Dataset to ReDBox", ca_default=True, ca_order=next(order_counter),
#        ca_widget=ConditionalCheckboxMapping(),
        ca_description="Publish a metadata record to ReDBox for this dataset - leave this selected unless the data isn't relevant to anyone else (eg. Raw data where other users " \
                       "will only search for the processed data).  <b>TODO:  Hide the Coverage section when checkbox isn't selected.</b>")

    time_period_description = Column(String(256), ca_order=next(order_counter), ca_title="Time Period (description)",
        ca_group_start="coverage", ca_group_collapsed=False,
        ca_placeholder="eg. Summers of 1996-2006", ca_missing="",
        ca_description="Provide a textual representation of the time period such as world war 2 or more information on the time within the dates provided.")
    date_from = Column(Date(), ca_order=next(order_counter), ca_placeholder="", ca_title="Date From",
        ca_description='The date that data will start being collected.')
    date_to = Column(Date(), ca_order=next(order_counter), ca_title="Date To", ca_page="metadata",
        ca_description='The date that data will stop being collected.', ca_missing=colander.null)
    location_description = Column(String(512), ca_order=next(order_counter), ca_title="Location (description)",
        ca_description="Textual description of the location such as Australian Wet Tropics or further information such as elevation."
        , ca_missing="", ca_placeholder="eg. Australian Wet Tropics, Great Barrier Reef, 1m above ground level")
    coverage_map = relationship('Location', ca_order=next(order_counter), ca_title="Location Map", ca_widget=deform.widget.SequenceWidget(template='map_sequence'),
        ca_group_end="coverage", ca_child_widget=deform.widget.MappingWidget(template="inline_mapping"),
        ca_missing=colander.null, ca_description=
        "<p>Geospatial location relevant to the research dataset/collection, registry/repository, catalogue or index. This may describe a geographical area where data was collected, a place which is the subject of a collection, or a location which is the focus of an activity, eg. coordinates or placename.</p>"\
        "<p>You may use the map to select an area, or manually enter a correctly formatted set of coordinates or a value supported by a standard such as a country code, a URL pointing to an XML based description of spatial coverage or free text describing a location."\
        "</p><p>If you wish to generate a map display in Research Data Australia, it is strongly advised that you use <b>DCMI Box</b> for shapes, or <b>DCMI Point</b> for points.</p><p>"\
        "Formats supported by the map widget:"\
        "<ul><li><a href=\"http://www.opengeospatial.org/standards/gml\" target=\"_blank\">GML</a> - OpenGIS Geography Markup Language (GML) Encoding Standard</li>"\
        "<li><a href=\"http://code.google.com/apis/kml/\" target=\"_blank\">KML</a> - Keyhole Markup Language developed for use with Google Earth</li>"\
        "<li><a href=\"http://dublincore.org/documents/dcmi-box\" target=\"_blank\">ISO19319dcmiBox</a> - DCMI Box notation derived from bounding box metadata conformant with the iso19139 schema</li>"\
        "<li><a href=\"http://dublincore.org/documents/dcmi-point\" target=\"_blank\">DCMIPoint</a> - spatial location information specified in DCMI Point notation</li></ul>"\
        "<p>When using the map to input shapes/points, only the above formats are supported. You can use the 'Find location' feature to pan the map to an area you are interested in, but you still need to select a map region to store geospatial data.</p>"\
        "<p>Formats available for manual data entry:</p>"\
        "<ul><li><a href=\"http://www.topografix.com/gpx.asp\" target=\"_blank\">GPX</a> - the GPS Exchange Format</li>"\
        "<li><a href=\"http://www.iso.org/iso/country_codes/iso_3166_code_lists.htm\" target=\"_blank\">ISO3166</a> - ISO 3166-1 Codes for the representation of names of countries and their subdivisions - Part 1: Country codes</li>"\
        "<li><a href=\"http://www.iso.org/iso/country-codes/background_on_iso_3166/iso_3166-2.htm\" target=\"_blank\">ISO31662</a> - Codes for the representation of names of countries and their subdivisions - Part 2: Country subdivision codes</li>"\
        "<li><a href=\"http://code.google.com/apis/kml/\" target=\"_blank\">kmlPolyCoords</a> - A set of KML long/lat co-ordinates defining a polygon as described by the KML coordinates element</li>"\
        "<li><a href=\"http://code.google.com/apis/kml/\" target=\"_blank\">gmlKmlPolyCoords</a> - A set of KML long/lat co-ordinates derived from GML defining a polygon as described by the KML coordinates element but without the altitude component</li>"\
        "<li><strong>Text</strong> - free-text representation of spatial location. Use this to record place or region names where geospatial notation is not available. In ReDBox this will search against the Geonames database and return a latitude and longitude value if selected. This will store as a DCMIPoint which in future will display as a point on a Google Map in Research Data Australia.</li></ul>")


    start_conditions = Column(String(100),ca_order=next(order_counter), ca_title="Start conditions", ca_child_title="todo",
        ca_group_start="sampling", ca_group_collapsed=False, ca_group_description="Provide filtering conditions for the data received, the most common and simplest"\
                    "cases are a sampling rate (eg. once per hour) or a repeating time periods (such as "\
                    "start at 6am, stop at 7am daily) but any filtering can be acheived by adding a custom "\
                    "sampling script below.</br></br>  The sampling script API can be found <a href="">here</a>.")
    stop_conditions = Column(String(100),ca_order=next(order_counter), ca_title="Stop conditions", ca_child_title="todo")

    custom_sampling_desc = Column(String(256),ca_order=next(order_counter), ca_widget=deform.widget.TextAreaWidget(),
        ca_group_start="custom_sampling", ca_group_title="Custom sampling",
        ca_placeholder="eg. Extract some value from the comma separated file where the value is the first field.",
        ca_title="Describe custom sampling needs", ca_missing="", ca_description="Describe your sampling "\
                                                                          "requirements and what your uploaded script does, or what you will need help with.")

    custom_sampling_script = Column(String(256),ca_order=next(order_counter), ca_title="Upload custom sampling script", ca_missing = colander.null,
        ca_group_end="sampling",
        ca_description="Upload a custom Python script to "\
                    "sample the data in some way.  The sampling script API can be found "\
                    "<a title=\"Python sampling script API\"href=\"\">here</a>.")

    custom_processor_desc = Column(String(256),ca_order=next(order_counter), ca_widget=deform.widget.TextAreaWidget(),
        ca_group_start="processing", ca_group_collapsed=False, ca_group_title="Custom processing",
        ca_placeholder="eg. Extract some value from the comma separated file where the value is the first field.",
        ca_title="Describe custom processing needs", ca_missing="", ca_description="Describe your processing "\
                    "requirements and what your uploaded script does, or what you will need help with.")

    custom_processor_script = Column(String(256),ca_order=next(order_counter), ca_title="Upload custom processing script", ca_missing = colander.null,
        ca_group_end="method",
        ca_description="Upload a custom Python script to "\
            "process the data in some way.  The processing script API can be found "\
            "<a title=\"Python processing script API\"href=\"\">here</a>.")


class ProjectNote(Base):
    order_counter = itertools.count()

    __tablename__ = 'project_note'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    comment = Column(Text(),
        ca_placeholder="eg. Please enter all metadata, the supplied processing script has errors, please extend the existing temperature data type so that your data is searchable, etc..."
        , ca_widget=deform.widget.TextAreaWidget(rows=3))

class ProjectTemplate(Base):
    """
    Indicate an existing project is a template that others can use to pre-populate their projects
    """
    __tablename__ = 'project_template'
    order_counter = itertools.count()
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

class DatasetTemplate(Base):
    """
    Indicate that a dataset is a template that users can pre-populate datasets with.

    This is only intended to be used by method templates
    """
    __tablename__ = 'dataset_template'
    order_counter = itertools.count()
    id = Column(Integer, ca_order=next(order_counter), primary_key=True, ca_widget=deform.widget.HiddenWidget(), ca_missing=-1)
    dataset_id = Column(Integer, ForeignKey('dataset.id'), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    method_template_id = Column(Integer, ForeignKey('method_template.id'),  nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

class MethodTemplate(Base):
    """
    Method templates that can be used to pre-populate a method with as well as datasets created for that method.
    """
    __tablename__ = 'method_template'
    order_counter = itertools.count()
    id = Column(Integer, ca_order=next(order_counter), primary_key=True, ca_widget=deform.widget.HiddenWidget(), ca_missing=-1)
    method_id = Column(Integer, ForeignKey('method.id'), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_templates = relationship('DatasetTemplate')

choices = ['JCU Name 1', 'JCU Name 2', 'JCU Name 3', 'JCU Name 4']

class Project(Base):
    order_counter = itertools.count()

    __tablename__ = 'project'

    id = Column(Integer, ca_order=next(order_counter), primary_key=True, ca_widget=deform.widget.HiddenWidget(), ca_missing=-1)
    project_creator = Column(String(100), ca_order=next(order_counter),ca_widget=deform.widget.HiddenWidget())

    #--------------Setup--------------------
    project_title = Column(String(512), ca_order=next(order_counter), ca_widget=deform.widget.TextInputWidget(css_class="full_width"), ca_page="setup", ca_force_required=True,
#                ca_group_start="test", ca_group_description="test description", ca_group_collapsed=False,
                ca_placeholder="eg. Temperature deviation across rainforest canopy elevations",
                ca_title="Project Title", ca_description="<p>A descriptive title that will make the generated records easy to search:</P>" \
                                                         "<ul><li>The title should be a concise what and why including relevant keywords.</li>" \
                                                         "<li>Keep the description relevant to all generated records.</li>" \
                                                         "<li>The title should be unique to the data, ie. do not use the publication title as the data title.</li></ul>")

    data_manager = Column(String(256), ca_order=next(order_counter), ca_title="Data Manager", ca_page="setup", ca_force_required=True,
        ca_widget=deform.widget.AutocompleteInputWidget(min_length=1, values=choices),
        ca_placeholder="eg. TODO: data manager of artificial tree",
        ca_description="Primary contact for the project, this should be the person in charge of the data and actively working on the project.<br /><br />" \
                       "<i>Autocomplete from most universities and large organisations, if the person you are trying to select isn't available please organise an external JCU account for them.</i>")
    project_lead = Column(String(256), ca_order=next(order_counter), ca_title="Project Lead", ca_page="setup",
        ca_widget=deform.widget.AutocompleteInputWidget(min_length=1, values=choices), ca_force_required=True,
        ca_placeholder="eg. Dr Jeremy Vanderwal",
        ca_description="Head supervisor of the project that should be contacted when the data manager is unavailable.<br /><br />" \
                       "<i>Autocomplete from most universities and large organisations, if the person you are trying to select isn't available please organise an external JCU account for them.</i>")

    #---------------------description---------------------
    brief_description = Column(Text(), ca_order=next(order_counter), ca_page="description",
                    ca_placeholder="eg.  TODO: Get a well written brief description for the artificial tree project.",
                    ca_widget=deform.widget.TextAreaWidget(rows=6), ca_title="Brief Description",
                    ca_description="A short description (Approx. 6 lines) of the research done, why the research was done and the collection and research methods used:" \
                                   "<ul><li>Write this description in lay-mans terms targeted for the general population to understand.</li>" \
                                   "<li>A short description of the <i>project level</i> where and when can also be included.</li>" \
                                   "<li>Note: Keep the description relevant to all generated records.</li></ul>")
    full_description = Column(Text(), ca_order=next(order_counter), ca_widget=deform.widget.TextAreaWidget(rows=20), ca_page="description",
        ca_title="Full Description", ca_placeholder="eg.  TODO: Get a well written full description for the artificial tree project.",
        ca_description="A full description (Approx. 10-20 lines) of the research done, why the research was done and the collection and research methods used:" \
                    "<ul><li>Write this description targeted for other researchers  to understand (include the technicalities).</li>" \
                    "<li>Information about the research dataset/collection, registry/repository, catalogue or index, including its characteristics and features, eg. This dataset contains observational data, calibration files and catalogue information collected from the Mount Stromlo Observatory Facility.</li>" \
                    "<li>If applicable: the scope; details of entities being studied or recorded; methodologies used.</li>"
                    "<li>Note: Keep the description relevant to all generated records.</li></ul>")


    #---------------------metadata---------------------
    #-------------Subject--------------------
    keywords = relationship('Keyword', ca_order=next(order_counter), ca_page="metadata",
        ca_group_collapsed=False, ca_group_start='subject', ca_group_title="Area of Research (Subject)",
        ca_group_description="",
        ca_description="Enter keywords that users are likely to search on when looking for this projects data.")

    fieldOfResearch = relationship('FieldOfResearch', ca_order=next(order_counter), ca_title="Fields of Research", ca_page="metadata",
        ca_widget=deform.widget.SequenceWidget(template='multi_select_sequence'),
        ca_description="Select or enter applicable Fields of Research (FoR) from the drop-down menus, and click the 'Add Field Of Research' button (which is hidden until a code is selected)."
        , ca_missing="")
    #    colander.SchemaNode(colander.String(), title="Fields of Research",
    #        placeholder="To be redeveloped similar to ReDBox", description="Select relevant FOR code/s. ")
#
    socioEconomicObjective = relationship('SocioEconomicObjective', ca_order=next(order_counter), ca_title="Socio-Economic Objectives", ca_page="metadata",
        ca_widget=deform.widget.SequenceWidget(template='multi_select_sequence'),
        ca_description="Select relevant Socio-Economic Objectives below.", ca_missing="")

#    researchThemes = Column(String(),
#
#        ca_group_start="research_themes", ca_group_title="Research Themes",ca_group_validator=research_theme_validator,
#        ca_description="Select one or more of the 4 themes, or \'Not aligned to a University theme\'.", required=True)

        #-------Research themese---------------------
    ecosystems_conservation_climate = Column(Boolean(), ca_order=next(order_counter), ca_widget=deform.widget.CheckboxWidget(), ca_page="metadata",
        ca_title='Tropical Ecosystems, Conservation and Climate Change',
        ca_group_start="research_themes", ca_group_title="Research Themes",ca_group_validator=research_theme_validator,
        ca_group_description="Select one or more of the 4 themes, or \'Not aligned to a University theme\'.",
        ca_group_required=True,)
    industries_economies = Column(Boolean(), ca_order=next(order_counter),ca_widget=deform.widget.CheckboxWidget(), ca_page="metadata",
        ca_title='Industries and Economies in the Tropics')
    peoples_societies = Column(Boolean(), ca_order=next(order_counter), ca_widget=deform.widget.CheckboxWidget(), ca_page="metadata",
        ca_title='Peoples and Societies in the Tropics')
    health_medicine_biosecurity = Column(Boolean(), ca_order=next(order_counter), ca_widget=deform.widget.CheckboxWidget(), ca_page="metadata",
        ca_title='Tropical Health, Medicine and Biosecurity')
    not_aligned = Column(Boolean(), ca_order=next(order_counter), ca_widget=deform.widget.CheckboxWidget(), ca_page="metadata",
        ca_title='Not aligned to a University theme',
        ca_group_end="research_themes")
        #------------end Research themes--------------


        #-------typeOfResearch---------------------
    researchTypes = (
        ('applied', '<b>Applied research</b> is original work undertaken primarily to acquire new knowledge with a specific application in view. It is undertaken either to determine possible uses for the findings of basic research or to determine new ways of achieving some specific and predetermined objectives.'),
        ('experimental', '<b>Experimental development</b> is systematic work, using existing knowledge gained from research or practical experience, that is directed to producing new materials, products or devices, to installing new processes, systems and services, or to improving substantially those already produced or installed.'),
        ('pure_basic', '<b>Pure basic research</b> is experimental and theoretical work undertaken to acquire new knowledge without looking for long term benefits other than the advancement of knowledge.'),
        ('pure_strategic', '<b>Strategic basic research</b> is experimental and theoretical work undertaken to acquire new knowledge directed into specified broad areas in the expectation of useful discoveries. It provides the broad base of knowledge necessary for the solution of recognised practical problems.'))

    typeOfResearch = Column(String(50), ca_order=next(order_counter), ca_page="metadata",
        ca_group_end="subject",
        ca_widget=deform.widget.RadioChoiceWidget(values=researchTypes),
        ca_validator=OneOfDict(researchTypes[1:]),
        ca_title="Type of Research Activity",
#        ca_description="1297.0 Australian Standard Research Classification (ANZSRC) 2008. </br></br>"\
#                    "<b>Pure basic research</b> is experimental and theoretical work undertaken to acquire new knowledge without looking for long term benefits other than the advancement of knowledge.</br></br>"\
#                    "<b>Strategic basic research</b> is experimental and theoretical work undertaken to acquire new knowledge directed into specified broad areas in the expectation of useful discoveries. It provides the broad base of knowledge necessary for the solution of recognised practical problems.</br></br>"\
#                    "<b>Applied research</b> is original work undertaken primarily to acquire new knowledge with a specific application in view. It is undertaken either to determine possible uses for the findings of basic research or to determine new ways of achieving some specific and predetermined objectives.</br></br>"\
#                    "<b>Experimental development</b> is systematic work, using existing knowledge gained from research or practical experience, that is directed to producing new materials, products or devices, to installing new processes, systems and services, or to improving substantially those already produced or installed."
    )
        #------------end typeOfResearch--------------


    #-------------coverage--------------------
    time_period_description = Column(String(256), ca_order=next(order_counter), ca_title="Time Period (description)", ca_page="metadata",
        ca_group_start="coverage", ca_group_collapsed=False,
        ca_placeholder="eg. Summers of 1996-2006", ca_missing="",
        ca_description="Provide a textual representation of the time period such as world war 2 or more information on the time within the dates provided.")
    date_from = Column(Date(), ca_order=next(order_counter), ca_placeholder="", ca_title="Date From", ca_page="metadata",
        ca_description='The date that data will start being collected.')
    date_to = Column(Date(), ca_order=next(order_counter), ca_title="Date To", ca_page="metadata",
        ca_description='The date that data will stop being collected.', ca_missing=colander.null)
    location_description = Column(String(512), ca_order=next(order_counter), ca_title="Location (description)", ca_page="metadata",
        ca_description="Textual description of the location such as Australian Wet Tropics or further information such as elevation."
        , ca_missing="", ca_placeholder="eg. Australian Wet Tropics, Great Barrier Reef, 1m above ground level")
    coverage_map = relationship('Location', ca_order=next(order_counter), ca_title="Location Map", ca_widget=deform.widget.SequenceWidget(template='map_sequence'), ca_page="metadata",
        ca_group_end="coverage", ca_child_widget=deform.widget.MappingWidget(template="inline_mapping"),
        ca_missing=colander.null, ca_description=
        "<p>Geospatial location relevant to the research dataset/collection, registry/repository, catalogue or index. This may describe a geographical area where data was collected, a place which is the subject of a collection, or a location which is the focus of an activity, eg. coordinates or placename.</p>"\
        "<p>You may use the map to select an area, or manually enter a correctly formatted set of coordinates or a value supported by a standard such as a country code, a URL pointing to an XML based description of spatial coverage or free text describing a location."\
        "</p><p>If you wish to generate a map display in Research Data Australia, it is strongly advised that you use <b>DCMI Box</b> for shapes, or <b>DCMI Point</b> for points.</p><p>"\
        "Formats supported by the map widget:"\
        "<ul><li><a href=\"http://www.opengeospatial.org/standards/gml\" target=\"_blank\">GML</a> - OpenGIS Geography Markup Language (GML) Encoding Standard</li>"\
        "<li><a href=\"http://code.google.com/apis/kml/\" target=\"_blank\">KML</a> - Keyhole Markup Language developed for use with Google Earth</li>"\
        "<li><a href=\"http://dublincore.org/documents/dcmi-box\" target=\"_blank\">ISO19319dcmiBox</a> - DCMI Box notation derived from bounding box metadata conformant with the iso19139 schema</li>"\
        "<li><a href=\"http://dublincore.org/documents/dcmi-point\" target=\"_blank\">DCMIPoint</a> - spatial location information specified in DCMI Point notation</li></ul>"\
        "<p>When using the map to input shapes/points, only the above formats are supported. You can use the 'Find location' feature to pan the map to an area you are interested in, but you still need to select a map region to store geospatial data.</p>"\
        "<p>Formats available for manual data entry:</p>"\
        "<ul><li><a href=\"http://www.topografix.com/gpx.asp\" target=\"_blank\">GPX</a> - the GPS Exchange Format</li>"\
        "<li><a href=\"http://www.iso.org/iso/country_codes/iso_3166_code_lists.htm\" target=\"_blank\">ISO3166</a> - ISO 3166-1 Codes for the representation of names of countries and their subdivisions - Part 1: Country codes</li>"\
        "<li><a href=\"http://www.iso.org/iso/country-codes/background_on_iso_3166/iso_3166-2.htm\" target=\"_blank\">ISO31662</a> - Codes for the representation of names of countries and their subdivisions - Part 2: Country subdivision codes</li>"\
        "<li><a href=\"http://code.google.com/apis/kml/\" target=\"_blank\">kmlPolyCoords</a> - A set of KML long/lat co-ordinates defining a polygon as described by the KML coordinates element</li>"\
        "<li><a href=\"http://code.google.com/apis/kml/\" target=\"_blank\">gmlKmlPolyCoords</a> - A set of KML long/lat co-ordinates derived from GML defining a polygon as described by the KML coordinates element but without the altitude component</li>"\
        "<li><strong>Text</strong> - free-text representation of spatial location. Use this to record place or region names where geospatial notation is not available. In ReDBox this will search against the Geonames database and return a latitude and longitude value if selected. This will store as a DCMIPoint which in future will display as a point on a Google Map in Research Data Australia.</li></ul>")

    #-------------associations--------------------
    parties = relationship('Party', ca_title="People", ca_order=next(order_counter), ca_widget=deform.widget.SequenceWidget(min_len=1), ca_missing="", ca_page="metadata",
            ca_group_start="associations", ca_group_collapsed=False, ca_group_title="Associations",
            ca_description="Enter the details of associated people as described by the dropdown box.")
    collaborators = relationship('Collaborator', ca_order=next(order_counter), ca_page="metadata",
        ca_description="Names of other collaborators in the research project where applicable, this may be a person or organisation/group of some type."
        , ca_missing="")
    related_publications = relationship('WebResource', ca_order=next(order_counter), ca_title="Related Publications", ca_page="metadata",
        ca_child_widget=deform.widget.MappingWidget(template="inline_mapping"), ca_child_title="Related Publication",
        ca_description="Include URL/s to any publications underpinning the research dataset/collection, registry/repository, catalogue or index.")
    related_websites = relationship('WebResource', ca_order=next(order_counter), ca_title="Related Websites", ca_page="metadata", ca_child_title="Related Website",
        ca_description="Include URL/s for the relevant website.", ca_child_widget=deform.widget.MappingWidget(template="inline_mapping"))
    activities = Column(String(256), ca_order=next(order_counter), ca_title="Grants (Activity)", ca_page="metadata",
        ca_description="Enter details of which activities are associated with this record.", ca_missing="",
        ca_placeholder="TODO: Autocomplete from Mint/Mint DB")
    services = Column(String(256), ca_order=next(order_counter), ca_placeholder="Autocomplete - Mint/Mint DB", ca_page="metadata",
        ca_description="Indicate any related Services to this Collection. A lookup works against Mint, or you can enter known information about remote Services."
        , ca_missing="",
        ca_group_end="associations")
    #-------------legal--------------------
    access_rights = Column(String(256), ca_order=next(order_counter), ca_title="Access Rights", ca_default="Open access", ca_page="metadata",
        ca_group_start="legality", ca_group_collapsed=False, ca_group_title="Licenses & Access Rights",
        ca_description="Information about access to the collection or service, including access restrictions or embargoes based on privacy, security or other policies. A URI is optional.</br></br>"\
                            "eg. Contact Chief Investigator to negotiate access to the data.</br></br>"\
                            "eg. Embargoed until 1 year after publication of the research.")
    access_rights_url = Column(String(256), ca_order=next(order_counter), ca_title="URL", ca_missing="", ca_page="metadata",)

    rights = Column(String(256), ca_order=next(order_counter), ca_placeholder="TODO: replaced with default license", ca_missing="", ca_title="Usage Rights", ca_page="metadata",
        ca_description="Information about rights held in and over the collection such as copyright, licences and other intellectual property rights, eg. This dataset is made available under the Public Domain Dedication and License v1.0 whose full text can be found at: <b>http://www.opendatacommons.org/licences/pddl/1.0/</b></br>"\
                        "A URI is optional. ")
    rights_url = Column(String(256), ca_order=next(order_counter), ca_title="URL", ca_missing="", ca_page="metadata",)
    #    TODO: Link to external sources

    licenses = (
               ('none', 'No License'),
               ('creative_commons_by', 'Creative Commons - Attribution alone (by)'),
               ('creative_commons_bync', 'Creative Commons - Attribution + Noncommercial (by-nc)'),
               ('creative_commons_bynd', 'Creative Commons - Attribution + NoDerivatives (by-nd)'),
               ('creative_commons_bysa', 'Creative Commons - Attribution + ShareAlike (by-sa)'),
               ('creative_commons_byncnd', 'Creative Commons - Attribution + Noncommercial + NoDerivatives (by-nc-nd)'),
               ('creative_commons_byncsa', 'Creative Commons - Attribution + Noncommercial + ShareAlike (by-nc-sa)'),
               ('restricted_license', 'Restricted License'),
               ('other', 'Other'),
               )
    license = Column(String(256), ca_order=next(order_counter), ca_title="License", ca_placeholder="creative_commons_by", ca_page="metadata",
        ca_default="creative_commons_by",
        ca_widget=deform.widget.SelectWidget(values=licenses, template="select_with_other"),
        ca_description="This list contains data licences that this server has been configured with. For more information about Creative Commons licences please <a href=\'http://creativecommons.org.au/learn-more/licences\' alt=\'licenses\'>see here</a>. ")

    name = Column(String(256), ca_order=next(order_counter), ca_title="License Name", ca_placeholder="", ca_missing="", ca_page="metadata",
        ca_group_start="other_license", ca_group_title="Other", ca_group_description="If you want to use a license not included in the above list you can provide details below.</br></br>"\
                                "<ul><li>If you are using this field frequently for the same license it would make sense to get your system administrator to add the license to the field above.</li>"\
                                "<li>If you provide two licenses (one from above, plus this one) only the first will be sent to RDA in the RIF-CS.</li>"\
                                "<li>Example of another license: http://www.opendefinition.org/licenses</li></ul>")
    license_url = Column(String(256), ca_order=next(order_counter), ca_title="License URL", ca_placeholder="", ca_missing="", ca_page="metadata",
        ca_group_end="legality")

    #-------------citation--------------------
    title = Column(String(512), ca_order=next(order_counter), ca_placeholder="Mr, Mrs, Dr etc.", ca_missing="", ca_page="metadata",
        ca_group_collapsed=False, ca_group_start='citation', ca_group_title="Citation",
        ca_group_description="Provide metadata that should be used for the purposes of citing this record. Sending a citation to RDA is optional, but if you choose to enable this there are quite specific mandatory fields that will be required by RIF-CS.")
    creators = relationship('Creator', ca_order=next(order_counter), ca_missing=None, ca_page="metadata",)
    edition = Column(String(256), ca_order=next(order_counter), ca_missing="", ca_page="metadata",)
    publisher = Column(String(256), ca_order=next(order_counter), ca_page="metadata")
    place_of_publication = Column(String(512), ca_order=next(order_counter), ca_title="Place of publication", ca_page="metadata")
    dates = relationship('CitationDate', ca_order=next(order_counter), ca_title="Date(s)", ca_page="metadata")
    url = Column(String(256), ca_order=next(order_counter), ca_title="URL", ca_page="metadata")
    context = Column(String(512), ca_order=next(order_counter), ca_placeholder="citation context", ca_missing="", ca_page="metadata",
        ca_group_end='citation')
    #-------------additional_information--------------------
    retention_periods = (
        ("indefinite", "Indefinite"), ("1", "1 Year"), ("5", "5 Years"), ("7", "7 Years"), ("10", "10 Years"),
        ("15", "15 Years"))
    retention_period = Column(String(50), ca_order=next(order_counter), ca_title="Retention period", ca_page="metadata",
        ca_group_start="additional_information", ca_group_collapsed=False, ca_group_title="Additional Information",
        ca_widget=deform.widget.SelectWidget(values=retention_periods),
        ca_description="Record the period of time that the data must be kept in line with institutional/funding body retention policies.")
    national_significance = Column(Boolean(), ca_order=next(order_counter), ca_title="Is the data nationally significant?", ca_page="metadata",
        ca_widget=deform.widget.RadioChoiceWidget(values=(("true", "Yes"), ("false", "No"))),
        ca_description="Do you know or believe that this projects data may be Nationally Significant?")
    attachments = relationship('Attachment', ca_order=next(order_counter), ca_missing=None, ca_page="metadata", ca_child_widget=deform.widget.MappingWidget(template="inline_mapping"))
    notes = relationship('Note', ca_order=next(order_counter), ca_description="Enter administrative notes as required.", ca_missing=None, ca_page="metadata",
        ca_group_end="additional_information")

    #-----------------------------Method page----------------------------------------------------------
    overall_method_description = Column(Text(), ca_order=next(order_counter), ca_title="Overall methods description", ca_page="methods",
            ca_widget=deform.widget.TextAreaWidget(rows=5),
            ca_placeholder="Provide an overview of all the data collection methods used in the project and why those methods were chosen.",
            ca_description="Provide a description for all data input methods used in the project.  This will be used as the description for data collection in the project metadata record and will provide users of your data with an overview of what the project is researching.")
    methods = relationship('Method', ca_title="Methods", ca_widget=deform.widget.SequenceWidget(min_len=1), ca_order=next(order_counter), ca_page="methods",
        ca_child_collapsed=False,
        ca_description="Add 1 method for each type of data collection method (eg. SOS temperature sensors, manually entered field observations using a form or files retrieved by polling a server...)")

    #----------------------------Dataset page------------------------------------------
    # The datasets page is dynamically generated from user input on the methods page, therefore a static
    # ColanderAlchemy schema will not be able to generate the required deform schemas:
    #   * Setup the ColanderAlchemy schema to correctly create the database
    #   * Dynamically alter the generated schema in the view
    datasets = relationship('Dataset', ca_widget=deform.widget.SequenceWidget(min_len=1), ca_order=next(order_counter), ca_page="datasets",
        ca_child_collapsed=False,)

    #-----------------------------------------Submit page---------------------------------------------------
    project_notes = relationship("ProjectNote", ca_order=next(order_counter), ca_page="submit",
        ca_description="<b>TODO: Select the method this dataset is for.</b><br/><br/>Project comments that are only relevant to the provisioning system (eg. comments as to why the project was reopened after the creator submitted it).")