import ConfigParser
from collections import OrderedDict
import itertools
import logging
import sys
import colander
from pyramid.security import Allow, Everyone
from sqlalchemy.dialects.mysql.base import DOUBLE
from sqlalchemy.engine import create_engine
from sqlalchemy.schema import ForeignKey, Table
from zope.sqlalchemy import ZopeTransactionExtension
from simplesos.client import SOSVersions
from colanderalchemy.declarative import Column, relationship
from jcudc24provisioning.models.ca_model import CAModel
import deform
from sqlalchemy import (
    Integer,
    Text,
    Float, INTEGER)
from sqlalchemy.types import String, Boolean, Date
from jcudc24provisioning.models.common_schemas import OneOfDict
from jcudc24provisioning.models.common_schemas import upload_widget
from jcudc24provisioning.models.metadata_exporters import ReDBoxExportWrapper

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    mapper)
from jcudc24provisioning.views.deform_widgets import MethodSchemaWidget, ConditionalCheckboxMapping
from jcudc24provisioning.views.mint_lookup import MintLookup

#config = ConfigParser.SafeConfigParser()
#config.read('../../development.ini')
#db_engine = create_engine(config.get("app:main", "sqlalchemy.url"), connect_args={'pool_recycle': 3600, 'echo': False},) #connect_args={'reconnect':True})
#db_engine.connect()
#DBSession = scoped_session(sessionmaker(bind=db_engine))
import re

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

logger = logging.getLogger(__name__)


def research_theme_validator(form, value):
    error = True
    exc = colander.Invalid(form, 'At least 1 research theme or Not aligned needs to be selected')

    for key, selected in value.items():
        if selected:
            error = False

#        exc[key] = 'At least 1 research theme needs to be selected'


    if error:
        raise exc

#@cache_region('long_term')
@colander.deferred
def getFORCodes(node, kw):
    FOR_CODES_FILE = kw['settings'].get("provisioning.for_codes", {})

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
@colander.deferred
def getSEOCodes(node, kw):
    SEO_CODES_FILE = kw['settings'].get("provisioning.seo_codes", {})

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

def sequence_required_validator(form, value):
        if not isinstance(value, list) or len(value) < 1:
            exc = colander.Invalid(form, 'Required.')
            raise exc

class FieldOfResearch(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'field_of_research'
    id = Column(Integer, primary_key=True, ca_order=next(order_counter), ca_force_required=False, nullable=False, ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'),ca_order=next(order_counter),  nullable=False, ca_widget=deform.widget.HiddenWidget())

    field_of_research = Column(String(50), ca_order=next(order_counter), ca_title="Field Of Research", ca_widget=deform.widget.TextInputWidget(template="readonly/textinput"),
        ca_data=getFORCodes)


class SocioEconomicObjective(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'socio_economic_objective'
    id = Column(Integer, primary_key=True, ca_order=next(order_counter), nullable=False, ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'), ca_order=next(order_counter), nullable=False, ca_widget=deform.widget.HiddenWidget())

    socio_economic_objective = Column(String(50), ca_order=next(order_counter), ca_title="Socio-Economic Objective", ca_widget=deform.widget.TextInputWidget(template="readonly/textinput"),
    ca_data=getSEOCodes)

class Person(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'person'
    id = Column(Integer, primary_key=True, ca_order=next(order_counter), nullable=False, ca_widget=deform.widget.HiddenWidget())

    title = Column(String(5), ca_title="Title", ca_order=next(order_counter), ca_placeholder="eg. Mr, Mrs, Dr",)
    given_name = Column(String(256), ca_order=next(order_counter), ca_title="Given name")
    family_name = Column(String(256), ca_order=next(order_counter), ca_title="Family name")
    email = Column(String(256), ca_order=next(order_counter), ca_missing="", ca_validator=colander.Email())

relationship_types = (
        ("select", "---Select One---"), ("owner", "Owned by"), ("manager", "Managed by"), ("associated", "Associated with"),
        ("aggregated", "Aggregated by")
        , ("enriched", "Enriched by"))

class Party(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'party'
    id = Column(Integer, primary_key=True, nullable=False, ca_force_required=False, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
#    person_id = Column(Integer, ForeignKey('person.id'), ca_order=next(order_counter), nullable=False, ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'), ca_order=next(order_counter), nullable=False, ca_widget=deform.widget.HiddenWidget())

    party_relationship = Column(String(100), ca_name="dc:creator.foaf:Person.0.jcu:relationshipType", ca_order=next(order_counter), ca_title="This project is",
        ca_widget=deform.widget.SelectWidget(values=relationship_types),
        ca_validator=OneOfDict(relationship_types[1:]),)

    identifier = Column(String(100), ca_name="dc:creator.foaf:Person.0.dc:identifier", ca_order=next(order_counter), ca_title="Persistent Identifier", ca_force_required=True,
        ca_widget=deform.widget.AutocompleteInputWidget(min_length=1, values='/search/parties/', template="mint_autocomplete_input", size="70", delay=10))
#    person = relationship('Person', ca_order=next(order_counter), uselist=False)

class Creator(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'creator'
    id = Column(Integer, primary_key=True, nullable=False, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'), ca_order=next(order_counter), nullable=False, ca_widget=deform.widget.HiddenWidget())

    title = Column(String(5), ca_name="dc:biblioGraphicCitation.dc:hasPart.locrel:ctb.0.foaf:title", ca_title="Title", ca_order=next(order_counter), ca_placeholder="eg. Mr, Mrs, Dr",)
    given_name = Column(String(256), ca_name="dc:biblioGraphicCitation.dc:hasPart.locrel:ctb.0.foaf:givenName", ca_order=next(order_counter), ca_title="Given name")
    family_name = Column(String(256), ca_name="dc:biblioGraphicCitation.dc:hasPart.locrel:ctb.0.foaf:familyName", ca_order=next(order_counter), ca_title="Family name")
    email = Column(String(256), ca_order=next(order_counter), ca_missing="", ca_validator=colander.Email())


class Keyword(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'keyword'
    id = Column(Integer, primary_key=True, ca_force_required=False, nullable=False, ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'), ca_force_required=False, nullable=False, ca_widget=deform.widget.HiddenWidget())

    keyword = Column(String(512), ca_name="dc:subject.vivo:keyword.0.rdf:PlainLiteral")


class Collaborator(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'collaborator'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'), nullable=False, ca_widget=deform.widget.HiddenWidget())

    collaborator = Column(String(256), ca_title="Collaborator", ca_name="dc:contributor.locrel:clb.0.foaf:Agent",
        ca_placeholder="eg. CSIRO, University of X, Prof. Jim Bloggs, etc.")


class CitationDate(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'citation_date'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'), nullable=False, ca_widget=deform.widget.HiddenWidget())

    dateType = Column(String(100), ca_name="sourced from citationDateType.json", ca_title="Date type",
        ca_widget=deform.widget.TextInputWidget(size="40", css_class="full_width"))
    archivalDate = Column(Date(), ca_name="dc:biblioGraphicCitation.dc:hasPart.dc:date.0.dc:type.skos:prefLabel", ca_title="Date")


attachment_types = (("data", "Data file"), ("supporting", "Supporting material"), ("readme", "Readme"))
class Attachment(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'attachment'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'),  nullable=False, ca_widget=deform.widget.HiddenWidget())

    type = Column(String(100), ca_name="attachment_type", ca_widget=deform.widget.SelectWidget(values=attachment_types),
        ca_validator=colander.OneOf(
            [attachment_types[0][0], attachment_types[1][0], attachment_types[2][0]]),
        ca_title="Attachment type", ca_css_class="inline")
    attachment = Column(String(512), ca_name="filename",  ca_widget=upload_widget, ca_type = deform.FileData(), ca_missing=colander.null)

    note = Column(Text(), ca_name="notes")
#    ca_params={'widget' : deform.widget.HiddenWidget()}


class Note(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'note'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'),  nullable=False, ca_widget=deform.widget.HiddenWidget())

    note = Column(Text(), ca_widget=deform.widget.TextAreaWidget())

    def __init__(self, note):
        self.note = note

class Region(CAModel, Base):
    __tablename__ = 'region'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    dam_id = Column(Integer, nullable=True, ca_widget=deform.widget.HiddenWidget())
    dam_version = Column(String(128), ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'), nullable=True, ca_widget=deform.widget.HiddenWidget())
    # TODO: Regions


location_validator = colander.Regex(
    re.compile(r"""(point\([+-]?\d*\.?\d* [+-]?\d*\.?\d*\))|(polygon\(\(([+-]?\d*\.?\d*\s[+-]?\d*\.?\d*,?\s?)*\)\))|(linestring\(([+-]?\d*\.?\d*\s[+-]?\d*\.?\d*,?\s?)*\))""", re.I),
    "Must be valid WTK"
)

#float_validator = colander.Regex(
#    re.compile(r"""(((\.\d*)?)|(\d+(\.\d*)?))$"""),
#    "Must be a valid decimal number"
#)
#
#integer_validator = colander.Regex(
#    re.compile(r"""\d*$"""),
#    "Must be a valid decimal number"
#)

class Location(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'location'
    id = Column(Integer, primary_key=True, ca_force_required=False, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dam_id = Column(Integer, nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dam_version = Column(String(128), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    metadata_id = Column(Integer, ForeignKey('metadata.id'), nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'), nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    name = Column(String(256), ca_force_required=True,ca_order=next(order_counter))
    location = Column(String(512), ca_validator=location_validator, ca_name="dc:coverage.vivo:GeographicLocation.0.redbox:wktRaw", ca_widget=deform.widget.TextInputWidget(css_class='map_location'),ca_order=next(order_counter),
        ca_force_required=True, ca_child_widget=deform.widget.TextInputWidget(regex_mask="^(POINT\([+-]?\d*\.?\d* [+-]?\d*\.?\d*\)) |(POLYGON\(\(([+-]?\d*\.?\d*\s[+-]?\d*\.?\d*,?\s?)*\)\))|(LINESTRING\(([+-]?\d*\.?\d*\s[+-]?\d*\.?\d*,?\s?)*\))$"),
        ca_help="<a href='http://en.wikipedia.org/wiki/Well-known_text#Geometric_Objects' title='Well-known Text (WKT) markup reference'>WTK format reference</a>")

    elevation = Column(Float(),ca_order=next(order_counter), ca_help="Elevation in meters from mean sea level", ca_widget=deform.widget.TextInputWidget(regex_mask="^(((\\\\.\\\\d*)?)|(\\\\d+(\\\\.\\\\d*)?))$", strip=False))
    # regions = relationship("Region", ca_widget=deform.widget.HiddenWidget())

    def is_point(self):
        return self.location[:5] == "POINT"

    def get_latitude(self):
        return 0.0

    def get_longitude(self):
        return 0.0

    def get_points(self):
        return [[]]

class LocationOffset(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'location_offset'
    id = Column(Integer, primary_key=True, ca_force_required=False, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dam_id = Column(Integer, nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dam_version = Column(String(128), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'), nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    data_entry_id = Column(Integer, ForeignKey('data_entry.id'), nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    x = Column(Float(), ca_title="Lattitude Offset (meters)",ca_order=next(order_counter), ca_placeholder="eg. 1 is East 3m", ca_widget=deform.widget.TextInputWidget(size=10, css_class="full_width", regex_mask="^(((\\\\.\\\\d*)?)|(\\\\d+(\\\\.\\\\d*)?))$", strip=False))
    y = Column(Float(), ca_title="Longitude Offset (meters)",ca_order=next(order_counter), ca_placeholder="eg. 1 is North 3m", ca_widget=deform.widget.TextInputWidget(size=10, css_class="full_width", regex_mask="^(((\\\\.\\\\d*)?)|(\\\\d+(\\\\.\\\\d*)?))$", strip=False))
    z = Column(Float(), ca_title="Elevation Offset (meters)",ca_order=next(order_counter), ca_placeholder="eg. 1 is Higher 3m", ca_widget=deform.widget.TextInputWidget(size=10, css_class="full_width", regex_mask="^(((\\\\.\\\\d*)?)|(\\\\d+(\\\\.\\\\d*)?))$", strip=False))

    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z


class DataEntry(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'data_entry'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    dam_id = Column(Integer, nullable=True, ca_widget=deform.widget.HiddenWidget())
    dam_version = Column(String(128), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'), nullable=True, ca_widget=deform.widget.HiddenWidget())

class RelatedPublication(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'related_publication'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'), nullable=False, ca_widget=deform.widget.HiddenWidget())

    title = Column(String(512), ca_name="dc:relation.swrc:Publication.0.dc:title", ca_title="Title", ca_placeholder="eg. TODO", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40), ca_force_required=True)
    url = Column(String(512), ca_validator=colander.url, ca_name="dc:relation.swrc:Publication.0.dc:identifier", ca_title="URL", ca_placeholder="eg. http://www.somewhere.com.au", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40), ca_force_required=True)
    notes = Column(String(512), ca_name="dc:relation.swrc:Publication.0.skos:note", ca_title="Note", ca_missing="", ca_placeholder="eg. This publication provides additional information on xyz", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40))

class RelatedWebsite(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'related_website'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'), nullable=False, ca_widget=deform.widget.HiddenWidget())

    title = Column(String(512), ca_name="dc:relation.bibo:Website.0.dc:title", ca_title="Title", ca_placeholder="eg. TODO", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40), ca_force_required=True)
    url = Column(String(512), ca_validator=colander.url, ca_name="dc:relation.bibo:Website.0.dc:identifier", ca_title="URL", ca_placeholder="eg. http://www.somewhere.com.au", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40), ca_force_required=True)
    notes = Column(String(512), ca_name="dc:relation.bibo:Website.0.skos:note", ca_title="Note", ca_missing="", ca_placeholder="eg. This publication provides additional information on xyz", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40))


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
    ('radio', 'Radio buttons/Multiple choice'),
    ('file', 'File upload'),
    ('website', 'Website'),
    ('email', 'Email'),
    ('phone', 'Phone'),
    ('date', 'Date picker'),
    ('hidden', 'Hidden (Used by custom processing only)'),
)

class MethodAttachment(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'method_attachment'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('method.id'), nullable=False, ca_widget=deform.widget.HiddenWidget())

    attachment = Column(String(512),  ca_widget=upload_widget)
    note = colander.SchemaNode(colander.String(), placeholder="eg. data sheet", widget=deform.widget.TextInputWidget(css_class="full_width"))


class MethodWebsite(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'method_website'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('method.id'), nullable=False, ca_widget=deform.widget.HiddenWidget())

    title = Column(String(256), ca_title="Title", ca_placeholder="eg. Great Project Website", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40))
    url = Column(String(256), ca_validator=colander.url, ca_title="URL", ca_placeholder="eg. http://www.somewhere.com.au", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40))
    notes = Column(Text(), ca_title="Notes", ca_missing="", ca_placeholder="eg. This article provides additional information on xyz", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40))

method_schema_to_schema = Table("schema_to_schema", Base.metadata,
    Column("child_id", Integer, ForeignKey("method_schema.id"), primary_key=True),
    Column("parent_id", Integer, ForeignKey("method_schema.id"), primary_key=True)
)

# TODO: test this validator
def schema_validator(form, value):
    if not value['name']:
        exc = colander.Invalid(form)
        exc['name'] = "The schema must have a name"

    duplicates = find_duplicate_names([], [], value)
    if len(duplicates) > 0:
        if not exc:
            exc = colander.Invalid(form)

        for name in duplicates:
            exc[name] = "All field names in the schema must be unique.  Please check " + str(name)

    raise exc

def find_duplicate_names(names, duplicates, values):
    for key, value in values.items():
        if isinstance(value, list):
            for item in value:
                find_duplicate_names(names, duplicates, values)

        elif isinstance(value, dict):
            find_duplicate_names(names, duplicates, values)
        else:
            if key in names and not key[0] == '_':
                duplicates.append(key)
            else:
                names.append(key)

    return duplicates



# TODO: Test that schemas are fully recursive (eg. parents can have parents)
class MethodSchemaField(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'method_schema_field'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    method_schema_id = Column(Integer, ForeignKey('method_schema.id'),  nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    type = Column(String(100), ca_title="Field Type",
        ca_widget=deform.widget.SelectWidget(values=field_types),
        ca_description="",
        ca_placeholder="Type of field that should be shown.",ca_force_required=True)

    units = Column(String(256), ca_placeholder="eg. mm", ca_widget=deform.widget.TextInputWidget(css_class="custom_field_units"),ca_force_required=True)

    name = Column(String(256), ca_title="Name", ca_placeholder="eg. Temperature", ca_widget=deform.widget.TextInputWidget(css_class="full_width custom_field_name"),ca_force_required=True)
    description = Column(Text(), ca_title="Description", ca_placeholder="eg. Calibrated temperature reading", ca_widget=deform.widget.TextInputWidget(css_class="full_width custom_field_description"))
    placeholder = Column(String(256), ca_title="Example", ca_placeholder="eg. 26.3", ca_widget=deform.widget.TextInputWidget(css_class="full_width custom_field_example"))
    default = Column(String(256), ca_title="Default Value", ca_placeholder="Use appropriately where the user will usually enter the same value.", ca_widget=deform.widget.TextInputWidget(css_class="full_width custom_field_default"))
    values = Column(Text(), ca_title="List of Values", ca_placeholder="Provide possible selections", ca_widget=deform.widget.TextInputWidget(css_class="full_width custom_field_values"))
    validators = Column(String(256), ca_title="Validator", ca_placeholder="eg. Numerical value with decimal places or what values are expected such as for a dropdown box", ca_widget=deform.widget.TextInputWidget(css_class="full_width custom_field_validators"))
    notes = Column(String(256), ca_title="Admin Notes", ca_placeholder="eg. Please read this field from the uploaded files, it will follow a pattern like temp:xxx.xx", ca_widget=deform.widget.TextAreaWidget(css_class="full_width custom_field_notes"))

class MethodSchema(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'method_schema'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dam_id = Column(Integer, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dam_version = Column(String(128), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    method_id = Column(Integer, ForeignKey('method.id'),  nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    template_schema = Column(Boolean, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter)) # These are system schemas that users are encouraged to extend.

    schema_type = Column(String(256), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())


    name = Column(String(256), ca_order=next(order_counter), ca_title="Schema Name", ca_placeholder="eg. Temperature with sensor XYZ calibration data",
        ca_widget=deform.widget.TextInputWidget(size=40),
        ca_help="Try to enter a unique name that easily identifies this schema.")
#    nominate_as_template = Column(Boolean, ca_order=next(order_counter), ca_default=False, ca_title="Nominate this schema as a template",
#        ca_help="Use this checkbox to suggest to admins that it would be helpful for this schema to be added as a template") # These are system schemas that users are encouraged to extend.
    parents = relationship("MethodSchema",ca_order=next(order_counter),
        secondary=method_schema_to_schema,
        primaryjoin=id==method_schema_to_schema.c.child_id,
        secondaryjoin=id==method_schema_to_schema.c.parent_id,
        ca_title="Template(s) to CAModel, Base/extend your data schema from (Recommended)",
        ca_widget=deform.widget.SequenceWidget(template="method_schema_parents_sequence"),
        ca_child_title = "Parent Schema",
        ca_child_widget=deform.widget.MappingWidget(template="ca_sequence_mapping", item_template="method_schema_parents_item"),
        ca_help="Add existing schemas to use or extend from.  This makes it both easier to create the data schema (data "
                "formats) and re-use existing schemas making cross project searching possible.")

    custom_fields = relationship("MethodSchemaField", ca_order=next(order_counter), ca_child_title="Custom Field",
        cascade="all, delete-orphan",
        ca_child_widget=deform.widget.MappingWidget(item_template="method_schema_field_item"),
        ca_description="Provide details of the schema field and how it should be displayed.",
        ca_help="TODO:  This needs to be displayed better - I'm thinking a custom template that has a sidebar for options and the fields are displayed 1 per line.  All fields will be shown here (including fields from parent/extended schemas selected above).")

def custom_processing_validator(form, value):
    pass
    #TODO
#    with open(value) as f:
#        script = f.read()
#        if model.dataset_data_source.custom_processing_parameters is not None:
#            temp_params = [param.strip() for param in model.dataset_data_source.custom_processing_parameters.split(",")]
#            named_params = {'args': model.dataset_data_source.custom_processing_parameters}
#            unnamed_params = []
#            for param in temp_params:
#                if '=' in param:
#                    param_parts = param.split("=")
#                    named_params[param_parts[0]] = param_parts[1]
#                else:
#                    unnamed_params.append(param)
#
#            try:
#                script = script.format(*unnamed_params, **named_params)
#            except KeyError as e:
#                raise ValueError("Invalid custom processing parameters for {} dataset: {}".format(model.name, e.message))
#            data_source.processing_script = script
#
#    error = False
#    exc = colander.Invalid(form) # Uncomment to add a block message: , 'At least 1 research theme or Not aligned needs to be selected')
#
#    mint = MintLookup(None)
#
#    if value['publish_dataset'] is True and value['publish_date'] == colander.null:
#     exc['publish_date'] = "Required"
#     error = True
#    elif value['no_activity'] is True:
#     if mint.get_from_identifier(value['activity']) is None:
#         exc['activity'] = "The entered activity isn't a valid Mint identifier.  Please use the autocomplete feature to ensure valid values."
#         error = True
#
#    if mint.get_from_identifier(value['project_lead']) is None:
#         exc['project_lead'] = "The entered project lead isn't a valid Mint identifier.  Please use the autocomplete feature to ensure valid values."
#         error = True
#
#    if mint.get_from_identifier(value['data_manager']) is None:
#         exc['data_manager'] = "The entered data manager isn't a valid Mint identifier.  Please use the autocomplete feature to ensure valid values."
#         error = True
#
#    if error:
#     raise exc

class CustomProcessor(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'custom_processor'
    id = Column(Integer, primary_key=True, nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    custom_processor_desc = Column(String(256),ca_order=next(order_counter), ca_widget=deform.widget.TextAreaWidget(),
        ca_placeholder="eg. Extract he humidity and temperature values from the raw data file received in another dataset.",
        ca_title="Describe custom processing needs", ca_missing="", ca_description="Describe your processing "\
                    "requirements and what your uploaded script does (or what you will need help with).")

    custom_processing_parameters = Column(String(512),ca_order=next(order_counter),
            ca_description="Comma separated list of parameters.",
            ca_help="Parameters are added via python string formatting syntax, simply add %s or %(<i>name</i>)s wherever you want a parameter inserted (parameters must either be added in the correct order or be named).")

    custom_processor_script = Column(String(512), ca_type = deform.FileData(), ca_missing=colander.null ,ca_order=next(order_counter),ca_widget=upload_widget,
        ca_title="Upload custom processing script",
        ca_group_end="method",
        ca_description="Upload a custom Python script to "\
            "process the data in some way.  The processing script API can be found "\
            "<a title=\"Python processing script API\"href=\"\">here</a>.")


class FormDataSource(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'form_data_source'
    id = Column(Integer, primary_key=True, nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'),  nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))


class PullDataSource(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'pull_data_source'
    id = Column(Integer, primary_key=True, nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'),  nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    uri = Column(Text(), ca_order=next(order_counter), ca_validator=colander.url,
        ca_placeholder="eg. http://example.com.au/folder/",
        ca_description="Provide the url that should be polled for data - files will be ingested that follow the name convention of <i>TODO</i>")

    # Id of the data_entry schema field used for the datasource file
    file_field = Column(Integer, ca_order=next(order_counter),
            ca_widget=deform.widget.SelectWidget(),
            ca_description="<i>Select the schema field (field within the data type in methods) that the data source will use</i>")


    # TODO: filename_patterns
    filename_pattern=Column(String(100),ca_order=next(order_counter), ca_title="Filename Pattern (Regex)",)
#            ca_group_help="Provide a filename pattern (Regex) that identifies which files should be ingested.")
#     mime_type=Column(String(100),ca_order=next(order_counter), ca_title="File MIME Type",
#                ca_group_help="Provide a file MIME type that identifies the file content type.")

    selected_sampling = Column(String(64), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter),
        ca_group_start="sampling", ca_group_title="Data Sampling/Filtering", ca_group_collapsed=False, ca_group_validator=custom_processing_validator,
        ca_group_widget=deform.widget.MappingWidget(item_template="choice_mapping_item", template="choice_mapping"),
        ca_group_missing=colander.null)

    periodic_sampling = Column(INTEGER(),ca_order=next(order_counter), ca_title="Periodic Sampling (Collect data every X minutes)",
        ca_widget=deform.widget.TextInputWidget(regex_mask="^(\\\\d*)$", strip=False),
        ca_help="Provide the number of minutes between checks for new data.  If you require something more advanced any filtering can be achieved by adding a custom "\
                "sampling script below.</br></br>  The sampling script API can be found <a href="">here</a>.")

    cron_sampling = Column(String(100),ca_order=next(order_counter), ca_title="Cron Based Sampling (When data is collected)",
        ca_widget=deform.widget.TextInputWidget(template="chron_textinput"),
        ca_help="<p>Provide repetitive filtering condition for retrieving data using the selectors below.</p>" \
                "<p>If you require something more advanced you can provide your own cron string or any filtering can be achieved by adding a custom "\
                "sampling script below.</p><p>The sampling script API can be found <a href="">here</a></p>.")


    #    stop_conditions = Column(String(100),ca_order=next(order_counter), ca_title="Stop conditions (TODO)", ca_child_title="todo")

    custom_sampling_desc = Column(String(256),ca_order=next(order_counter), ca_widget=deform.widget.TextAreaWidget(),
        ca_group_start="custom_sampling", ca_group_title="Custom Data Sampling/Filtering",
        ca_placeholder="eg. Only ingest the first data value of every hour.",
        ca_title="Describe custom sampling needs", ca_missing="",
        ca_description="Describe your sampling requirements and what your uploaded script does, or what you will need help with.")

    custom_sampling_script = Column(String(512), ca_type = deform.FileData(), ca_missing=colander.null ,ca_order=next(order_counter),ca_widget=upload_widget,
        ca_title="Upload custom sampling script",
        ca_group_end="sampling",
        ca_description="Upload a custom Python script to "\
                       "sample the data in some way.  The sampling script API can be found "\
                       "<a title=\"Python sampling script API\"href=\"\">here</a>.")


    custom_processor_id = Column(Integer, ForeignKey('custom_processor.id'),  nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    custom_processor = relationship("CustomProcessor", uselist=False, ca_order=next(order_counter), ca_group_collapsed=False,
        ca_group_title="Custom Data Processing",  ca_group_validator=custom_processing_validator,
        ca_placeholder="eg. Extract he humidity and temperature values from the raw data file received in another dataset.",
        ca_title="Describe custom processing needs", ca_missing="", ca_description="Describe your processing "\
                                   "requirements and what your uploaded script does (or what you will need help with).")


class PushDataSource(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'push_data_source'
    id = Column(Integer, primary_key=True, nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'),  nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    api_key = Column(Text(), ca_title="API Key (Password to use this functionality)", ca_order=next(order_counter),
        ca_default="TODO: Auto-generate key",
        ca_description="The password that is needed to push your data into to this system.")

    file_field = Column(String(100), ca_order=next(order_counter),
            ca_description="<b>TODO: Redevelop into dropdown selection from schema fields that are of type file</b>")

sos_variants = (("52North", "52 North"),)
sos_versions = ((SOSVersions.v_1_0_0, "1.0.0"),)

class SOSScraperDataSource(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'sos_scraper_data_source'
    id = Column(Integer, primary_key=True, nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'),  nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    uri = Column(Text(), ca_order=next(order_counter), ca_validator=colander.url,
        ca_placeholder="eg. http://example.com.au/folder/",
        ca_description="Provide the url of the external Sensor Observation Service.")

    # Id of the data_entry schema field used for the datasource file
    data_field = Column(Integer, ca_order=next(order_counter),
        ca_widget=deform.widget.SelectWidget(),
        ca_description="<i>Select the schema field (field within the data type in methods) that the raw SOS data will be saved to.</i>")

    variant = Column(String(64), ca_order=next(order_counter), ca_widget=deform.widget.SelectWidget(values=sos_variants),
        ca_description="Select the external Sensor Observation Service (SOS) implementation variant, please contact the administrators if you require a different variant.")
    version = Column(String(64), ca_order=next(order_counter), ca_widget=deform.widget.SelectWidget(values=sos_versions),
        ca_description="Select the external Sensor Observation Service (SOS) implementation version, please contact the administrators if you require a different version.")


    selected_sampling = Column(String(64), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter),
        ca_group_start="sampling", ca_group_title="Data Sampling/Filtering", ca_group_collapsed=False,
        ca_group_widget=deform.widget.MappingWidget(item_template="choice_mapping_item", template="choice_mapping"),
        ca_group_missing=colander.null)

    periodic_sampling = Column(INTEGER(),ca_order=next(order_counter), ca_title="Periodic Sampling (Collect data every X minutes)",
        ca_widget=deform.widget.TextInputWidget(regex_mask="^(\\\\d*)$", strip=False),
        ca_help="Provide the number of minutes between checks for new data.  If you require something more advanced any filtering can be achieved by adding a custom "\
                "sampling script below.</br></br>  The sampling script API can be found <a href="">here</a>.")

    cron_sampling = Column(String(100),ca_order=next(order_counter), ca_title="Cron Based Sampling (When data is collected)",
        ca_widget=deform.widget.TextInputWidget(template="chron_textinput"),
        ca_help="<p>Provide repetitive filtering condition for retrieving data using the selectors below.</p>"\
                "<p>If you require something more advanced you can provide your own cron string or any filtering can be achieved by adding a custom "\
                "sampling script below.</p><p>The sampling script API can be found <a href="">here</a></p>.")

    custom_processor_desc = Column(String(256),ca_order=next(order_counter), ca_widget=deform.widget.TextAreaWidget(),
        ca_group_start="processing", ca_group_collapsed=False, ca_group_title="Custom Data Processing",  ca_group_validator=custom_processing_validator,
        ca_placeholder="eg. Extract he humidity and temperature values from the raw data file received in another dataset.",
        ca_title="Describe custom processing needs", ca_missing="", ca_description="Describe your processing "\
                                                                                   "requirements and what your uploaded script does (or what you will need help with).")

    custom_processing_parameters = Column(String(512),ca_order=next(order_counter),
        ca_description="Comma separated list of parameters.",
        ca_help="Parameters are added via python string formatting syntax, simply add %s or %(<i>name</i>)s wherever you want a parameter inserted (parameters must either be added in the correct order or be named).")


    custom_processor_script = Column(String(512), ca_type = deform.FileData(), ca_missing=colander.null ,ca_order=next(order_counter),ca_widget=upload_widget,
        ca_title="Upload custom processing script",
        ca_group_end="method",
        ca_description="Upload a custom Python script to "\
                       "process the data in some way.  The processing script API can be found "\
                       "<a title=\"Python processing script API\"href=\"\">here</a>.")

@colander.deferred
def dataset_select_widget(node, kw):
    if 'datasets' in kw:
        datasets = kw['datasets']
        dataset_values = []
        for dataset in datasets:
            dataset_values.append((dataset.id, dataset.name))
        return deform.widget.SelectWidget(values=dataset_values, template="source_dataset_select")


class DatasetDataSource(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'dataset_data_source'
    id = Column(Integer, primary_key=True, nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'),  nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    # TODO: Selection of datasets
    dataset_data_source_id = Column(Text(), ca_title="Source Dataset", ca_order=next(order_counter), ca_widget=dataset_select_widget,
        ca_description="The dataset to retrieve processed data from.  If there are no items to select from - there must be other datasets already setup!")

    custom_processor_desc = Column(String(256),ca_order=next(order_counter), ca_widget=deform.widget.TextAreaWidget(),
        ca_group_start="processing", ca_group_collapsed=False, ca_group_title="Custom Data Processing",  ca_group_validator=custom_processing_validator,
        ca_placeholder="eg. Extract he humidity and temperature values from the raw data file received in another dataset.",
        ca_title="Describe custom processing needs", ca_missing="", ca_description="Describe your processing "\
                    "requirements and what your uploaded script does (or what you will need help with).")

    custom_processing_parameters = Column(String(512),ca_order=next(order_counter),
            ca_description="Comma separated list of parameters.",
            ca_help="Parameters are added via python string formatting syntax, simply add %s or %(<i>name</i>)s wherever you want a parameter inserted (parameters must either be added in the correct order or be named).")

    custom_processor_script = Column(String(512), ca_type = deform.FileData(), ca_missing=colander.null ,ca_order=next(order_counter),ca_widget=upload_widget,
        ca_title="Upload custom processing script",
        ca_description="Upload a custom Python script to "\
            "process the data in some way.  The processing script API can be found "\
            "<a title=\"Python processing script API\"href=\"\">here</a>.")


class MethodTemplate(CAModel, Base):
    """
    Method templates that can be used to pre-populate a method with as well as datasets created for that method.
    """
    __tablename__ = 'method_template'
    order_counter = itertools.count()
    id = Column(Integer, ca_order=next(order_counter), primary_key=True, ca_widget=deform.widget.HiddenWidget())
    template_id = Column(Integer, ForeignKey('method.id'),  nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'),  nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

#    implementing_methods = relationship("Method", foreign_keys="method.method_template_id", ca_order=next(order_counter), ca_missing=colander.null,
#        ca_widget=deform.widget.HiddenWidget(), backref="template", ca_exclude=True)

    name = Column(String(100),ca_order=next(order_counter), ca_description="Name the template (eg. Artificial tree).")
    description = Column(String(256),ca_order=next(order_counter), ca_description="Provide a short description (<256 chars) of the template for the end user.")
    category = Column(String(100),ca_order=next(order_counter), ca_description="Category of template, this is a flexible way of grouping templates such as DRO, SEMAT or other organisational groupings.")


class Method(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'method'
    project_id = Column(Integer, ForeignKey('project.id'), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
    id = Column(Integer, ca_order=next(order_counter), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())

    method_template_id = Column(Integer, ForeignKey('method_template.id', ForeignKey('method_template.id'), use_alter=True, name="fk_method_template_id"), nullable=True, ca_order=next(order_counter), ca_title="Select a template to base this method off (Overrides all fields)",
        ca_widget=deform.widget.TextInputWidget(template="method_template_mapping", strip=False),
        ca_help="<p>Method templates provide pre-configured data collection methods and pre-fill as much information as possible to make this process as quick and easy as possible.</p>"
             "<ul><li>If you don't want to use any template, select the general category and Blank template."
             "</li><li>Please contact the administrators to request new templates.</li>",
        ca_description="<ol><li>First select the category or organisational group on the left hand side.</li>"
                    "<li>Then select the most relevant template from the list on the right hand side.</li>")

    method_name = Column(String(256), ca_order=next(order_counter),
            ca_placeholder="Searchable identifier for this input method (eg. Invertebrate observations)",
            ca_description="Descriptive, human readable name for this data collection method.  The name is used for selecting this method in the <i>Datasets</i> step.")
    method_description = Column(Text(), ca_order=next(order_counter), ca_title="Description", ca_widget=deform.widget.TextAreaWidget(),
        ca_description="Provide a description of this method, this should include what, why and how the data is being collected but <b>Don\'t enter where or when</b> as this information is relevant to the dataset, not the method.",
        ca_placeholder="Enter specific details for this method, users of your data will need to know how reliable your data is and how it was collected.")

    data_type = relationship("MethodSchema", ca_order=next(order_counter), uselist=False, ca_widget=MethodSchemaWidget(),
        cascade="all, delete-orphan",ca_title="Type of data being collected",
        ca_collapsed=False,
        ca_help="The type of data that is being collected - <b>Please extend the provided schemas where possible only use the custom fields for additional information</b> (eg. specific calibration data).</br></br>" \
                    "Extending the provided schemas allows your data to be found in a generic search (eg. if you use the temperature schema then users will find your data " \
                    "when searching for temperatures, but if you make the schema using custom fields (even if it is the same), then it won't show up in the temperature search results).",
        ca_description="Extend existing data types wherever possible - only create custom fields or schemas if you cannot find an existing schema.")

    data_sources=(
        (FormDataSource.__tablename__,"Web form/manual only"),
        (PullDataSource.__tablename__,"Pull from external file system"),
        (SOSScraperDataSource.__tablename__,"Sensor Observation Service"),
        (PushDataSource.__tablename__,"<i>(Advanced)</i> Push to this website through the API"),
        (DatasetDataSource.__tablename__,"<i>(Advanced)</i> Output from other dataset"),
    )

    data_source =  Column(String(50), ca_order = next(order_counter), ca_widget=deform.widget.RadioChoiceWidget(values=data_sources),
        ca_title="Data Source (How the data gets transferred into this system)", ca_force_required=True,
        ca_help="<p>'Web form/manual' is the default and included in all others anyway, 'Output from other dataset' provides advanced "
                "processing features and the other three methods allow automatic ingestion from compatible sensors or devices:</p>" \
                "<ul><li><b>Web form/manual only:</b> Only use an online form accessible through this interface to manually upload data (Other data sources also include this option).</li>" \
                "<li><b>Pull from external file system:</b> Setup automatic polling of an external file system from a URL location, when new files of the correct type and naming convention are found they are ingested.</li>" \
                "<li><b><i>(Advanced)</i> Push to this website through the API:</b> Use the XMLRPC API to directly push data into persistent storage, on project acceptance you will be emailed your API key and instructions.</li>" \
                "<li><b>Sensor Observation Service:</b> Set-up a sensor that implements the Sensor Observation Service (SOS) to push data into this systems SOS server.</li>" \
                "<li><b><i>(Advanced)</i> Output from other dataset:</b> Output from other dataset: </b>This allows for advanced/chained processing of data, where the results of another dataset can be further processed and stored as required.</li></ul>" \
                "<p><i>Please refer to the help section or contact the administrators if you need additional information.</i></p>",
        ca_placeholder="Select the easiest method for your project.  If all else fails, manual file uploads will work for all data types.")

    method_attachments = relationship('MethodAttachment', ca_order=next(order_counter), ca_missing=colander.null, ca_child_title="Attachment",
        cascade="all, delete-orphan",
        ca_title="Attachment (Such as datasheets, collection processes, observation forms)",
        ca_help="Attach information about this method, this is preferred to websites as it is persistent.  " \
                       "Example attachments would be sensor datasheets, documentation describing your file/data storage schema or calibration data.")

    method_website = relationship("MethodWebsite", ca_order=next(order_counter), ca_missing=colander.null,
        cascade="all, delete-orphan",ca_title="Further information website (Such as manufacturers website or supporting web resources)",
        ca_child_widget=deform.widget.MappingWidget(template="inline_mapping"), ca_child_title="Website",
        ca_help="If there are web addresses that can provide more information on your data collection method, add them here.  Examples may include manufacturers of your equipment or an article on the calibration methods used.")

    datasets = relationship("Dataset", ca_order=next(order_counter), ca_missing=colander.null,
        cascade="all, delete-orphan", ca_widget=deform.widget.HiddenWidget(), ca_exclude=True)

    method_template = relationship("MethodTemplate", primaryjoin=method_template_id==MethodTemplate.id, single_parent=True,
        ca_exclude=True, uselist=False, ca_order=next(order_counter), ca_missing=colander.null,
        cascade="all, delete-orphan", ca_widget=deform.widget.HiddenWidget())

def dataset_validator(form, value):
    error = False
    exc = colander.Invalid(form) # Uncomment to add a block message: , 'At least 1 research theme or Not aligned needs to be selected')

    mint = MintLookup(None)

    if value['publish_dataset'] is True and value['publish_date'] == colander.null:
     exc['publish_date'] = "Required"
     error = True
    elif value['no_activity'] is True:
     if mint.get_from_identifier(value['activity']) is None:
         exc['activity'] = "The entered activity isn't a valid Mint identifier.  Please use the autocomplete feature to ensure valid values."
         error = True

    if mint.get_from_identifier(value['project_lead']) is None:
         exc['project_lead'] = "The entered project lead isn't a valid Mint identifier.  Please use the autocomplete feature to ensure valid values."
         error = True

    if mint.get_from_identifier(value['data_manager']) is None:
         exc['data_manager'] = "The entered data manager isn't a valid Mint identifier.  Please use the autocomplete feature to ensure valid values."
         error = True

    if error:
     raise exc

class Dataset(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'dataset'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter),
#        ca_group_start="method", ca_group_title="Method", ca_group_schema=SelectMappingSchema,
        )
    dam_id = Column(Integer, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dam_version = Column(String(128), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    project_id = Column(Integer, ForeignKey('project.id'),  ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter),
#        ca_group_start="test_method", ca_group_title="Test Method",
        )
    method_id = Column(Integer, ForeignKey('method.id'), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    disabled = Column(Boolean,ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())

    mint_service_id = Column(String(256), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
    mint_service_uri = Column(String(256), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())

    name = Column(Text(), ca_name="dc:relation.vivo:Dataset.0.dc:title", ca_title="Dataset Name", ca_order=next(order_counter),
        ca_placeholder="Provide a textual description of this dataset.",
        ca_help="Provide a dataset specific name that is easily identifiable within this system.", ca_force_required=True)

    publish_dataset = Column(Boolean, ca_title="Publish Dataset to ReDBox", ca_default=True, ca_order=next(order_counter),
        ca_widget=deform.widget.CheckboxWidget(template="checked_conditional_input", inverted=True),
        ca_help="Publish a metadata record to ReDBox for this dataset - leave this selected unless the data isn't relevant to anyone else (eg. Raw data where other users " \
                       "will only search for the processed data).")

    publish_date = Column(Date(), ca_order=next(order_counter), ca_title="Date to make ReDBox record publicly available",
        ca_help='The date that data will start being collected.')

#    description = Column(Text(),ca_order=next(order_counter), ca_widget=deform.widget.TextAreaWidget(rows=6),
#            ca_placeholder="Provide a textual description of the dataset being collected.",
#            ca_help="Provide a dataset specific description for the metadata records.")
#
#    time_period_description = Column(String(256), ca_name="dc:coverage.redbox:timePeriod", ca_order=next(order_counter), ca_title="Time Period (description)",
#        ca_group_start="coverage", ca_group_collapsed=False, ca_group_title="Dataset Date and Location",
#        ca_placeholder="eg. Summers of 1996-2006", ca_missing="",
#        ca_help="Provide a textual representation of the time period such as world war 2 or more information on the time within the dates provided.")
#    date_from = Column(Date(), ca_name="dc:coverage.vivo:DateTimeInterval.vivo:start", ca_order=next(order_counter), ca_placeholder="", ca_title="Date data started/will start being collected",
#        ca_help="The date that data started being collected.  Note that this is the actual data date not the finding date, recording date or other date.  For example, an old letter may be found in 2013 but it was actually written in 1900 - the date to use is 1900.", ca_force_required=True)
#    date_to = Column(Date(), ca_name="dc:coverage.vivo:DateTimeInterval.vivo:end", ca_order=next(order_counter), ca_title="Date data stopped/will stop being collected", ca_page="information",
#        ca_help='The date that data will stop being collected.  Note that this is the actual data date not the finding date, recording date or other date.  For example, an old letter may be found in 2013 but it was actually written in 1900 - the date to use is 1900.', ca_missing=colander.null)
#    location_description = Column(String(512), ca_order=next(order_counter), ca_title="Location (description)",
#        ca_help="Textual description of the location such as Australian Wet Tropics."
#        , ca_missing="", ca_placeholder="eg. Australian Wet Tropics or Great Barrier Reef")

    dataset_locations = relationship('Location', ca_order=next(order_counter), ca_title="Location",
        cascade="all, delete-orphan",ca_widget=deform.widget.SequenceWidget(template='map_sequence', max_len=1, min_len=1, points_only=True, error_class="error"),
        ca_force_required=True,
        ca_child_widget=deform.widget.MappingWidget(template="inline_mapping"),
        ca_missing="", ca_help="<p>Use the drawing tools on the map and/or edit the text representations below.</p><p>Locations are represented using <a href='http://en.wikipedia.org/wiki/Well-known_text#Geometric_Objects'>Well-known Text (WKT) markup</a> in the WGS 84 coordinate system (coordinate system used by GPS).</p>")

    location_offset = relationship('LocationOffset', uselist=False, ca_order=next(order_counter), ca_title="Location Offset (optional)",
        cascade="all, delete-orphan",
        ca_group_end="coverage", ca_widget=deform.widget.MappingWidget(template="inline_mapping", show_label=True),
        ca_missing=colander.null, ca_help="Use an offset from the current location where the current location is the project location if valid, else the dataset location (eg. such as the artificial tree location is known so use z offsets for datasets).")

    form_data_source = relationship("FormDataSource", ca_order=next(order_counter), uselist=False, ca_force_required=False, cascade="all, delete-orphan",ca_collapsed=False)
    pull_data_source = relationship("PullDataSource", ca_order=next(order_counter), uselist=False, ca_force_required=False,cascade="all, delete-orphan",ca_collapsed=False)
    sos_scraper_data_source = relationship("SOSScraperDataSource", ca_order=next(order_counter), uselist=False, ca_force_required=False,cascade="all, delete-orphan",ca_collapsed=False,)
    push_data_source = relationship("PushDataSource", ca_order=next(order_counter), uselist=False, ca_force_required=False,cascade="all, delete-orphan",ca_collapsed=False,)
    dataset_data_source = relationship("DatasetDataSource", ca_order=next(order_counter), uselist=False, ca_force_required=False,cascade="all, delete-orphan",ca_collapsed=False)

    record_metadata = relationship("Metadata", uselist=False, ca_order=next(order_counter), ca_missing=colander.null,
        cascade="all, delete-orphan", ca_widget=deform.widget.HiddenWidget(), ca_exclude=True)

    method_template = relationship("MethodTemplate", ca_order=next(order_counter), ca_missing=colander.null,
        cascade="all, delete-orphan", ca_widget=deform.widget.HiddenWidget(), ca_exclude=True)


class ProjectNote(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'project_note'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
#    TODO: user_id = Column(Integer, ForeignKey('project.id'), nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    comment = Column(Text(),
        ca_placeholder="eg. Please enter all metadata, the supplied processing script has errors, please extend the existing temperature data type so that your data is searchable, etc..."
        , ca_widget=deform.widget.TextAreaWidget(rows=3))

class ProjectTemplate(CAModel, Base):
    """
    Indicate an existing project is a template that others can use to pre-populate their projects
    """
    order_counter = itertools.count()

    __tablename__ = 'project_template'
    id = Column(Integer, ca_order=next(order_counter), primary_key=True, ca_widget=deform.widget.HiddenWidget())
    order_counter = itertools.count()
    template_id = Column(Integer, ForeignKey('project.id'), nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    category = Column(String(100),ca_order=next(order_counter), ca_description="Category of template, this is a flexible way of grouping templates such as DRO, SEMAT or other organisational groupings.")
    name = Column(String(100),ca_order=next(order_counter), ca_description="Name the template (eg. Artificial tree).")
    description = Column(String(256),ca_order=next(order_counter), ca_description="Provide a short description (<256 chars) of the template for the end user.")

choices = ['JCU Name 1', 'JCU Name 2', 'JCU Name 3', 'JCU Name 4']

class UntouchedFields(CAModel, Base):
    __tablename__ = 'untouched_fields'
    order_counter = itertools.count()
    id = Column(Integer, ca_order=next(order_counter), primary_key=True, ca_widget=deform.widget.HiddenWidget())

    project_id = Column(Integer, ForeignKey('project.id'), nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'), nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    method_schema_id = Column(Integer, ForeignKey('method_schema.id'), nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    method_schema_field_id = Column(Integer, ForeignKey('method_schema_field.id'),  nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    method_id = Column(Integer, ForeignKey('method.id'),nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    field_name = Column(String(100))

# Page names below need to be synchronised with WORKFLOW_STEPS->href in workflows.py
class UntouchedPages(CAModel, Base):
    __tablename__ = 'untouched_pages'
    order_counter = itertools.count()
    id = Column(Integer, ca_order=next(order_counter), primary_key=True, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    general = Column(Boolean, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    description = Column(Boolean, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    information = Column(Boolean, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    methods = Column(Boolean, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    datasets = Column(Boolean, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

class MetadataNote(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'metadata_note'

    id = Column(Integer, ca_order=next(order_counter), primary_key=True, ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    note = Column(Text(), ca_order=next(order_counter),
            ca_placeholder="eg. TODO",
            ca_widget=deform.widget.TextAreaWidget(rows=3), ca_title="Note",)


class Metadata(ReDBoxExportWrapper, Base):
    order_counter = itertools.count()

    __tablename__ = 'metadata'

    id = Column(Integer, ca_order=next(order_counter), ca_force_required=False, primary_key=True, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'), unique=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))


    redbox_identifier = Column(String(256), ca_name="", ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    redbox_uri = Column(String(256), ca_name="dc:relation.vivo:Dataset.0.dc:identifier",ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
    ccdam_identifier = Column(String(256), ca_name="", ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    #--------------Setup--------------------
    project_title = Column(String(512), ca_order=next(order_counter), ca_name="dc:title",
        ca_widget=deform.widget.TextInputWidget(css_class="full_width"), ca_page="general", ca_force_required=True,
        ca_placeholder="eg. Temperature deviation across rainforest canopy elevations",
        ca_title="Project Title",
        ca_help="<p>A descriptive title that will make the generated records easy to search:</P>"\
                "<ul><li>The title should be a concise what and why including relevant keywords.</li>"\
                "<li>Keep the description relevant to all generated records.</li>"\
                "<li>The title should be unique to the data, ie. do not use the publication title as the data title.</li></ul>")

    # TODO: Refactor template, activity and data_manager/project_lead into setup page - use the autocomplete functionality to add details to project.
    #    template = Column(String(512), ca_order=next(order_counter), ca_page="general", ca_force_required=True,
    #        ca_description="<b>TODO: Implement templating</b>",)
    #
    #    no_activity = Column(Boolean(), ca_order=next(order_counter), ca_title="There is no associated research grant", ca_page="general",
    #        ca_description="Must be selected if a research grant isn't provided below.")
    #
    activity = Column(String(256), ca_order=next(order_counter), ca_title="Research Grant", ca_page="general",
        ca_missing="",
        ca_help="Enter the associated research grant associated with this record (this field will autocomplete).",
        ca_widget=deform.widget.AutocompleteInputWidget(min_length=1, values='/search/activities/', template="mint_autocomplete_input", delay=10))

    #    services = Column(String(256), ca_title="Services - Remove this?", ca_order=next(order_counter), ca_placeholder="Autocomplete - Mint/Mint DB", ca_page="general",
    #            ca_help="Indicate any related Services to this Collection. A lookup works against Mint, or you can enter known information about remote Services."
    #            , ca_missing="",
    #            ca_group_end="associations")


    #    data_manager = Column(String(256), ca_order=next(order_counter), ca_title="Data Manager (Primary contact)", ca_page="general", ca_force_required=True,
    #        ca_widget=deform.widget.AutocompleteInputWidget(min_length=1, values=choices),
    #        ca_placeholder="eg. TODO: data manager of artificial tree",
    #        ca_help="Primary contact for the project, this should be the person in charge of the data and actively working on the project.<br /><br />" \
    #                       "<i>Autocomplete from most universities and large organisations, if the person you are trying to select isn't available please organise an external JCU account for them.</i>")
    #    project_lead = Column(String(256), ca_order=next(order_counter), ca_title="Project Lead (Supervisor)", ca_page="general",
    #        ca_widget=deform.widget.AutocompleteInputWidget(min_length=1, values=choices), ca_force_required=True,
    #        ca_placeholder="eg. Dr Jeremy Vanderwal",
    #        ca_help="Head supervisor of the project that should be contacted when the data manager is unavailable.<br /><br />" \
    #                       "<i>Autocomplete from most universities and large organisations, if the person you are trying to select isn't available please organise an external JCU account for them.</i>")

    #-------------associations--------------------
    parties = relationship('Party', ca_title="People", ca_order=next(order_counter),
        cascade="all, delete-orphan",
        ca_widget=deform.widget.SequenceWidget(min_len=1), ca_missing="", ca_page="general",
        ca_child_widget=deform.widget.MappingWidget(template="inline_mapping"),
        ca_child_title="Person",
        ca_help="Enter the details of all associated people.  There will already be some pre-filled:"
                "<ul><li>Project lead and data manager from the project creation wizard.</li>"
                "<li>People associated with the research grant.</li></ul>"\
                "<i>Autocomplete from most universities and large organisations, if the person you are trying to select isn't available please organise an external JCU account for them.</i>")


    collaborators = relationship('Collaborator', ca_order=next(order_counter), ca_page="general", ca_title="Collaborators (Organisations, groups or external people)",
        cascade="all, delete-orphan", ca_widget=deform.widget.SequenceWidget(min_len=1),
        ca_help="Enter the collaborators fully qualified name:<ul><li>Try to avoid abbreviations.</li><li>If the collaborator is a person, it is preferable to organise an external JCU account and add them in the people section above.</li></ul>",
        ca_description="Other people, groups or organisations who are associated with this project but cannot be added as a person above.",
        ca_herlp="<b>TODO: This should give good definitions and edge cases etc...</b>", ca_missing="")

    #---------------------description---------------------
    brief_description = Column(Text(), ca_order=next(order_counter), ca_page="description", ca_force_required=True,
        ca_placeholder="eg.  TODO: Get a well written brief description for the artificial tree project.",
        ca_widget=deform.widget.TextAreaWidget(rows=6), ca_title="Brief Description",
        ca_description="<p>A short description targeted at a general audience.</p><p><i>This field may be pre-filled with the grant description (<b>as a starting point</b>).</i></p>",
        ca_help="A short description of the research done, why the research was done and the collection and research methods used:"\
                "<ul><li>Write this description in lay-mans terms targeted for the general population to understand.</li>"\
                "<li>A short description of the (project level) where and when can also be included.</li>"\
                "<li>Note: Keep the description relevant to all generated records.</li></ul>")
    full_description = Column(Text(), ca_order=next(order_counter), ca_widget=deform.widget.TextAreaWidget(rows=20), ca_page="description", ca_force_required=True,
        ca_title="Full Description", ca_placeholder="eg.  TODO: Get a well written full description for the artificial tree project.",
        ca_description="Full description targeted at researchers and scientists",
        ca_help="A full description of the research done, why the research was done and the collection and research methods used:"\
                "<ul><li>Write this description targeted for other researchers  to understand (include the technicalities).</li>"\
                "<li>Information about the research dataset/collection, registry/repository, catalogue or index, including its characteristics and features, eg. This dataset contains observational data, calibration files and catalogue information collected from the Mount Stromlo Observatory Facility.</li>"\
                "<li>If applicable: the scope; details of entities being studied or recorded; methodologies used.</li>"
                "<li>Note: Keep the description relevant to all generated records.</li></ul>")

    notes = relationship('MetadataNote', ca_title="Note(s)", ca_order=next(order_counter), ca_child_title="Note",
           cascade="all, delete-orphan", ca_widget=deform.widget.SequenceWidget(min_len=1), ca_missing="", ca_page="description",
            ca_help="Optional additional note(s) about this record.")

    #---------------------metadata---------------------
    #-------------Subject--------------------
    keywords = relationship('Keyword', ca_order=next(order_counter), ca_page="information",
        ca_widget=deform.widget.SequenceWidget(min_len=1),
        cascade="all, delete-orphan",
        ca_group_collapsed=False, ca_group_start='subject', ca_group_title="Area of Research",
        ca_group_description="",
        ca_help="Enter keywords that users are likely to search on when looking for this projects data.")

    fieldOfResearch = relationship('FieldOfResearch', ca_name="dc:subject.anzsrc:for.0.rdf:resource", ca_order=next(order_counter), ca_title="Fields of Research", ca_page="information",
        cascade="all, delete-orphan", ca_validator=sequence_required_validator,
        ca_force_required=True,
        ca_widget=deform.widget.SequenceWidget(template='multi_select_sequence', max_len=3, error_class="error"),
        ca_child_title="Field of Research",
        ca_help="Select the most applicable Fields of Research (FoR) from the drop-down menus, and click the 'Add Field Of Research' button (which is hidden until a code is selected)."
        , ca_missing="")
    #    colander.SchemaNode(colander.String(), title="Fields of Research",
    #        placeholder="To be redeveloped similar to ReDBox", description="Select relevant FOR code/s. ")
    #
    socioEconomicObjective = relationship('SocioEconomicObjective', ca_name="dc:subject.anzsrc:seo.0.rdf:resource", ca_order=next(order_counter), ca_title="Socio-Economic Objectives", ca_page="information",
        cascade="all, delete-orphan",
        ca_widget=deform.widget.SequenceWidget(template='multi_select_sequence'),
        ca_child_title="Socio-Economic Objective",
        ca_help="Select the most applicable Socio-Economic Objective (SEO) from the drop-down menus, and click the 'Add Socio-Economic Objective' button (which is hidden until a code is selected).")

    #    researchThemes = Column(String(),
    #
    #        ca_group_start="research_themes", ca_group_title="Research Themes",ca_group_validator=research_theme_validator,
    #        ca_description="Select one or more of the 4 themes, or \'Not aligned to a University theme\'.", required=True)

    #-------Research themese---------------------
    ecosystems_conservation_climate = Column(Boolean(), ca_name="jcu:research.themes.tropicalEcoSystems", ca_order=next(order_counter), ca_widget=deform.widget.CheckboxWidget(css_class="normal_font"), ca_page="information",
        ca_title='Tropical Ecosystems, Conservation and Climate Change',
        ca_group_start="research_themes", ca_group_title="Research Themes",ca_group_validator=research_theme_validator,
        ca_group_force_required=True, ca_group_page="information",
        #        ca_group_description="Select one or more of the 4 themes, or \'Not aligned to a University theme\'.",
        ca_group_required=True,)
    industries_economies = Column(Boolean(), ca_name="jcu:research.themes.industriesEconomies", ca_order=next(order_counter),ca_widget=deform.widget.CheckboxWidget(css_class="normal_font"), ca_page="information",
        ca_title='Industries and Economies in the Tropics')
    peoples_societies = Column(Boolean(), ca_name="jcu:research.themes.peopleSocieties", ca_order=next(order_counter), ca_widget=deform.widget.CheckboxWidget(css_class="normal_font"), ca_page="information",
        ca_title='Peoples and Societies in the Tropics')
    health_medicine_biosecurity = Column(Boolean(), ca_name="jcu:research.themes.tropicalHealth", ca_order=next(order_counter), ca_widget=deform.widget.CheckboxWidget(css_class="normal_font"), ca_page="information",
        ca_title='Tropical Health, Medicine and Biosecurity',
        #    not_aligned = Column(Boolean(), ca_order=next(order_counter), ca_widget=deform.widget.CheckboxWidget(), ca_page="information",
        #        ca_title='Not aligned to a University theme',
        ca_group_end="research_themes")
    #------------end Research themes--------------


    #-------typeOfResearch---------------------
    researchTypes = (
        ('applied', 'Applied research'),
        ('experimental', 'Experimental development'),
        ('pure_basic', 'Pure basic research'),
        ('pure_strategic', 'Strategic basic research'))

    typeOfResearch = Column(String(50), ca_name="dc:subject.anzsrc:toa.rdf:resource", ca_order=next(order_counter), ca_page="information",
        ca_group_end="subject",
        ca_widget=deform.widget.RadioChoiceWidget(values=researchTypes),
        ca_validator=OneOfDict(researchTypes[:]),
        ca_title="Type of Research Activity",
        ca_force_required=True,
        ca_help="1297.0 Australian Standard Research Classification (ANZSRC) 2008. </br></br>"\
                "<b>Pure basic research</b> is experimental and theoretical work undertaken to acquire new knowledge without looking for long term benefits other than the advancement of knowledge.</br></br>"\
                "<b>Strategic basic research</b> is experimental and theoretical work undertaken to acquire new knowledge directed into specified broad areas in the expectation of useful discoveries. It provides the broad base of knowledge necessary for the solution of recognised practical problems.</br></br>"\
                "<b>Applied research</b> is original work undertaken primarily to acquire new knowledge with a specific application in view. It is undertaken either to determine possible uses for the findings of basic research or to determine new ways of achieving some specific and predetermined objectives.</br></br>"\
                "<b>Experimental development</b> is systematic work, using existing knowledge gained from research or practical experience, that is directed to producing new materials, products or devices, to installing new processes, systems and services, or to improving substantially those already produced or installed."
    )
    #------------end typeOfResearch--------------


    #-------------coverage--------------------
    time_period_description = Column(String(256), ca_order=next(order_counter), ca_title="Time Period (description)", ca_page="information",
        ca_group_start="coverage", ca_group_collapsed=False, ca_group_title="Project Date and Location",
        ca_placeholder="eg. Summers of 1996-2006", ca_missing="",
        ca_help="Provide a textual representation of the time period such as 'world war 2' or more information on the time within the dates provided.")
    date_from = Column(Date(), ca_validator=colander.Range(), ca_name="dc:coverage.vivo:DateTimeInterval.vivo:start", ca_order=next(order_counter), ca_placeholder="", ca_title="Date data started/will start being collected", ca_page="information",
        ca_help="The date that data started being collected.  Note that this is the actual data date not the finding date, recording date or other date.  For example, an old letter may be found in 2013 but it was actually written in 1900 - the date to use is 1900.", ca_force_required=True)
    date_to = Column(Date(), ca_name="dc:coverage.vivo:DateTimeInterval.vivo:end", ca_order=next(order_counter), ca_title="Date data stopped/will stop being collected", ca_page="information",
        ca_help='The date that data will stop being collected.  Note that this is the actual data date not the finding date, recording date or other date.  For example, an old letter may be found in 2013 but it was actually written in 1900 - the date to use is 1900.', ca_missing=colander.null)
    location_description = Column(String(512), ca_order=next(order_counter), ca_title="Location (description)", ca_page="information",
        ca_help="Textual description of the region covered such as Australian Wet Tropics."
        , ca_missing="", ca_placeholder="eg. Australian Wet Tropics or Great Barrier Reef")


    locations = relationship('Location', ca_order=next(order_counter), ca_title="Location", ca_widget=deform.widget.SequenceWidget(template='map_sequence', error_class="error"), ca_page="information",
        cascade="all, delete-orphan", ca_validator=sequence_required_validator,
        ca_force_required=True,
        ca_group_end="coverage", ca_child_widget=deform.widget.MappingWidget(template="inline_mapping"),
        ca_missing=colander.null, ca_help="<p>Use the drawing tools on the map and/or edit the text representations below.</p><p>Locations are represented using <a href='http://en.wikipedia.org/wiki/Well-known_text#Geometric_Objects'>Well-known Text (WKT) markup</a> in the WGS 84 coordinate system (coordinate system used by GPS).</p>")


    #-------------legal--------------------
    # TODO: Make this into a drop down - still need the list of options though.
    access_rights = Column(String(256), ca_name="dc:accessRights.skos:prefLabel", ca_order=next(order_counter), ca_title="Access Rights", ca_page="information",
        ca_widget=deform.widget.SelectWidget(values=(("open", "Open Access"),)),
        ca_group_start="legality", ca_group_collapsed=False, ca_group_title="Licenses & Access Rights",
        ca_help="Information how to access the records data, including access restrictions or embargoes based on privacy, security or other policies. A URI is optional.<br/>TODO: Update the list of access rights.")
    # TODO: Pre-populate with a url - still waiting on URL to use
    access_rights_url = Column(String(256), ca_validator=colander.url, ca_order=next(order_counter), ca_name="dc:accessRights.dc:identifier", ca_title="URL", ca_missing="", ca_page="information",
        ca_requires_admin=True)

    rights = Column(String(256), ca_order=next(order_counter), ca_name="dc:accessRights.dc:RightsStatement.skos:prefLabel", ca_missing="", ca_title="Usage Rights", ca_page="information",
        ca_requires_admin=True,
        ca_placeholder=" eg. Made available under the Public Domain Dedication and License v1.0",
        ca_help="Information about rights held over the collection such as copyright, licences and other intellectual property rights.  A URI is optional.",
        ca_widget=deform.widget.TextInputWidget(css_class="full_width"))
    rights_url = Column(String(256), ca_validator=colander.url, ca_name="dc:accessRights.dc:RightsStatement.dc:identifier", ca_order=next(order_counter), ca_title="URL", ca_missing="", ca_page="information",ca_requires_admin=True,)
    #    TODO: Link to external sources

    licenses = (
        ("http://creativecommons.org/licenses/by-nc-nd/3.0/au", "CC BY-NC-ND: Attribution-Noncommercial-No Derivatives 3.0 AU"),
        ("http://creativecommons.org/licenses/by-nc-sa/3.0/au", "CC BY-NC-SA: Attribution-Noncommercial-Share Alike 3.0 AU"),
        ("http://creativecommons.org/licenses/by-nc/3.0/au", "CC BY-NC: Attribution-Noncommercial 3.0 AU"),
        ("http://creativecommons.org/licenses/by-nd/3.0/au", "CC BY-ND: Attribution-No Derivative Works 3.0 AU"),
        ("http://creativecommons.org/licenses/by-sa/3.0/au", "CC BY-SA: Attribution-Share Alike 3.0 AU"),
        ("http://creativecommons.org/licenses/by/3.0/au", "CC BY: Attribution 3.0 AU"),
        ("http://opendatacommons.org/licenses/by/1.0/", "ODC-By - Attribution License 1.0"),
        ("http://opendatacommons.org/licenses/odbl/1.0/", "ODC-ODbL - Attribution Share-Alike for data/databases 1.0"),
        ("http://opendatacommons.org/licenses/pddl/1.0/", "PDDL - Public Domain Dedication and License 1.0"),
#        ('none', 'No License'),
#        ('creative_commons_by', 'Creative Commons - Attribution alone (by)'),
#        ('creative_commons_bync', 'Creative Commons - Attribution + Noncommercial (by-nc)'),
#        ('creative_commons_bynd', 'Creative Commons - Attribution + NoDerivatives (by-nd)'),
#        ('creative_commons_bysa', 'Creative Commons - Attribution + ShareAlike (by-sa)'),
#        ('creative_commons_byncnd', 'Creative Commons - Attribution + Noncommercial + NoDerivatives (by-nc-nd)'),
#        ('creative_commons_byncsa', 'Creative Commons - Attribution + Noncommercial + ShareAlike (by-nc-sa)'),
#        ('restricted_license', 'Restricted License'),
#        ('other', 'Other'),
        )
    license = Column(String(256), ca_name="dc:license.dc:identifier", ca_order=next(order_counter), ca_title="License", ca_page="information",
        ca_default="creative_commons_by", ca_force_required=True,
        ca_widget=deform.widget.SelectWidget(values=licenses, template="select_with_other"),
        ca_help="<p>This list contains data licences that this server has been configured with. For more information about "
                "Creative Commons licences please <a href=\'http://creativecommons.org.au/learn-more/licences\' alt=\'licenses\'>see here</a>.</p>"
                "<p><i>If you would like to add additional licenses please contact the administrators.</i></p>")

    license_name = Column(String(256), ca_name="dc:license.rdf:Alt.skos:prefLabel", ca_order=next(order_counter), ca_title="License Name", ca_placeholder="", ca_missing="", ca_page="information",
        ca_group_requires_admin=True, ca_group_end="legality", ca_group_start="other_license", ca_group_title="Other",
        ca_group_help="If you want to use a license not included in the above list you can provide details below.</br></br>"\
                      "<ul><li>If you are using this field frequently for the same license it would make sense to get your system administrator to add the license to the field above.</li>"\
                      "<li>If you provide two licenses (one from above, plus this one) only the first will be sent to RDA in the RIF-CS.</li>"\
                      "<li>Example of another license: http://www.opendefinition.org/licenses</li></ul>", ca_requires_admin=True,)
    license_url = Column(String(256), ca_validator=colander.url, ca_name="dc:license.rdf:Alt.dc:identifier", ca_order=next(order_counter), ca_title="License URL", ca_placeholder="", ca_missing="", ca_page="information",
        ca_requires_admin=True, ca_group_end="legality")

    #-------------citation--------------------
    # Autocomplete from project title
    citation_title = Column(String(512), ca_name="dc:biblioGraphicCitation.dc:hasPart.dc:title", ca_order=next(order_counter), ca_placeholder="", ca_missing="", ca_page="information",
        ca_group_collapsed=False, ca_group_start='citation', ca_group_title="Citation", ca_group_requires_admin=True,
        ca_group_description="<b>TODO:  Need to work out what these feilds actually mean and refactor/reword."
                             "</b><br/>Provide metadata that should be used for the purposes of citing this record. Providing a "
                             "citation is optional, but if you choose to enable this there are quite specific mandatory "
                             "fields that will be required.")
    # Autocomplete from all people
    citation_creators = relationship('Creator', ca_order=next(order_counter), ca_missing=None, ca_page="information",cascade="all, delete-orphan",)
    # Dont know?
    citation_edition = Column(String(256), ca_name="dc:biblioGraphicCitation.dc:hasPart.dc:hasVersion.rdf:PlainLiteral", ca_order=next(order_counter), ca_missing="", ca_page="information",)
    # Autocomplete as James Cook University
    citation_publisher = Column(String(256), ca_name="dc:biblioGraphicCitation.dc:hasPart.dc:publisher.rdf:PlainLiteral", ca_order=next(order_counter), ca_page="information")
    # Autocomplete as James Cook University
    citation_place_of_publication = Column(String(512), ca_name="dc:biblioGraphicCitation.dc:hasPart.vivo:Publisher.vivo:Location", ca_order=next(order_counter), ca_title="Place of publication", ca_page="information")
    # Dates of data, eg. data data started being collected
    citation_dates = relationship('CitationDate', ca_order=next(order_counter), ca_title="Date(s)", ca_page="information",cascade="all, delete-orphan",)
    # Autocomplete as link to data (CC-DAM)
    citation_url = Column(String(256), ca_validator=colander.url, ca_name="dc:biblioGraphicCitation.dc:hasPart.bibo:Website.dc:identifier",ca_order=next(order_counter), ca_title="URL", ca_page="information")
    # Unknown
    citation_context = Column(String(512), ca_name="dc:biblioGraphicCitation.dc:hasPart.skos:scopeNote", ca_order=next(order_counter), ca_placeholder="citation context", ca_missing="", ca_page="information",
        ca_group_end='citation')
    #-------------additional_information--------------------
    retention_periods = (
        ("indefinite", "Indefinite"), ("1", "1 Year"), ("5", "5 Years"), ("7", "7 Years"), ("10", "10 Years"),
        ("15", "15 Years"))
    retention_period = Column(String(50), ca_name="redbox:retentionPeriod", ca_order=next(order_counter), ca_title="Retention period", ca_page="information",
        #        ca_group_start="additional_information", ca_group_collapsed=False, ca_group_title="Additional Information",
        ca_widget=deform.widget.SelectWidget(values=retention_periods),
        ca_help="Record the period of time that the data must be kept in line with institutional or funding body policies.")
#    national_significance = Column(Boolean(), ca_order=next(order_counter), ca_title="Is the data nationally significant?", ca_page="information",
#        ca_widget=deform.widget.RadioChoiceWidget(values=(("true", "Yes"), ("false", "No"))),
#        ca_help="Do you know or believe that this projects data may be Nationally Significant?")

    related_publications = relationship('RelatedPublication', ca_order=next(order_counter), ca_title="Related Publications", ca_page="information",
        cascade="all, delete-orphan",
        ca_child_widget=deform.widget.MappingWidget(template="inline_mapping"), ca_child_title="Related Publication",
        ca_help="Please provide details on any publications that are related to this project including their title and URL with an optional note.")

    related_websites = relationship('RelatedWebsite', ca_order=next(order_counter), ca_title="Related Websites", ca_page="information",
        cascade="all, delete-orphan",
        ca_child_widget=deform.widget.MappingWidget(template="inline_mapping"), ca_child_title="Related Website",
        ca_help="Please provide details on any websites that are related to this project including their title and URL with an optional note.")

    attachments = relationship('Attachment', ca_order=next(order_counter),
        ca_missing=None, ca_page="information", ca_child_widget=deform.widget.MappingWidget(template="inline_mapping"),
        cascade="all, delete-orphan",
        ca_help="Optionally provide additional information as attachments.")
#    notes = relationship('Note', ca_order=next(order_counter), ca_description="Enter administrative notes as required.", ca_missing=None, ca_page="information",
#        ca_group_end="additional_information")

class ProjectStates(object):
    OPEN, SUBMITTED, APPROVED, ACTIVE, DISABLED = range(5)

def project_validator(form, value):
    error = False
    exc = colander.Invalid(form) # Uncomment to add a block message: , 'At least 1 research theme or Not aligned needs to be selected')

    if not isinstance(value['project:methods'], list) or len(value['project:methods']) <= 0:
        exc['project:methods'] = "The project must have at least one method."
        error = True
    if not isinstance(value['project:datasets'], list) or len(value['project:datasets']) <= 0:
        exc['project:datasets'] = "The project must have at least one dataset."
        error = True

    if error:
        raise exc


class Project(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'project'

    id = Column(Integer, ca_order=next(order_counter), primary_key=True, ca_widget=deform.widget.HiddenWidget())
    state = Column(Integer, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(), ca_missing=ProjectStates.OPEN, ca_default=ProjectStates.OPEN)

    project_creator = Column(String(100), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
    creation_date = Column(Date, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())

    template_only = Column(Boolean, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())

    information = relationship('Metadata', ca_title="", ca_order=next(order_counter),
        cascade="all, delete-orphan",
        ca_child_collapsed=False, uselist=False,)

    #-----------------------------Method page----------------------------------------------------------

#    overall_method_description = Column(Text(), ca_order=next(order_counter), ca_title="Project wide methods description", ca_page="methods",
#        ca_widget=deform.widget.TextAreaWidget(rows=5),
#        ca_description="Provide a description for all data input methods used in the project.",
#        ca_placeholder="Provide an overview of all the data collection methods used in the project and why those methods were chosen.",
#        ca_help="<p>This will be used as the description for data collection in the project metadata record and will provide users of your data with an overview of what the project is researching.</p>"
#                "<p><i>If you aren't sure what a method is return to this description after completing the Methods page.</i></p>")

    methods = relationship('Method', ca_title="", ca_widget=deform.widget.SequenceWidget(min_len=0, template="method_sequence"), ca_order=next(order_counter), ca_page="methods",
        cascade="all, delete-orphan",
        ca_child_collapsed=False,)
#        ca_description="Add one method for each type of data collection method (eg. temperature sensors, manually entered field observations using a form or files retrieved by polling a server...)")

    #----------------------------Dataset page------------------------------------------
    # The datasets page is dynamically generated from user input on the methods page, therefore a static
    # ColanderAlchemy schema will not be able to generate the required deform schemas:
    #   * Setup the ColanderAlchemy schema to correctly create the database
    #   * Dynamically alter the generated schema in the view
    datasets = relationship('Dataset', ca_widget=deform.widget.SequenceWidget(min_len=0, template="dataset_sequence"), ca_order=next(order_counter), ca_page="datasets",
        ca_child_widget=deform.widget.MappingWidget(template="dataset_mapping"),
        ca_child_title="Dataset", ca_child_collapsed=False,cascade="all, delete-orphan",)

    #-----------------------------------------Submit page---------------------------------------------------

    validated = Column(Boolean, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(template="submit_validation"), default=False,
        ca_group_start="validation", ca_group_end="validation", ca_group_title="Validation", ca_group_collapsed=False, ca_page="submit",)

    records_ready = Column(Boolean, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(template="submit_records"), default=False,
        ca_group_start="records", ca_group_end="records", ca_group_title="Generated ReDBox Records", ca_group_collapsed=False, ca_page="submit",)

    ingesters_ready = Column(Boolean, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(template="submit_ingesters"), default=False,
        ca_group_start="ingesters", ca_group_end="ingesters", ca_group_title="Summary of Data Ingesters", ca_group_collapsed=False, ca_page="submit",)

    project_notes = relationship("ProjectNote", ca_title="Project Note",  ca_order=next(order_counter), ca_page="submit",
            cascade="all, delete-orphan",
            ca_help="Project comments that are only relevant to the provisioning system (eg. comments as to why the project was reopened after the creator submitted it).")


    project_template = relationship("ProjectTemplate", ca_order=next(order_counter), ca_missing=colander.null,
        cascade="all, delete-orphan", ca_widget=deform.widget.HiddenWidget(), ca_exclude=True)


def grant_validator(form, value):
    error = False
    exc = colander.Invalid(form) # Uncomment to add a block message: , 'At least 1 research theme or Not aligned needs to be selected')

    mint = MintLookup(None)

    print value
    if value['no_activity'] is True and value['activity'] == colander.null:
        exc['activity'] = "'There is an associated research grant' must be un-selected if a research grant isn't provided."
        error = True
    elif value['no_activity'] is True:
        if mint.get_from_identifier(value['activity']) is None:
            exc['activity'] = "The entered activity isn't a valid Mint identifier.  Please use the autocomplete feature to ensure valid values."
            error = True

    if mint.get_from_identifier(value['project_lead']) is None:
            exc['project_lead'] = "The entered project lead isn't a valid Mint identifier.  Please use the autocomplete feature to ensure valid values."
            error = True

    if mint.get_from_identifier(value['data_manager']) is None:
            exc['data_manager'] = "The entered data manager isn't a valid Mint identifier.  Please use the autocomplete feature to ensure valid values."
            error = True

    if error:
        raise exc

class CreatePage(colander.MappingSchema):
    template = colander.SchemaNode(colander.Integer(), title="Select a Project Template",
        widget=deform.widget.TextInputWidget(template="project_template_mapping"),
        help="<p>Templates pre-fill the project with as much information as possible to make this process as quick and easy as possible.</p><ul><li>If you don't want to use any template, select the general category and Blank template.</li><li>Please contact the administrators to request new templates.</li>",
        description="<ol><li>First select the category or organisational group on the left hand side.</li><li>Then select the most relevant template from the list on the right hand side.</li>")

    no_activity = colander.SchemaNode(colander.Boolean(), help="Must be un-selected if a research grant isn't provided below.",
        title="There is an associated research grant", default=True, widget=deform.widget.CheckboxWidget(template="checked_conditional_input", inverted=True))

    activity = colander.SchemaNode(colander.String(), title="Research Grant",
        missing=colander.null, required=False,
        help="Enter title of the research grant associated with this record (Autocomplete).  The grant will be looked up for additional information that can be pre-filled.",
        description="Un-Select 'There is an associated research grant' above if your project isn't associated with a research grant.",
        widget=deform.widget.AutocompleteInputWidget(min_length=1, values='/search/activities/', template="mint_autocomplete_input", delay=10))

    #    services = Column(String(256), ca_title="Services - Remove this?", ca_order=next(order_counter), ca_placeholder="Autocomplete - Mint/Mint DB", ca_page="general",
    #            ca_help="Indicate any related Services to this Collection. A lookup works against Mint, or you can enter known information about remote Services."
    #            , ca_missing="",
    #            ca_group_end="associations")


    data_manager = colander.SchemaNode(colander.String(), title="Data Manager (Primary contact)",
        widget=deform.widget.AutocompleteInputWidget(min_length=1, values='/search/parties/', template="mint_autocomplete_input", delay=10),
        help="Primary contact for the project, this should be the person in charge of the data and actively working on the project.<br /><br />"\
                "<i>Autocomplete from most universities and large organisations, if the person you are trying to select isn't available please organise an external JCU account for them.</i>")
    project_lead = colander.SchemaNode(colander.String(), title="Project Lead (Supervisor)",
        widget=deform.widget.AutocompleteInputWidget(min_length=1, values='/search/parties/', template="mint_autocomplete_input", delay=10),
        help="Head supervisor of the project that should be contacted when the data manager is unavailable.<br /><br />"\
                "<i>Autocomplete from most universities and large organisations, if the person you are trying to select isn't available please organise an external JCU account for them.</i>")


method_template = colander.SchemaNode(colander.Integer, title="Select a template to base this method off",
    widget=deform.widget.TextInputWidget(template="project_template_mapping"),
    help="<p>Method templates provide pre-configured data collection methods and pre-fill as much information as possible to make this process as quick and easy as possible.</p>"
            "<ul><li>If you don't want to use any template, select the general category and Blank template."
            "</li><li>Please contact the administrators to request new templates.</li>",
    description="<ol><li>First select the category or organisational group on the left hand side.</li>"
                   "<li>Then select the most relevant template from the list on the right hand side.</li>")


class IngesterLogsFiltering(colander.MappingSchema):
    log_levels=(("ALL","Show All"),
                ("ERROR","Errors"),
                ("INFO", "Informational"),
#                ("WARNING", "Warnings"),
#                ("DEBUG", "Debugging"),
)
    start_date = colander.SchemaNode(colander.Date(),missing=colander.null)
    end_date = colander.SchemaNode(colander.Date(),missing=colander.null)
    level = colander.SchemaNode(colander.String(),widget=deform.widget.SelectWidget(values=log_levels,
        multiple=False),missing=colander.null)

class IngesterLogs(colander.MappingSchema):
    filtering = IngesterLogsFiltering(widget=deform.widget.MappingWidget(template="inline_mapping", show_label=True),
        title="Filter Logs",
        help='Filter the ingester event logs based on level (multple seletion) as well as date start, end or range.',
        missing=colander.null)
    logs = colander.SchemaNode(colander.String(), title="", widget=deform.widget.HiddenWidget(template="ingester_logs"),
        help="TODO: Provide information on what logs mean",missing=colander.null)