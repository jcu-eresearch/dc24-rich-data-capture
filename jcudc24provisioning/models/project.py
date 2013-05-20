"""
Provides all project related Colander (deform) and ColanderAlchemy (deform+SQLAlchemy) models, this includes project
configuration as well as maintainence and searching models (eg. anything to do with data ingestion and metadata).
"""

from collections import OrderedDict
from datetime import date, datetime
import itertools
import logging
from beaker.cache import cache_region

import colander
from sqlalchemy.orm import backref
from sqlalchemy.schema import ForeignKey, Table
from sqlalchemy import (
    Integer,
    Text,
    Float, INTEGER)
from sqlalchemy.types import String, Boolean, Date

from simplesos.client import SOSVersions
from colanderalchemy.declarative import Column, relationship
from jcudc24provisioning.models.ca_model import CAModel
import deform
from jcudc24provisioning.models import Base, DBSession
from jcudc24provisioning.models.file_upload import upload_widget
from jcudc24provisioning.views.deform_widgets import MethodSchemaWidget
from jcudc24provisioning.views.ajax_mint_lookup import MintLookup
from jcudc24provisioning.controllers.authentication import DefaultPermissions


#config = ConfigParser.SafeConfigParser()
#config.read('../../development.ini')
#db_engine = create_engine(config.get("app:main", "sqlalchemy.url"), connect_args={'pool_recycle': 3600, 'echo': False},) #connect_args={'reconnect':True})
#db_engine.connect()
#DBSession = scoped_session(sessionmaker(bind=db_engine))
import re


logger = logging.getLogger(__name__)

class OneOfDict(object):
    """
    Validator which succeeds if the value passed to it is one of
    a fixed set of values
    """
    def __init__(self, choices):
        self.choices = choices

    def __call__(self, node, value):
        test = 1
        if not value in [x[0] for x in self.choices]:
            choices = ', '.join(['%s' % x[1] for x in self.choices])
            #            err = colander._('Please select one of ${choices}',
            #                    mapping={'choices':choices})
            err = "Required"
            raise colander.Invalid(node, err)


def sequence_required_validator(form, value):
    """
    Validator that returns a 'required' error for None or empty sequences.  This is a custom validator for sequences
    that can't enforce at least item being present at the start (SEO/FOR codes - their value needs to be selected first)

    :param form: Form to validate on
    :param value: Value of the sequence (this should be a list)
    :return: None, raise a colander.Invalid error if the sequence doesn't have at least 1 item.
    """
    if not isinstance(value, list) or len(value) < 1:
        exc = colander.Invalid(form, 'Required.')
        raise exc

########################################################################################################################
###################################### MODELS FOR CREATING METADATA RECORDS ###########################################
########################################################################################################################
def research_theme_validator(form, value):
    """
    Validation that at least 1 research theme is selected.

    :param form: Form to validate on
    :param value: Value of the research theme's mapping
    :return: None, raise a colander.Invalid error if there is no research theme selected.
    """
    error = True
    exc = colander.Invalid(form, 'At least 1 research theme needs to be selected')

    for key, selected in value.items():
        if selected:
            error = False
        #        exc[key] = 'At least 1 research theme needs to be selected'
    if error:
        raise exc

@cache_region('long_term')
def get_for_codes_from_file(file):
    for_codes_file = open(file).read()
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



@colander.deferred
def getFORCodes(node, kw):
    """
    Helper function for retrieving and organising FOR codes from the CSV file that contains them.

    :param node: Node that the returnd values are for.
    :param kw: Arguments that are passed to the shema's bind() method.
    :return: OrderedDict of FOR codes nested appropriately.
    """
    FOR_CODES_FILE = kw['settings'].get("provisioning.for_codes", {})
    return get_for_codes_from_file(FOR_CODES_FILE)

@cache_region('long_term')
def get_seo_codes_from_file(file):
    seo_codes_file = open(file).read()
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

@colander.deferred
def getSEOCodes(node, kw):
    """
    Helper function for retrieving and organising SEO codes from the CSV file that contains them.

    :param node: Node that the returnd values are for.
    :param kw: Arguments that are passed to the shema's bind() method.
    :return: OrderedDict of SEO codes nested appropriately.
    """
    SEO_CODES_FILE = kw['settings'].get("provisioning.seo_codes", {})

    return get_seo_codes_from_file(SEO_CODES_FILE)


class FieldOfResearch(CAModel, Base):
    """
    Model to hold and display Fields Of Research (FOR) codes.
    - field_of_research is only used for exporting to ReDBox (processed to contain the code only)
    - field_of_research_label holds the value actually selected.
    """

    order_counter = itertools.count()

    __tablename__ = 'field_of_research'
    id = Column(Integer, primary_key=True, ca_order=next(order_counter), ca_force_required=False, nullable=False, ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'),ca_order=next(order_counter),  nullable=False, ca_widget=deform.widget.HiddenWidget())

    field_of_research = Column(String(100), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
    field_of_research_label = Column(String(128), ca_order=next(order_counter), ca_title="Field Of Research", ca_widget=deform.widget.TextInputWidget(template="readonly/textinput"),
        ca_data=getFORCodes)


class SocioEconomicObjective(CAModel, Base):
    """
    Model to hold and display Fields Of Research (FOR) codes.
    - socio_economic_objective is only used for exporting to ReDBox (processed to contain the code only)
    - socio_economic_objective_label holds the value actually selected.
    """
    order_counter = itertools.count()

    __tablename__ = 'socio_economic_objective'
    id = Column(Integer, primary_key=True, ca_order=next(order_counter), nullable=False, ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'), ca_order=next(order_counter), nullable=False, ca_widget=deform.widget.HiddenWidget())

    socio_economic_objective = Column(String(100), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
    socio_economic_objective_label = Column(String(128), ca_order=next(order_counter), ca_title="Socio-Economic Objective", ca_widget=deform.widget.TextInputWidget(template="readonly/textinput"),
        ca_data=getSEOCodes)

#class Person(CAModel, Base):
#    order_counter = itertools.count()
#
#    __tablename__ = 'person'
#    id = Column(Integer, primary_key=True, ca_order=next(order_counter), nullable=False, ca_widget=deform.widget.HiddenWidget())
#
#    title = Column(String(5), ca_title="Title", ca_order=next(order_counter), ca_placeholder="eg. Mr, Mrs, Dr",)
#    given_name = Column(String(256), ca_order=next(order_counter), ca_title="Given name")
#    family_name = Column(String(256), ca_order=next(order_counter), ca_title="Family name")
#    email = Column(String(256), ca_order=next(order_counter), ca_missing="", ca_validator=colander.Email())

# Types of relationships as per ReDBox.
relationship_types = (
    ("select", "---Select One---"), ("isManagedBy", "Managed by"), ("hasAssociationWith", "Associated with"),
    ("hasCollector", "Aggregated by")
    , ("isEnrichedBy", "Enriched by"))

@colander.deferred
def search_parties_widget(node, kw):
    search_path = kw['request'].route_url("get_parties", search_terms="")
    identifier_path = kw['request'].route_url("get_from_identifier", identifier="")
    return deform.widget.AutocompleteInputWidget(min_length=1, values=search_path, identifier_path=identifier_path,
        template="mint_autocomplete_input", readonly_template="readonly/mint_autocomplete_input", size="70", delay=10)

@colander.deferred
def search_activities_widget(node, kw):
    search_path = kw['request'].route_url("get_activities", search_terms="")
    identifier_path = kw['request'].route_url("get_from_identifier", identifier="")
    return deform.widget.AutocompleteInputWidget(min_length=1, values=search_path, identifier_path=identifier_path,
        template="mint_autocomplete_input", readonly_template="readonly/mint_autocomplete_input", size="70", delay=10)

class Party(CAModel, Base):
    """
    Parties associated with a project/metadata record, currently parties are only people which are selected from a
    mint lookup widget but this could be upgraded to include other parties such as groups or organisations.
    - party_relationship and identifier are the primary fields the only ones set by the user interface.
    - Other fields are filled before creating metadata records by looking up Mint.
    """
    order_counter = itertools.count()

    __tablename__ = 'party'
    id = Column(Integer, primary_key=True, nullable=False, ca_force_required=False, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
    #    person_id = Column(Integer, ForeignKey('person.id'), ca_order=next(order_counter), nullable=False, ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'), ca_order=next(order_counter), nullable=False, ca_widget=deform.widget.HiddenWidget())

    party_relationship_label = Column(String(100), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(),)
    party_relationship = Column(String(100), ca_order=next(order_counter), ca_title="This project is",
        ca_widget=deform.widget.SelectWidget(values=relationship_types),
        ca_validator=OneOfDict(relationship_types[1:]),
        ca_help="<b>Managed by</b>: Primary contact<br />"
                "<b>Aggregated by</b>: Helped with collecting data<br />"
                "<b>Enriched by</b>: Helped the project in some other way<br />"
                "<b>Associated With</b>: The project has something to do with this person<br />")

    name = Column(String(100), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(),)              # TODO: Pre-fill these fields when a party is selected.
    title = Column(String(100), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(),)
    #                Party.coprimary: "dc:creator.foaf:Person.1.redbox:isCoPrimaryInvestigator",
    #                Party.primary: "dc:creator.foaf:Person.1.redbox:isPrimaryInvestigator",
    given_name = Column(String(100), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(),)
    family_name = Column(String(100), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(),)
    organisation = Column(String(100), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(),)
    organisation_label = Column(String(100), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(),)
    email = Column(String(100), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(),)
    association = Column(String(256), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(),)
    association_label = Column(String(256), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(),)

    short_display_name = Column(String(256), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(),)


    identifier = Column(String(100), ca_order=next(order_counter), ca_title="Person", ca_force_required=True,
        ca_widget=search_parties_widget)
#    person = relationship('Person', ca_order=next(order_counter), uselist=False)


class Keyword(CAModel, Base):
    """
    Metadata record keywords.
    """
    order_counter = itertools.count()

    __tablename__ = 'keyword'
    id = Column(Integer, primary_key=True, ca_force_required=False, nullable=False, ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'), ca_force_required=False, nullable=False, ca_widget=deform.widget.HiddenWidget())

    keyword = Column(String(512), ca_name="dc:subject.vivo:keyword.0.rdf:PlainLiteral", ca_force_required=True)


class Collaborator(CAModel, Base):
    """
    Metadata record collaborators, these are organisations, groups or people that can't be entered as a party.
    """
    order_counter = itertools.count()

    __tablename__ = 'collaborator'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'), nullable=False, ca_widget=deform.widget.HiddenWidget())

    collaborator = Column(String(256), ca_title="Collaborator", ca_name="dc:contributor.locrel:clb.0.foaf:Agent",
        ca_placeholder="eg. CSIRO, University of X, Prof. Jim Bloggs, etc.")

class Creator(CAModel, Base):
    """
    Person to use in the citation as a creator, this is typically pre-filled using all parties setup on the general
    details page.

    This table is required for 2 reasons:
    - Allow users to customise the citation (rather than just using all people added on general details page).
    - Transparent export to metadata records via CAModel.toXML().
    """
    order_counter = itertools.count()

    __tablename__ = 'creator'
    id = Column(Integer, primary_key=True, nullable=False, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'), ca_order=next(order_counter), nullable=False, ca_widget=deform.widget.HiddenWidget())

    title = Column(String(5), ca_name="dc:biblioGraphicCitation.dc:hasPart.locrel:ctb.0.foaf:title", ca_title="Title", ca_order=next(order_counter), ca_placeholder="eg. Mr, Mrs, Dr",)
    given_name = Column(String(256), ca_name="dc:biblioGraphicCitation.dc:hasPart.locrel:ctb.0.foaf:givenName", ca_order=next(order_counter), ca_title="Given name")
    family_name = Column(String(256), ca_name="dc:biblioGraphicCitation.dc:hasPart.locrel:ctb.0.foaf:familyName", ca_order=next(order_counter), ca_title="Family name")

    def __init__(self, title=None, given_name=None, family_name=None):
        super(Creator, self).__init__()
        self.title = title
        self.given_name = given_name
        self.family_name = family_name

class CitationDate(CAModel, Base):
    """
    Citation date(s) for metadata records.
    """
    order_counter = itertools.count()

    __tablename__ = 'citation_date'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'), nullable=False, ca_widget=deform.widget.HiddenWidget())

    label = Column(String(256), ca_widget=deform.widget.HiddenWidget())
    type = Column(String(100), ca_name="sourced from citationDateType.json", ca_title="Date type",
        ca_widget=deform.widget.TextInputWidget(size="40", css_class="full_width"))
    date = Column(Date(), ca_name="dc:biblioGraphicCitation.dc:hasPart.dc:date.0.dc:type.skos:prefLabel", ca_title="Date")

    def __init__(self, date=None, type=None, label=None):
        super(CitationDate, self).__init__()
        self.date = date
        self.type = type
        self.label = label


attachment_types = (("data", "Data file"), ("supporting", "Supporting material"), ("readme", "Readme"))
class Attachment(CAModel, Base):
    """
    Metadata record attachment (currently not immplemented for ReDBox export so it doesn't really do anything).
    """

    order_counter = itertools.count()

    __tablename__ = 'attachment'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'),  nullable=False, ca_widget=deform.widget.HiddenWidget())

    type = Column(String(100), ca_name="attachment_type", ca_widget=deform.widget.SelectWidget(values=attachment_types),
        ca_validator=colander.OneOf(
            [attachment_types[0][0], attachment_types[1][0], attachment_types[2][0]]),
        ca_title="Attachment type", ca_css_class="inline")
    attachment = Column(String(512), ca_name="filename",  ca_widget=upload_widget, ca_missing=colander.null)

    note = Column(Text(), ca_name="notes")
#    ca_params={'widget' : deform.widget.HiddenWidget()}



class RelatedPublication(CAModel, Base):
    """
    Publications that are related to the metadata table/record, this is basically a title, URL, and optional note.
    """
    order_counter = itertools.count()

    __tablename__ = 'related_publication'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'), nullable=False, ca_widget=deform.widget.HiddenWidget())

    title = Column(String(512), ca_name="dc:relation.swrc:Publication.0.dc:title", ca_title="Title", ca_placeholder="eg. TODO", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40), ca_force_required=True)
    url = Column(String(512), ca_validator=colander.url, ca_name="dc:relation.swrc:Publication.0.dc:identifier", ca_title="URL", ca_placeholder="eg. http://www.somewhere.com.au", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40), ca_force_required=True)
    notes = Column(String(512), ca_name="dc:relation.swrc:Publication.0.skos:note", ca_title="Note", ca_missing="", ca_placeholder="eg. This publication provides additional information on xyz", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40))

class RelatedWebsite(CAModel, Base):
    """
    Websites that are related to the metadata table/record, this is basically a title, URL, and optional note.
    """
    order_counter = itertools.count()

    __tablename__ = 'related_website'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'), nullable=False, ca_widget=deform.widget.HiddenWidget())

    title = Column(String(512), ca_name="dc:relation.bibo:Website.0.dc:title", ca_title="Title", ca_placeholder="eg. TODO", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40), ca_force_required=True)
    url = Column(String(512), ca_validator=colander.url, ca_name="dc:relation.bibo:Website.0.dc:identifier", ca_title="URL", ca_placeholder="eg. http://www.somewhere.com.au", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40), ca_force_required=True)
    notes = Column(String(512), ca_name="dc:relation.bibo:Website.0.skos:note", ca_title="Note", ca_missing="", ca_placeholder="eg. This publication provides additional information on xyz", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40))


class MetadataNote(CAModel, Base):
    """
    Note description(s) for the metadata record, this is an optional sequence of description fields.
    - note_desc is the relavant field, the others are used for exporting to redbox.
    """
    order_counter = itertools.count()

    __tablename__ = 'metadata_note'

    id = Column(Integer, ca_order=next(order_counter), primary_key=True, ca_widget=deform.widget.HiddenWidget())
    metadata_id = Column(Integer, ForeignKey('metadata.id'), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    note_desc_type = Column(String(100), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), ca_default="note")
    note_desc_label = Column(String(100), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), ca_default="Note:",)
    note_desc = Column(Text(), ca_order=next(order_counter),
        ca_placeholder="eg. TODO",
        ca_widget=deform.widget.TextAreaWidget(rows=3), ca_title="Note",)


# TODO: Deemed too hard/confusing for the end, but this should be most of the code + MintWrapper in controllers/redbox_mint.  The most difficult part will be providing a user friendly way of getting service information.
#class ServiceMetadata(CAModel, Base):
#    order_counter = itertools.count()
#
#    __tablename__ = 'service_metadata'
#
#    id = Column(Integer, ca_order=next(order_counter), ca_force_required=False, primary_key=True, ca_widget=deform.widget.HiddenWidget())
#    project_id = Column(Integer, ForeignKey('project.id'), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
#    method_id = Column(Integer, ForeignKey('method.id'), unique=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
#
#    date_added_to_mint = Column(Date, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
#
#    mint_id = Column(String(256), ca_order=next(order_counter))
#    name = Column(String(256), ca_order=next(order_counter))
#    type = Column(String(256), ca_order=next(order_counter))
#    related_party_1 = Column(String(256), ca_order=next(order_counter))
#    related_relationship_1 = Column(String(256), ca_order=next(order_counter))
#    related_party_2 = Column(String(256), ca_order=next(order_counter))
#    related_relationship_2 = Column(String(256), ca_order=next(order_counter))
#    field_of_research = relationship('FieldOfResearch', ca_name="dc:subject.anzsrc:for.0.rdf:resource", ca_order=next(order_counter), ca_title="Fields of Research", ca_page="information",
#        cascade="all, delete-orphan", ca_validator=sequence_required_validator,
#        ca_force_required=True,
#        ca_widget=deform.widget.SequenceWidget(template='multi_select_sequence', max_len=3, error_class="error"),
#        ca_child_title="Field of Research",
#        ca_help="Select the most applicable Fields of Research (FoR) from the drop-down menus, and click the 'Add Field Of Research' button (which is hidden until a code is selected)."
#        , ca_missing="")
#    keywords = Column(String(256), ca_order=next(order_counter))
#    license = Column(String(256), ca_order=next(order_counter))
#    license_url = Column(String(256), ca_order=next(order_counter))
#    access_rights = Column(String(256), ca_order=next(order_counter))
#    delivery_method = Column(String(256), ca_order=next(order_counter))
#    description = Column(String(256), ca_order=next(order_counter))
#    website = Column(String(256), ca_order=next(order_counter))
#    website_title = Column(String(256), ca_order=next(order_counter))


def metadata_validator(form, value):
    """
    Validates that custom citations are correct.

    :param form: Metadata schemas/form to validate
    :param value: Appstruct/values passed in for validation.
    :return: None, raise a colander.Invalid exception if the validation fails.
    """
    error = False
    exc = colander.Invalid(form) # Uncomment to add a block message: , 'At least 1 research theme or Not aligned needs to be selected')

    item = value.popitem()
    value[item[0]] = item[1]
    key = item[0][:item[0].rindex(":")+1]

    if '%scustom_citation' % key in value and value['%scustom_citation' % key]:
        citation = value["%scitation" % key]
        citation_key = "%scitation:" % key

        exc["%scitation" % key] = "Invalid custom citation."

        if citation['%scitation_title' % citation_key] is None or len(citation['%scitation_title' % citation_key]) == 0:
            exc.children[0]['%scitation_title' % citation_key] = "Required"
        if not isinstance(citation['%scitation_publish_date' % citation_key], (date, datetime)):
            exc.children[0]['%scitation_publish_date' % citation_key] = "Required"
        if not isinstance(citation['%scitation_creators' % citation_key], list) or len(citation['%scitation_title' % citation_key]) == 0:
            exc.children[0]['%scitation_creators' % citation_key] = "Required"
        if citation['%scitation_edition' % citation_key] is None or len(citation['%scitation_edition' % citation_key]) == 0:
            exc.children[0]['%scitation_edition' % citation_key] = "Required"
        if citation['%scitation_publisher' % citation_key] is None or len(citation['%scitation_publisher' % citation_key]) == 0:
            exc.children[0]['%scitation_publisher' % citation_key] = "Required"
        if citation['%scitation_place_of_publication' % citation_key] is None or len(citation['%scitation_place_of_publication' % citation_key]) == 0:
            exc.children[0]['%scitation_place_of_publication' % citation_key] = "Required"
        if citation['%scitation_url' % citation_key] is None or len(citation['%scitation_url' % citation_key]) == 0:
            exc.children[0]['%scitation_url' % citation_key] = "Required"
        if citation['%scitation_data_type' % citation_key] is None or len(citation['%scitation_data_type' % citation_key]) == 0:
            exc.children[0]['%scitation_data_type' % citation_key] = "Required"

        error = True

    if error:
        raise exc


class Metadata(CAModel, Base):
    """
    Main metadata table/form that is an almost direct mapping to exported metadata records.
    - Many of the fields with HiddenWidget's are only used for metadata record/ReDBox export.
    """
    order_counter = itertools.count()

    __tablename__ = 'metadata'

    id = Column(Integer, ca_order=next(order_counter), ca_force_required=False, primary_key=True, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'), unique=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    #----------------------Static fields for ReDBox integration-------------------------
    record_export_date = Column(Date, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(), name="dc:created")
    date_added_to_redbox = Column(Date, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())


    use_record_id = Column(String(256), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), ca_default="false")
    type_of_identifier = Column(String(256), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), ca_default="local")
    type_of_identifier_label = Column(String(256), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), ca_default="Local Identifier")
    dc_spec = Column(String(256), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), name="xmlns:dc", ca_default="http://dublincore.org/documents/2008/01/14/dcmi-terms/")
    foaf_spec = Column(String(256), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), name="xmlns:foaf", ca_default="http://xmlns.com/foaf/spec/",)
    anzsrc_spec = Column(String(256), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), name="xmlns:anzsrc", ca_default="http://purl.org/anzsrc/",)
    view_id = Column(String(256), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), name="viewId", ca_default="default",)
    package_type = Column(String(256), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), name="packageType", ca_default="dataset",)
    record_origin = Column(String(256), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), name="dc:identifier.redbox:origin", ca_default="",) #TODO: What should this be prefilled with? Internal or something like rdc?
    new_redbox_form = Column(String(256), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), name="redbox:newForm", ca_default="false",)    #TODO: Should this be true?
    redbox_form_version = Column(String(256), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), name="redbox:formVersion", ca_default="1.5.2.2",)
    record_type = Column(String(256), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), name="dc:type.rdf:PlainLiteral", ca_default="dataset",)
    record_type_label = Column(String(256), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), name="dc:type.skos:prefLabel", ca_default="Dataset",)
    language = Column(String(256), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), name="dc:language.dc:identifier", ca_default="http://id.loc.gov/vocabulary/iso639-2/eng",)
    language_label = Column(String(256), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), name="dc:language.skos:prefLabel", ca_default="English",)

    data_storage_location = Column(String(256), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    data_storage_location_name = Column(String(512), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), ca_default="CC-DAM, James Cook University, Townsville Campus")
    redbox_identifier = Column(String(256), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    redbox_uri = Column(String(256), ca_name="dc:relation.vivo:Dataset.0.dc:identifier",ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
    ccdam_identifier = Column(String(256), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

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

    internal_grant = Column(Boolean, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), name="foaf:fundedBy.vivo:Grant.1.redbox:internalGrant", ca_default="false")
    grant_number = Column(String(256), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), name="foaf:fundedBy.vivo:Grant.1.redbox:grantNumber",)
    grant_label = Column(String(256), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), name="foaf:fundedBy.vivo:Grant.1.skos:prefLabel",)
    grant = Column(String(256), ca_order=next(order_counter), ca_title="Research Grant", ca_page="general",
        ca_missing="", ca_help="Enter the associated research grant associated with this record (this field will autocomplete).",
        ca_widget=search_activities_widget)

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
        ca_child_widget=deform.widget.MappingWidget(template="inline_mapping", readonly_template="readonly/inline_mapping"),
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
    brief_desc_type = Column(String(100), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), ca_default="brief", ca_page="description",)
    brief_desc_label = Column(String(100), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), ca_default="Brief:", ca_page="description",)
    brief_desc = Column(Text(), ca_order=next(order_counter), ca_page="description", ca_force_required=True,
        ca_placeholder="eg.  TODO: Get a well written brief description for the artificial tree project.",
        ca_widget=deform.widget.TextAreaWidget(rows=6), ca_title="Brief Description",
        ca_description="<p>A short description targeted at a general audience.</p><p><i>This field may be pre-filled with the grant description (<b>as a starting point</b>).</i></p>",
        ca_help="A short description of the research done, why the research was done and the collection and research methods used:"\
                "<ul><li>Write this description in lay-mans terms targeted for the general population to understand.</li>"\
                "<li>A short description of the (project level) where and when can also be included.</li>"\
                "<li>Note: Keep the description relevant to all generated records.</li></ul>")

    full_desc_type = Column(String(100), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), ca_default="full", ca_page="description",)
    full_desc_label = Column(String(100), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter), ca_default="Full:", ca_page="description",)
    full_desc = Column(Text(), ca_order=next(order_counter), ca_widget=deform.widget.TextAreaWidget(rows=20), ca_page="description", ca_force_required=True,
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

    field_of_research = relationship('FieldOfResearch', ca_name="dc:subject.anzsrc:for.0.rdf:resource", ca_order=next(order_counter), ca_title="Fields of Research", ca_page="information",
        cascade="all, delete-orphan", ca_validator=sequence_required_validator,
        ca_force_required=True,
        ca_widget=deform.widget.SequenceWidget(template='multi_select_sequence', max_len=3, error_class="error"),
        ca_child_title="Field of Research",
        ca_help="Select the most applicable Fields of Research (FoR) from the drop-down menus, and click the 'Add Field Of Research' button (which is hidden until a code is selected)."
        , ca_missing="")
    #    colander.SchemaNode(colander.String(), title="Fields of Research",
    #        placeholder="To be redeveloped similar to ReDBox", description="Select relevant FOR code/s. ")
    #
    socio_economic_objective = relationship('SocioEconomicObjective', ca_name="dc:subject.anzsrc:seo.0.rdf:resource", ca_order=next(order_counter), ca_title="Socio-Economic Objectives", ca_page="information",
        cascade="all, delete-orphan", ca_force_required=True,
        ca_widget=deform.widget.SequenceWidget(template='multi_select_sequence', max_len=3),
        ca_child_title="Socio-Economic Objective",
        ca_help="Select the most applicable Socio-Economic Objective (SEO) from the drop-down menus, and click the 'Add Socio-Economic Objective' button (which is hidden until a code is selected).")

    #    researchThemes = Column(String(),
    #
    #        ca_group_start="research_themes", ca_group_title="Research Themes",ca_group_validator=research_theme_validator,
    #        ca_description="Select one or more of the 4 themes, or \'Not aligned to a University theme\'.", required=True)

    #-------Research themese---------------------
    no_research_theme = Column(Boolean(), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())   # TODO: On save, set this if no other selected, else unset.
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
        ('pure', 'Pure basic research'),
        ('strategic', 'Strategic basic research'))

    type_of_research_label = Column(String(100), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
    type_of_research = Column(String(50), ca_name="dc:subject.anzsrc:toa.rdf:resource", ca_order=next(order_counter), ca_page="information",
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
    date_from = Column(Date(), ca_name="dc:coverage.vivo:DateTimeInterval.vivo:start", ca_order=next(order_counter), ca_placeholder="", ca_title="Date data started/will start being collected", ca_page="information",
        ca_help="The date that data started being collected.  Note that this is the actual data date not the finding date, recording date or other date.  For example, an old letter may be found in 2013 but it was actually written in 1900 - the date to use is 1900.", ca_force_required=True)
    date_to = Column(Date(), ca_name="dc:coverage.vivo:DateTimeInterval.vivo:end", ca_order=next(order_counter), ca_title="Date data stopped/will stop being collected", ca_page="information",
        ca_help='The date that data will stop being collected.  Note that this is the actual data date not the finding date, recording date or other date.  For example, an old letter may be found in 2013 but it was actually written in 1900 - the date to use is 1900.', ca_missing=colander.null)
    #    location_description = Column(String(512), ca_order=next(order_counter), ca_title="Location (description)", ca_page="information",
    #        ca_help="Textual description of the region covered such as Australian Wet Tropics."
    #        , ca_missing="", ca_placeholder="eg. Australian Wet Tropics or Great Barrier Reef")


    locations = relationship('Location', ca_order=next(order_counter), ca_title="Location", ca_widget=deform.widget.SequenceWidget(template='map_sequence', readonly_template='readonly/map_sequence', error_class="error", min_len=1), ca_page="information",
        cascade="all, delete-orphan", ca_validator=sequence_required_validator,
        ca_force_required=True,
        ca_group_end="coverage", ca_child_widget=deform.widget.MappingWidget(template="inline_mapping", readonly_template="readonly/inline_mapping"),
        ca_missing=colander.null, ca_help="<p>Use the drawing tools on the map and/or edit the text representations below.</p><p>Locations are represented using <a href='http://en.wikipedia.org/wiki/Well-known_text#Geometric_Objects'>Well-known Text (WKT) markup</a> in the WGS 84 coordinate system (coordinate system used by GPS).</p>")


    #-------------legal--------------------
    # TODO: Make this into a drop down - still need the list of options though.
    #    access_rights_label = Column(String(100), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
    access_rights = Column(String(256), ca_name="dc:accessRights.skos:prefLabel", ca_order=next(order_counter), ca_title="Access Rights", ca_page="information",
        ca_widget=deform.widget.SelectWidget(values=(("Open Access", "Open Access"),("Contact Manager","Contact project manager"), ("Contact Owner", "Contact project owner"))),
        ca_group_start="legality", ca_group_collapsed=False, ca_group_title="Licenses & Access Rights",
        ca_help="Information how to access the records data, including access restrictions or embargoes based on privacy, security or other policies. A URI is optional.<br/>TODO: Update the list of access rights.")
    # TODO: Pre-populate with a url - still waiting on URL to use
    access_rights_url = Column(String(256), ca_validator=colander.url, ca_order=next(order_counter), ca_name="dc:accessRights.dc:identifier", ca_title="Access Rights URL (Advanced)", ca_missing="", ca_page="information",
        ca_requires_admin=True)

    rights = Column(String(256), ca_order=next(order_counter), ca_name="dc:accessRights.dc:RightsStatement.skos:prefLabel", ca_missing="", ca_title="Usage Rights (Advanced)", ca_page="information",
        ca_placeholder=" eg. Made available under the Public Domain Dedication and License v1.0", ca_requires_admin=True,
        ca_help="Information about rights held over the collection such as copyright, licences and other intellectual property rights.  A URI is optional.",
        ca_widget=deform.widget.TextInputWidget(css_class="full_width"))
    rights_url = Column(String(256), ca_validator=colander.url,  ca_requires_admin=True,
        ca_name="dc:accessRights.dc:RightsStatement.dc:identifier", ca_order=next(order_counter), ca_title="Usage Rights URL (Advanced)", ca_missing="", ca_page="information",)
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
    license_label = other_license_name = Column(String(256), ca_order=next(order_counter), ca_page="information", ca_widget=deform.widget.HiddenWidget(),)
    license = Column(String(256), ca_name="dc:license.dc:identifier", ca_order=next(order_counter), ca_title="License", ca_page="information",
        ca_default="creative_commons_by", ca_force_required=True,
        ca_widget=deform.widget.SelectWidget(values=licenses, template="select_with_other"),
        ca_help="<p>This list contains data licences that this server has been configured with. For more information about "
                "Creative Commons licences please <a href=\'http://creativecommons.org.au/learn-more/licences\' alt=\'licenses\'>see here</a>.</p>"
                "<p><i>If you would like to add additional licenses please contact the administrators.</i></p>")

    other_license_name = Column(String(256), ca_name="dc:license.rdf:Alt.skos:prefLabel", ca_order=next(order_counter), ca_title="License Name", ca_placeholder="", ca_missing="", ca_page="information",
        ca_group_requires_admin=True, ca_group_start="other_license", ca_group_title="Other License (Advanced)",
        ca_group_help="If you want to use a license not included in the above list you can provide details below.</br></br>"\
                      "<ul><li>If you are using this field frequently for the same license it would make sense to get your system administrator to add the license to the field above.</li>"\
                      "<li>If you provide two licenses (one from above, plus this one) only the first will be sent to RDA in the RIF-CS.</li>"\
                      "<li>Example of another license: http://www.opendefinition.org/licenses</li></ul>", ca_requires_admin=True,)
    other_license_url = Column(String(256), ca_validator=colander.url, ca_name="dc:license.rdf:Alt.dc:identifier", ca_order=next(order_counter), ca_title="License URL", ca_placeholder="", ca_missing="", ca_page="information",
        ca_requires_admin=True, ca_group_end="legality", )

    #-------------citation--------------------
    custom_citation = Column(Boolean(), ca_title="Provide Custom Citation", ca_order=next(order_counter),
        ca_default=False, ca_page="information", ca_group_requires_admin=True, ca_requires_admin=True,
        ca_description="<i>Select this if you would like to alter the default citation.</i>",
        ca_widget=deform.widget.CheckboxWidget(template="checked_conditional_input", inverted=True),)

    # Autocomplete from project title
    citation_title = Column(String(512), ca_name="dc:biblioGraphicCitation.dc:hasPart.dc:title",
        ca_order=next(order_counter), ca_placeholder="", ca_missing="", ca_page="information",
        ca_group_collapsed=False, ca_group_start='citation', ca_group_title="Citation", ca_group_requires_admin=True,
        ca_group_description="<i>Citation is fully automated but users with adequate permissions may edit it manually, "
                             "the user is responsible for ensuring custom citation details are correct.</i>")

    send_citation = Column(String(100), ca_order=next(order_counter), ca_default="on", ca_page="information", ca_widget=deform.widget.HiddenWidget())
    use_curation = Column(String(100), ca_order=next(order_counter), ca_default="useCuration", ca_page="information", ca_widget=deform.widget.HiddenWidget(),)

    # Date of publication (either dataset publish date or date added to redbox)
    citation_publish_date = Column(Date(), ca_order=next(order_counter), ca_page="information")
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
    citation_data_type = Column(String(256), ca_order=next(order_counter), ca_page="information")
    # Unknown
    citation_context = Column(String(512), ca_name="dc:biblioGraphicCitation.dc:hasPart.skos:scopeNote", ca_order=next(order_counter), ca_placeholder="citation context", ca_missing="", ca_page="information",)
    citation_string = Column(String(512), ca_name="dc:biblioGraphicCitation.skos:prefLabel", ca_order=next(order_counter), ca_page="information",
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
        ca_child_widget=deform.widget.MappingWidget(template="inline_mapping", readonly_template="readonly/inline_mapping"), ca_child_title="Related Publication",
        ca_help="Please provide details on any publications that are related to this project including their title and URL with an optional note.")

    related_websites = relationship('RelatedWebsite', ca_order=next(order_counter), ca_title="Related Websites", ca_page="information",
        cascade="all, delete-orphan",
        ca_child_widget=deform.widget.MappingWidget(template="inline_mapping", readonly_template="readonly/inline_mapping"), ca_child_title="Related Website",
        ca_help="Please provide details on any websites that are related to this project including their title and URL with an optional note.")

    attachments = relationship('Attachment', ca_order=next(order_counter), ca_title="Attachments (Uploading to ReDBox isn't supported at this time)",
        ca_missing=None, ca_page="information", ca_child_widget=deform.widget.MappingWidget(template="inline_mapping", readonly_template="readonly/inline_mapping"),
        cascade="all, delete-orphan",
        ca_help="Optionally provide additional information as attachments.")
#    notes = relationship('Note', ca_order=next(order_counter), ca_description="Enter administrative notes as required.", ca_missing=None, ca_page="information",
#        ca_group_end="additional_information")


def create_project_validator(form, value):
    """
    Create project validator for the create project page, this validates that:
    - Either a valid grant is entered or the no_activity checkbox is unselected (unselected means don't use activity).
    - Either a valid template is selected or the use_template checkbox is unselected.
    - A valid project manager is entered using the mint lookup autocomlete widget
    - A valid project lead is entered using the mint lookup autocomlete widget

    :param form:
    :param value:
    :return:
    """
    error = False
    exc = colander.Invalid(form) # Uncomment to add a block message: , 'At least 1 research theme or Not aligned needs to be selected')

    mint = MintLookup(None)

    if value['use_template'] is True and value['template'] == colander.null:
        exc['template'] = "Please select the template to use."
        error = True

    if value['no_activity'] is True and value['grant'] == colander.null:
        exc['grant'] = "'There is an associated research grant' must be un-selected if a research grant isn't provided."
        error = True
    elif value['no_activity'] is True:
        if mint.get_from_identifier(value['grant']) is None:
            exc['grant'] = "The entered activity isn't a valid Mint identifier.  Please use the autocomplete feature to ensure valid values."
            error = True

    if mint.get_from_identifier(value['project_lead']) is None:
        exc['project_lead'] = "The entered project lead isn't a valid Mint identifier.  Please use the autocomplete feature to ensure valid values."
        error = True

    if mint.get_from_identifier(value['data_manager']) is None:
        exc['data_manager'] = "The entered data manager isn't a valid Mint identifier.  Please use the autocomplete feature to ensure valid values."
        error = True

    if error:
        raise exc


########################################################################################################################
################################ MODELS FOR CONFIGURING DATA INGESTION PAGES ###########################################
########################################################################################################################

class LocationOffset(CAModel, Base):
    """
    Location offsets provide the ability to set a dataset's location as an offset from the selected dataset location
    or a data entry's location as an offset from the dataset's location.

    This is usefull for situations where the distance from a set point is more logical than the actual location itself,
    such as this sensor is 1m higher than the base location.
    """
    order_counter = itertools.count()

    __tablename__ = 'location_offset'
    id = Column(Integer, primary_key=True, ca_force_required=False, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dam_id = Column(Integer, nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dam_version = Column(String(128), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'), nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    data_entry_id = Column(Integer, ForeignKey('data_entry.id'), nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    x = Column(Float(), ca_title="Latitude Offset/X (meters)",ca_order=next(order_counter), ca_placeholder="eg. 1 is East 3m", ca_widget=deform.widget.TextInputWidget(size=10, css_class="full_width", regex_mask="^(((\\\\.\\\\d*)?)|(\\\\d+(\\\\.\\\\d*)?))$", strip=False))
    y = Column(Float(), ca_title="Longitude Offset/Y (meters)",ca_order=next(order_counter), ca_placeholder="eg. 1 is North 3m", ca_widget=deform.widget.TextInputWidget(size=10, css_class="full_width", regex_mask="^(((\\\\.\\\\d*)?)|(\\\\d+(\\\\.\\\\d*)?))$", strip=False))
    z = Column(Float(), ca_title="Elevation Offset/Z (meters)",ca_order=next(order_counter), ca_placeholder="eg. 1 is Higher 3m", ca_widget=deform.widget.TextInputWidget(size=10, css_class="full_width", regex_mask="^(((\\\\.\\\\d*)?)|(\\\\d+(\\\\.\\\\d*)?))$", strip=False))

    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z



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
    ('file', 'File'),
    ('website', 'Website'),
    ('email', 'Email'),
    ('phone', 'Phone'),
    ('date', 'Date picker'),
    ('hidden', 'Hidden (Used by custom processing only)'),
    )

class MethodAttachment(CAModel, Base):
    """
    An attachment to further describe the data collection method, this would typically be a data sheet or similar.
    """
    order_counter = itertools.count()

    __tablename__ = 'method_attachment'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('method.id'), nullable=False, ca_widget=deform.widget.HiddenWidget())

    attachment = Column(String(512),  ca_widget=upload_widget)
    note = colander.SchemaNode(colander.String(), placeholder="eg. data sheet", widget=deform.widget.TextInputWidget(css_class="full_width"))


class MethodWebsite(CAModel, Base):
    """
    A website that futher describes the data collection method, this may give in-depth details of the science behind
    the method used or where the chosen method was derived from.
    """
    order_counter = itertools.count()

    __tablename__ = 'method_website'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('method.id'), nullable=False, ca_widget=deform.widget.HiddenWidget())

    title = Column(String(256), ca_title="Title", ca_placeholder="eg. Great Project Website", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40))
    url = Column(String(256), ca_validator=colander.url, ca_title="URL", ca_placeholder="eg. http://www.somewhere.com.au", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40))
    notes = Column(Text(), ca_title="Notes", ca_missing="", ca_placeholder="eg. This article provides additional information on xyz", ca_widget=deform.widget.TextInputWidget(css_class="full_width", size=40))

# many-to-many association table for the MethodSchema parent's
method_schema_to_schema = Table("schema_to_schema", Base.metadata,
    Column("child_id", Integer, ForeignKey("method_schema.id"), primary_key=True),
    Column("parent_id", Integer, ForeignKey("method_schema.id"), primary_key=True)
)

# TODO: Test that schemas are fully recursive (eg. parents can have parents)
class MethodSchemaField(CAModel, Base):
    """
    A custom fields to add to a MethodSchema this includes:
    - Data type
    - Special data type attributes such as values for select fields
    - field name (internal_name)
    - Form display options such as placeholder, display name (_name) and description.
    """

    order_counter = itertools.count()

    __tablename__ = 'method_schema_field'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    method_schema_id = Column(Integer, ForeignKey('method_schema.id'),  nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    # The ingester name can't have spaces, which is unintuitive to the end user.
    internal_name = Column(String(256), ca_widget=deform.widget.HiddenWidget(),)
    _name = Column(String(256), ca_title="Name", ca_placeholder="eg. Temperature", ca_force_required=True,
        ca_widget=deform.widget.TextInputWidget(css_class="full_width custom_field_name"),)
    description = Column(Text(), ca_title="Description", ca_placeholder="eg. Calibrated temperature reading", ca_widget=deform.widget.TextInputWidget(css_class="full_width custom_field_description"))

    type = Column(String(100), ca_title="Field Type",
        ca_widget=deform.widget.SelectWidget(values=field_types, css_class="field_type"),
        ca_description="",
        ca_placeholder="Type of field that should be shown.",ca_force_required=True)

    units = Column(String(256), ca_placeholder="eg. mm", ca_widget=deform.widget.TextInputWidget(css_class="full_width custom_field_units"),)#ca_force_required=True)

    placeholder = Column(String(256), ca_title="Example", ca_placeholder="eg. 26.3", ca_widget=deform.widget.TextInputWidget(css_class="full_width custom_field_example"))
    default = Column(String(256), ca_title="Default Value", ca_placeholder="", ca_widget=deform.widget.TextInputWidget(css_class="full_width custom_field_default"))
    values = Column(Text(), ca_title="List of Values", ca_placeholder="Provide possible selections", ca_widget=deform.widget.TextInputWidget(css_class="full_width custom_field_values"))
    #    validators = Column(String(256), ca_title="Validator", ca_placeholder="eg. Numerical value with decimal places or what values are expected such as for a dropdown box", ca_widget=deform.widget.TextInputWidget(css_class="full_width custom_field_validators"))
    notes = Column(String(256), ca_title="Admin Notes", ca_placeholder="eg. Please read this field from the uploaded files, it will follow a pattern like temp:xxx.xx", ca_widget=deform.widget.TextAreaWidget(css_class="full_width custom_field_notes"))

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if value is not None:
            self.internal_name = value.lower().replace(" ", "_")
        self._name = value

    def __setattr__(self, key, value):
        if key == "_name" and  value is not None:
            self.internal_name = value.lower().replace(" ", "_")

        super(MethodSchemaField, self).__setattr__(key, value)

    def __init__(self, name=None, type=None, description=None, units=None, placeholder=None, default=None, values=None, validators=None, notes=None):
        self.name = name
        self.description = description
        self.units = units
        self.placeholder = placeholder
        self.default = default
        self.values = values
        self.validators = validators
        self.notes = notes
        self.type = type

class MethodSchema(CAModel, Base):
    """
    Represents a data schema or basically defines the database table to store the ingested data in:
    - Schema type identifies whether this schema is for data entries or calibrations
    - Setting template schema to True will allow this schema to be selected as a standardised field (parent schema)
    - parents are other MethodSchema's that this schema extends, or in ither words this schema will have all
      custom_fields that its parents have.
    - custom_fields define data that is stored (eg. each custom field is a column in the defined table).
    """
    order_counter = itertools.count()

    __tablename__ = 'method_schema'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dam_id = Column(Integer, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dam_version = Column(String(128), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    template_schema = Column(Boolean, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter)) # These are system schemas that users are encouraged to extend.

    schema_type = Column(String(256), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())


    name = Column(String(256), ca_order=next(order_counter), ca_title="", ca_placeholder="eg. Temperature with sensor XYZ calibration data",
        ca_widget=deform.widget.TextInputWidget(template="hidden", readonly_template="hidden"), )
    #        ca_help="Try to enter a unique name that easily identifies this schema.")
    #    nominate_as_template = Column(Boolean, ca_order=next(order_counter), ca_default=False, ca_title="Nominate this schema as a template",
    #        ca_help="Use this checkbox to suggest to admins that it would be helpful for this schema to be added as a template") # These are system schemas that users are encouraged to extend.
    parents = relationship("MethodSchema",ca_order=next(order_counter),
        secondary=method_schema_to_schema,
        primaryjoin=id==method_schema_to_schema.c.child_id,
        secondaryjoin=id==method_schema_to_schema.c.parent_id,
        ca_title="Standardised data fields (Recommended where possible)",
        ca_widget=deform.widget.SequenceWidget(template="method_schema_parents_sequence",
            readonly_template="readonly/method_schema_parents_sequence"),
        ca_child_title = "Standard Data Field",
        ca_child_widget=deform.widget.MappingWidget(template="method_schema_parents_mapping",
            readonly_template="readonly/method_schema_parents_mapping", item_template="method_schema_parents_item",
            readonly_item_template="readonly/method_schema_parents_item"),
        ca_help="<p>Using standardised data fields makes your data more compatible and searchable within the system.</p>",
        ca_description="<i>Please request additional standardised data fields through the contact form.</i>")

    custom_fields = relationship("MethodSchemaField", ca_order=next(order_counter), ca_child_title="Custom Field",
        cascade="all, delete-orphan",
        ca_child_widget=deform.widget.MappingWidget(item_template="method_schema_field_item", readonly_item_template="readonly/method_schema_field_item"),
        ca_help="Data that needs to be searchable but isn't a common measurement.",
    )

#    method_id = Column(Integer, ForeignKey('method.id'),  nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
#    methods = relationship("Method", ca_order=next(order_counter), ca_exclude=True,)

def method_schema_validator(form, value):
    """
    Validate that the schema has at least 1 field and doesn't have custom fields or parent custom_fields with
    duplicate names.

    :param form: MethodSchema Form to validate on
    :param value: value to validate
    :return: None, raise a colander.Invalid error if the schema or any of the custom fields don't have a name.
    """
    error = False
    exc = colander.Invalid(form) # Uncomment to add a block message: , 'At least 1 research theme or Not aligned needs to be selected')

    # Check that there is at least 1 field
    if len(value['method:data_type:custom_fields']) + len(value['method:data_type:parents']) == 0:
        exc.msg = "The data configuration must have at least one standardised or custom field."
        error = True

    # Check that each field has a name
    for i in range(len(value['method:data_type:custom_fields'])):
        if not value['method:data_type:custom_fields'][i]['methodschemafield:_name']:
            exc['method:data_type:custom_fields'] = "All fields require a valid name to be set."

    # Check for fields with duplicate names
    duplicates = find_duplicate_names(value)
    if len(duplicates) > 0:
        for name in duplicates:
            exc[name] = "All field names in the schema must be unique.  Please check " + str(name)

    if error:
        raise exc

def find_duplicate_names(values, names=None, parent=False):
    # FIXME: Deform schemas for parents only go 1 level deep - needs to read parents from DB to check fully recursive.
    """
    Helper method to identify if two custom fields, or parent fields have the same name.  This is used in the
    schema_validator.

    :param names: Names that have already been found, this is used for recursibe calls.
    :param values: Form values to be checked.
    :return: Array of all duplicate field names.
    """
    if not names: names = []
    duplicates = []

    name_key = 'methodschemafield:_name'
    if parent:
        parent_key = 'methodschema:parents'
        custom_fields_key = 'methodschema:custom_fields'
    else:
        parent_key = 'method:data_type:parents'
        custom_fields_key = 'method:data_type:custom_fields'

    if parent_key in values:
        for parent in values[parent_key]:
            duplicates.extend(find_duplicate_names(parent, names, True))

    for field in values[custom_fields_key]:
        if field[name_key] in names:
            duplicates.append(field[name_key])
        else:
            names.append(field[name_key])

    return duplicates

#    if len(value.custom_fields) == 0 and len(value.parents) == 0:
#        return colander.Invalid(form, 'A valid data type needs to be entered, add a template data type and/or add
#               custom fields')

class _sampling(Column):
    """
    Abstract the sampling field out of the datasources so they are consistent.

    Sampling indicates when a data source that accesses external resources should check to see if there is anything new.
    """
    def __init__(self, **kw):
        super(_sampling, self).__init__(INTEGER(), ca_title="Periodic Sampling (How often should new files be looked for)",
            ca_widget=deform.widget.TextInputWidget(regex_mask="^(\\\\d*)$", strip=False),
            ca_help="Provide the number of minutes between checks for new files."
                    "<i>(Advanced) If you require something more advanced almost any custom needs can be implemented "
                    "with a custom processing script (below).</i>", **kw)


def _custom_processor(**kw) :
    """
    Abstract the custom processing script field out of the datasources so they are consistent

    Custom processors are used for customising how data is stored and indexed when ingested, they are part of data
    sources.

    :param kw: ColanderAlchemy arguments that define the database table and form display.
    :return: The Database Column/form element that this function created.
    """
    return relationship("CustomProcessor", uselist=False, ca_collapsed=False,
        ca_title="Custom Data Processing (Read data from the found file)",
        ca_help="Custom data processing is a flexible method of adding data to this system without knowing what that data will be in advance:"
                "<ul>"
                "<li>Pull data sources read a file from the folder address entered above</li>"
                "<li>Data configuration provided in the methods step sets up what data is important/searchable and how it is stored.</li>"
                "<li>Custom data processing configures how data is read from the file and added to this system as indexed data.</li>"
                "</ul>",
        ca_description="<i>If you haven't used this system before you will need help to create a processing script, "
                       "describe your requirements as best you can below and an administrator will contact you.</i>"
        , **kw)

class _uri_address(Column):
    """
    Abstract the uri_address field out of the datasources so they are consistent.

    The URI address provides the location of external resources that the data source looks at (eg. a file server).
    """
    def __init__(self, **kw):
        super(_uri_address, self).__init__(Text(), ca_title="Address (URL/URI)", ca_validator=colander.url,
            ca_placeholder="eg. http://example.com.au/folder/",
            ca_help="Provide the url that should be polled for data, all files in the folder will be used unless they"
                    " are excluded by the filename pattern.<i>(Advanced) The filename will be passed into the "
                    "custom processing script so that information can be read from it (eg. a timestamp).</i>", **kw)



class _data_file(Column):
    """
    Abstract the data file field out of the datasources so they are consistent.
    The data file field is used to hold raw data for most data sources.
    """
    def __init__(self, **kw):
        super(_data_file, self).__init__(Integer, ca_title="File Field",
            ca_name="data_file",
            ca_widget=deform.widget.SelectWidget(),
            ca_help="Select the custom field (setup in data configuration on the methods page) that the file read from the above folder address will be saved to (this is the raw data).<br />",
            ca_description="<i>This will be empty if the methods, data configuration doesn't have a custom field of type file.</i>", **kw)



class CustomProcessor(CAModel, Base):
    """
    Custom processor table/form that holds all information needed to customise how data is processed and added to the
    data storage schema (data configuration).

    This includes the python script itself as well as parameters and user descriptions.
    """
    order_counter = itertools.count()

    __tablename__ = 'custom_processor'
    id = Column(Integer, primary_key=True, nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    have_script = Column(Boolean, ca_title="I already have a processing script and know what I'm doing", ca_default=False, ca_order=next(order_counter),
        ca_widget=deform.widget.CheckboxWidget(template="checked_conditional_input", inverted=True),)

    custom_processing_parameters = Column(String(512),ca_order=next(order_counter),
        ca_group_start="custom_script", ca_group_title="Custom Processing Script",
        ca_description="Comma separated list of script specific parameters.",
        ca_help="Parameters are added via python string formatting syntax, in your script add %s or %(<i>name</i>)s wherever you want a parameter inserted (parameters must either be added in the correct order or be named).")

    custom_processor_script = Column(String(512), ca_missing=colander.null ,ca_order=next(order_counter),ca_widget=upload_widget,
        ca_title="Upload custom processing script", ca_group_end="custom_script",
        ca_description="Upload a custom Python script to "\
                       "process the data in some way.  The processing script API can be found "\
                       "<a title=\"Python processing script API\"href=\"\">here</a>.")

    custom_processor_desc = Column(String(256),ca_order=next(order_counter), ca_widget=deform.widget.TextAreaWidget(),
        ca_placeholder="eg. Extract the humidity and temperature values from the raw data file and add them to the humidity and temperature fields setup in the data configuration.",
        ca_title="Describe custom processing requirements (or describe your script)", ca_missing="",)


class FormDataSource(CAModel, Base):
    """
    A data source that only ingests data from manual user uploads (eg. empty/no data source).

    This is really provided to give a user friendly experience.
    """
    order_counter = itertools.count()

    __tablename__ = 'form_data_source'
    id = Column(Integer, primary_key=True, nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'),  nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
#    data_file = Column(Integer, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(),)

class PullDataSource(CAModel, Base):
    """
    Ingest data from an external file server, it is anticipated that this is the data source that will be used in most
    cases.
    - The address of the external file server is provided via the uri field.
    - Optional filtering of files can be specified by filename_pattern.
    - periodic_sampling configures the time period between polls for new data.
    - custom processor defines how data is read from the file into fields setup by data configuration (the data schema).
    """
    order_counter = itertools.count()

    __tablename__ = 'pull_data_source'
    id = Column(Integer, primary_key=True, nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'),  nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    #    data_file = Column(Integer, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(),)

    uri = _uri_address(ca_order=next(order_counter))

    data_file = _data_file(ca_order=next(order_counter))

    #    # Id of the data_entry schema field used for the datasource file
    #    file_field = Column(Integer, ca_order=next(order_counter), ca_title="File Field",
    #        ca_widget=deform.widget.SelectWidget(),
    #        ca_help="Select the custom field (setup in data configuration on the methods page) that the file read from the above folder address will be saved to (this is the raw data).<br />",
    #        ca_description="<i>This will be empty if the methods, data configuration doesn't have a custom field of type file.</i>")

    # TODO: filename_patterns
    filename_pattern=Column(String(100),ca_order=next(order_counter), ca_title="(Advanced) Filename Pattern (Regex)",
        ca_description="<i>Unless you know how to use this or that you need this, just leave it blank.</i><br />",
        ca_help="Allows filtering of file names, <b>it is recommended that you seek help</b>.  For the brave, <a href='http://docs.python.org/2/library/re.html'> here is the the programmer documentation</a>.")

    periodic_sampling = _sampling(ca_order=next(order_counter))
    custom_processor_id = Column(Integer, ForeignKey('custom_processor.id'),  nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    custom_processor = _custom_processor(ca_order=next(order_counter))

#            ca_group_help="Provide a filename pattern (Regex) that identifies which files should be ingested.")
#     mime_type=Column(String(100),ca_order=next(order_counter), ca_title="File MIME Type",
#                ca_group_help="Provide a file MIME type that identifies the file content type.")

#    selected_sampling = Column(String(64), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter),
#        ca_group_start="sampling", ca_group_title="Data Sampling (How often/when should new files be looked for)", ca_group_collapsed=False, ca_group_validator=custom_processing_validator,
#        ca_group_widget=deform.widget.MappingWidget(item_template="choice_mapping_item", template="choice_mapping"),
#        ca_group_missing=colander.null,
#        ca_group_description="<i>Select one of the below.</i>")

#    periodic_sampling = Column(INTEGER(),ca_order=next(order_counter), ca_title="Periodic Sampling (How often should new files be looked for)",
#        ca_widget=deform.widget.TextInputWidget(regex_mask="^(\\\\d*)$", strip=False),
#        ca_help="Provide the number of minutes between checks for new files."
#                "<i>(Advanced) If you require something more advanced almost any custom needs can be implemented with a custom processing script (below).</i>")


#    cron_sampling = Column(String(100),ca_order=next(order_counter), ca_title="Cron Based Sampling (When data is collected)",
#        ca_widget=deform.widget.TextInputWidget(template="chron_textinput"),
#        ca_help="<p>Provide repetitive filtering condition for retrieving data using the selectors below.</p>" \
#                "<p>If you require something more advanced you can provide your own cron string or any filtering can be achieved by adding a custom "\
#                "sampling script below.</p><p>The sampling script API can be found <a href="">here</a></p>.")
#
#
#    #    stop_conditions = Column(String(100),ca_order=next(order_counter), ca_title="Stop conditions (TODO)", ca_child_title="todo")
#
#    custom_sampling_desc = Column(String(256),ca_order=next(order_counter), ca_widget=deform.widget.TextAreaWidget(),
#        ca_group_start="custom_sampling", ca_group_title="Custom Data Sampling/Filtering",
#        ca_placeholder="eg. Only ingest the first data value of every hour.",
#        ca_title="Describe custom sampling needs", ca_missing="",
#        ca_description="Describe your sampling requirements and what your uploaded script does, or what you will need help with.")
#
#    custom_sampling_script = Column(String(512), ca_missing=colander.null ,ca_order=next(order_counter),ca_widget=upload_widget,
#        ca_title="Upload custom sampling script",
#        ca_group_end="sampling",
#        ca_description="Upload a custom Python script to "\
#                       "sample the data in some way.  The sampling script API can be found "\
#                       "<a title=\"Python sampling script API\"href=\"\">here</a>.")




class PushDataSource(CAModel, Base):
    """
    At this point the push data source isn't fully supported, the intended purpose is to allow external (authenticated)
    applications/programs to push their data into the ingester platform through the ingesterapi.
    """

    order_counter = itertools.count()

    __tablename__ = 'push_data_source'
    id = Column(Integer, primary_key=True, nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'),  nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    #    data_file = Column(Integer, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(),)

    api_key = Column(Text(), ca_title="(Advanced) API Key (Password to use this functionality)", ca_order=next(order_counter),
        ca_default="TODO: Auto-generate key",
        ca_description="The password that is needed to push your data into to this systems API, the API documentation can be found <a href=''>here</a>.")

sos_variants = (("52North", "52 North"),)
sos_versions = ((SOSVersions.v_1_0_0, "1.0.0"),)

class SOSScraperDataSource(CAModel, Base):
    """
    Dump all data from a Sensor Observation Service (SOS) into the ingester platform, custom processors can further
    parse specific sensors/data as needed.
    """
    order_counter = itertools.count()

    __tablename__ = 'sos_scraper_data_source'
    id = Column(Integer, primary_key=True, nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'),  nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    #    data_file = Column(Integer, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(),)

    uri = _uri_address(ca_order=next(order_counter))

    data_file = _data_file(ca_order=next(order_counter))

    #    uri = Column(Text(), ca_title="SOS Address (URL)", ca_order=next(order_counter), ca_validator=colander.url,
    #        ca_placeholder="eg. http://example.com.au/folder/",
    #        ca_help="Provide the url of the external Sensor Observation Service.")

    #    # Id of the data_entry schema field used for the datasource file
    #    data_field = Column(Integer, ca_order=next(order_counter),
    #        ca_widget=deform.widget.SelectWidget(), ca_title="Data File Field (Raw data is read as a file)",
    #        ca_help="Select the custom field (see data configuration in methods) that the raw SOS data will be saved to.",
    #         ca_description="<i>If there is no selection available you need to add a custom field of type file to this datasets method.</i>")

    variant = Column(String(64), ca_order=next(order_counter), ca_widget=deform.widget.SelectWidget(values=sos_variants),
        ca_description="<i>If you are unsure what this means leave it as the default</i>",
        ca_help="Select the external Sensor Observation Service (SOS) implementation variant, please contact the administrators if you require a different variant.")
    version = Column(String(64), ca_order=next(order_counter), ca_widget=deform.widget.SelectWidget(values=sos_versions),
        ca_help="Select the external Sensor Observation Service (SOS) implementation version, please contact the administrators if you require a different version.",
        ca_description="<i>If you are unsure what this means leave it as the default</i>")

    periodic_sampling = _sampling(ca_order=next(order_counter))
    custom_processor_id = Column(Integer, ForeignKey('custom_processor.id'),  nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    custom_processor = _custom_processor(ca_order=next(order_counter))


@colander.deferred
def dataset_select_widget(node, kw):
    """
    Deform widget for selecting fields of type file from the associated data configuration (data schema as setup on the
    methods page).

    :param node: The node/form element that this widget is for.
    :param kw: Widget arguments such as template
    :return: The widget that this function creates.
    """

    if 'datasets' in kw:
        datasets = kw['datasets']
        dataset_values = []
        for dataset in datasets:
            if dataset.method is None:
                continue

            project = DBSession.query(Project).filter_by(id=dataset.project_id).first()

            height_text = ""
            if len(dataset.dataset_locations) > 0 and dataset.dataset_locations[0] is not None:
                height_text =  (", %sm above MSL") % dataset.dataset_locations[0].elevation
            location_text = "none"
            if len(dataset.dataset_locations) > 0 and dataset.dataset_locations[0].location is not None:
                location_text = "%s (%s, %s%s)" % (dataset.dataset_locations[0].name, dataset.dataset_locations[0].get_latitude(),
                                                   dataset.dataset_locations[0].get_longitude(), height_text)
#                dataset_name = "%s at %s collected by %s" %\
#                               (project.information.project_title, location_text, dataset.method.method_name)
            dataset_name = "%s at %s" % (dataset.method.method_name, location_text)
            dataset_values.append((dataset.id, dataset_name))
        return deform.widget.SelectWidget(values=dataset_values, template="source_dataset_select")


class DatasetDataSource(CAModel, Base):
    """
    Further processes previously ingested data and stores it as per the associated methods data configuration.
    - Select another dataset as the data source for this dataset.
    - When the selected dataset receives data, the output from its custom processing script is given to this data source.
    - This data source then processes it further storing more relevant data (eg. calibrated vs raw).

    This allows chained processing and storage of data, such as with the artificial tree where raw data for the whole
    tree is ingested in one dataset and per sensor datasets further process that file into indexed temperatures
    and humidity's.
    """
    order_counter = itertools.count()

    __tablename__ = 'dataset_data_source'
    id = Column(Integer, primary_key=True, nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'),  nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    # TODO: Selection of datasets
    dataset_data_source_id = Column(Text(), ca_title="Source Dataset", ca_order=next(order_counter), ca_widget=dataset_select_widget,
        ca_help="The dataset to retrieve processed data from.  This allows chaining of data and processing such that:"
                "<ul>"
                "<li>A dataset could be configured to use a pull datasource to read files from an external folder and save the file as raw data.</li>"
                "<li>The results of that could then be read by n other dataset using a dataset data source and further processed the data into seperate, processed results.</li>"
                "</ul>"
                "This allows separating and processing of aggregated data, such as data from many sensors in a single file.",
        ca_description="<i>If there are no items to select from then no other datasets have been setup yet!</i>")

    custom_processor_id = Column(Integer, ForeignKey('custom_processor.id'),  nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    custom_processor = _custom_processor(ca_order=next(order_counter))


class MethodTemplate(CAModel, Base):
    """
    Method templates that can be used to pre-populate a method as well as datasets created for that method.
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
    """
    Represents a method (eg. the methods page), which includes:
    - metadata to describe the method (name, description, related websites and attachments).
    - Data source (how the data is ingested)
    - Data configuration (how data is stored and indexed for searching).
    - Linked to datasets (datasets page).
    """
    order_counter = itertools.count()

    __tablename__ = 'method'
    project_id = Column(Integer, ForeignKey('project.id'), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
    id = Column(Integer, ca_order=next(order_counter), primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    #    service_metadata_id = Column(Integer, ForeignKey('service_metadata.id'), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())

    method_template_id = Column(Integer, ForeignKey('method_template.id', ForeignKey('method_template.id'), use_alter=True, name="fk_method_template_id"), nullable=True, ca_order=next(order_counter), ca_title="Select a template to base this method off (Overrides all fields)",
        ca_widget=deform.widget.TextInputWidget(template="method_template_mapping", strip=False),
        ca_help="<p>Method templates provide pre-configured data collection methods and pre-fill as much information as possible to make this process as quick and easy as possible.</p>"
                "<i>Please contact the administrators to request new templates.</i>",
        ca_description="<ol><li>First select the category or organisational group on the left hand side.</li>"
                       "<li>Then select the most relevant template from the list on the right hand side.</li></ol>")

    method_name = Column(String(256), ca_order=next(order_counter), ca_force_required=True,
        ca_placeholder="Searchable identifier for this input method (eg. Invertebrate observations)",
        ca_description="Give the data collection method a name, this will be used in the title of the generated dataset"
                       " records.",
        ca_help="<p>The entered name will be used in the generated dataset record as: &lt;project title&gt; at "
                "&lt;location name&gt;(&lt;lat, long, height&gt;) collected by &lt;method name&gt;</p>"
                "<p>The name and description will also be used to identify the method used in the <i>datasets</i>"
                " step</p>")
    method_description = Column(Text(), ca_order=next(order_counter), ca_title="Description",
        ca_widget=deform.widget.TextAreaWidget(rows=10), ca_force_required=True,
        ca_description="Provide a description of this method, this should include what, why and how the data is being "
                       "collected but <b>Don\'t enter where or when</b> as this information is relevant to the dataset,"
                       " not the method.",
        ca_placeholder="Enter specific details for this method, users of your data will need to know how reliable your"
                       " data is and how it was collected.")

    data_sources=(
        (FormDataSource.__tablename__,"Web form/manual only"),
        (PullDataSource.__tablename__,"Pull from external file system"),
        (SOSScraperDataSource.__tablename__,"Sensor Observation Service"),
        (PushDataSource.__tablename__,"<i>(Advanced)</i> Push to this website through the API"),
        (DatasetDataSource.__tablename__,"<i>(Advanced)</i> Output from other dataset"),
        )

    data_source =  Column(String(50), ca_order = next(order_counter), ca_widget=deform.widget.RadioChoiceWidget(values=data_sources, template="datasource_radio_choice"),
        ca_title="Data Source (How the data gets transferred into this system)", ca_force_required=True,
        ca_description="<i>Additional configurations may be required on the datasets page (eg. each dataset for a pull from external file system method will need it's location set on a per dataset basis).</i>",
        ca_help="<p>'Web form/manual' is the default (other data sources also allow adding data through a web form), 'Output from other dataset' provides advanced "
                "processing features and the other three methods allow automatic ingestion from compatible sensors or services:</p>"
                "<ul><li><b>Web form/manual only:</b> Only use an online form accessible through this interface to manually upload data (No configuration required).</li>"\
                "<li><b>Pull from external file system:</b> Setup automatic polling of an external file system from a URL location, when new files of the correct type and naming convention are found they are ingested (Configuration required on datasets page).</li>"\
                "<li><b><i>(Advanced)</i> Push to this website through the API:</b> Use the XMLRPC API to directly push data into persistent storage, on project acceptance you will be emailed your API key and instructions (No configuration required).</li>"\
                "<li><b>Sensor Observation Service:</b> Set-up a sensor that implements the Sensor Observation Service (SOS) to push data into this systems SOS server (Configuration required on datasets page).</li>"\
                "<li><b><i>(Advanced)</i> Output from other dataset:</b> Output from other dataset: </b>This allows for advanced/chained processing of data, where the results of another dataset can be further processed and stored as required (Configuration required on datasets page).</li></ul>"\
                "<p><i>Please refer to the help section or contact the administrators if you need additional information.</i></p>",
        ca_placeholder="Select the easiest method for your project.  If all else fails, manual file uploads will work for all data types.")

    method_schema_id = Column(Integer, ForeignKey('method_schema.id'),  nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    data_type = relationship("MethodSchema", ca_order=next(order_counter), uselist=False, ca_widget=MethodSchemaWidget(),
        ca_title="Data Configuration", ca_validator=method_schema_validator,
        ca_collapsed=False,
        ca_help="<i>Configuration of the type of data being collected is an advanced topic, help can be requested through the contact forms.</i>"
                "<ol>"
                "<li>Think about what data is being collected, how the data is originally stored and what needs to be searchable.</li>"
                "<li>(Skip if using 'web form/manual') In most cases data is originally stored as a file of some kind, if this is the case add a custom field of type file (it is good practice to permenently store the raw data for future needs).</li>"
                "<li>Identify which of your data needs to be searchable and is also a common measurement (eg. temperature, weight, humidity - not calibrations or anything project specific), where available add these in the standardised data fields section.</li>"
                "<li>Add fields that need to be searchable but aren't common measurements in the custom fields section.</li>"
                "</ol>",
        ca_description="Configure how collected data should be stored, displayed and searched."
        #                       "<ul><li>Each field added to the the data type will be fields on the data entry form, these fields will be searchable.</li></ul>"

        #                       "<p>Extend existing data types wherever possible - only create custom fields or schemas if you cannot find an existing schema.</p>"
    )

    method_attachments = relationship('MethodAttachment', ca_order=next(order_counter), ca_missing=colander.null, ca_child_title="Attachment",
        cascade="all, delete-orphan",
        ca_title="Attachment (Such as datasheets, collection processes, observation forms)",
        ca_help="Attach information about this method, this is preferred to websites as it is persistent.  "\
                "Example attachments would be sensor datasheets, documentation describing your file/data storage schema or calibration data.")

    method_website = relationship("MethodWebsite", ca_order=next(order_counter), ca_missing=colander.null,
        cascade="all, delete-orphan",ca_title="Further information website (Such as manufacturers website or supporting web resources)",
        ca_child_widget=deform.widget.MappingWidget(template="inline_mapping", readonly_template="readonly/inline_mapping"), ca_child_title="Website",
        ca_help="If there are web addresses that can provide more information on your data collection method, add them here.  Examples may include manufacturers of your equipment or an article on the calibration methods used.")

    datasets = relationship("Dataset", ca_order=next(order_counter), ca_missing=colander.null,
        cascade="all, delete-orphan", ca_widget=deform.widget.HiddenWidget(), ca_exclude=True)

    method_template = relationship("MethodTemplate", primaryjoin=method_template_id==MethodTemplate.id, single_parent=True,
        ca_exclude=True, uselist=False, ca_order=next(order_counter), ca_missing=colander.null,
        cascade="all, delete-orphan", ca_widget=deform.widget.HiddenWidget())

class Dataset(CAModel, Base):
    """
    Each dataset represents a single data ingester and metadata record associated with a method.
    - The dataset configures the data source and the location for the data ingestion (for searching purposes).
    - A metadata record is only created if 'Publish Metadata Records' is selected + date to publish and the location
      are used in the creation of the metdata record.
    """
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

    date_created = Column(Date, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
    date_modified = Column(Date, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
    last_modified_by = Column(Integer, ForeignKey('user.id'),  ca_widget=deform.widget.HiddenWidget(), ca_order=next(order_counter))

    method_id = Column(Integer, ForeignKey('method.id'), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    disabled = Column(Boolean,ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(), ca_default=True)

    mint_service_id = Column(String(256), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
    mint_service_uri = Column(String(256), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())

    #    name = Column(Text(), ca_name="dc:relation.vivo:Dataset.0.dc:title", ca_title="Dataset Name (For ingesters not metadata/ReDBox records)", ca_order=next(order_counter),
    #        ca_placeholder="Provide a textual description of this dataset.",
    #        ca_help="Provide a dataset specific name that is easily identifiable within this system.", ca_force_required=True)

    publish_dataset = Column(Boolean, ca_title="Publish Metadata Record (Publicly advertise that this data exists)", ca_default=True, ca_order=next(order_counter),
        ca_widget=deform.widget.CheckboxWidget(template="checked_conditional_input", inverted=True),
        ca_help="Publish a metadata record to ReDBox for this dataset - leave this selected unless the data isn't relevant to anyone else (eg. Raw data where other users "\
                "will only search for the processed data).")

    publish_date = Column(Date(), ca_order=next(order_counter), ca_title="Date to publish*",
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
        cascade="all, delete-orphan",ca_widget=deform.widget.SequenceWidget(template='map_sequence', readonly_template='readonly/map_sequence', max_len=1, min_len=1, points_only=True, error_class="error"),
        ca_force_required=True,
        ca_child_widget=deform.widget.MappingWidget(template="inline_mapping", readonly_template="readonly/inline_mapping"),
        ca_missing="", ca_help="<p>Use the drawing tools on the map and/or edit the text representations below.</p><p>Locations are represented using <a href='http://en.wikipedia.org/wiki/Well-known_text#Geometric_Objects'>Well-known Text (WKT) markup</a> in the WGS 84 coordinate system (coordinate system used by GPS).</p>")

    location_offset = relationship('LocationOffset', uselist=False, ca_order=next(order_counter), ca_title="Location Offset (optional)",
        cascade="all, delete-orphan",
        ca_group_end="coverage", ca_widget=deform.widget.MappingWidget(template="inline_mapping", readonly_template="readonly/inline_mapping", show_label=True),
        ca_missing=colander.null, ca_help="Use an offset from the current location where the current location is the project location if valid, else the dataset location (eg. such as the artificial tree location is known so use z offsets for datasets).")

    form_data_source = relationship("FormDataSource", ca_title=None, ca_order=next(order_counter), uselist=False, ca_force_required=False, cascade="all, delete-orphan",ca_collapsed=False,)
    pull_data_source = relationship("PullDataSource", ca_order=next(order_counter), uselist=False, ca_force_required=False,cascade="all, delete-orphan",ca_collapsed=False)
    sos_scraper_data_source = relationship("SOSScraperDataSource", ca_title="Sensor Observation Service (SOS) Data Source", ca_order=next(order_counter), uselist=False, ca_force_required=False,cascade="all, delete-orphan",ca_collapsed=False,)
    push_data_source = relationship("PushDataSource", ca_title=None, ca_order=next(order_counter), uselist=False, ca_force_required=False,cascade="all, delete-orphan",ca_collapsed=False, )
    dataset_data_source = relationship("DatasetDataSource", ca_order=next(order_counter), uselist=False, ca_force_required=False,cascade="all, delete-orphan",ca_collapsed=False)

    record_metadata = relationship("Metadata", uselist=False, ca_order=next(order_counter), ca_missing=colander.null,
        cascade="all, delete-orphan", ca_widget=deform.widget.HiddenWidget(), ca_exclude=True)

    method_template = relationship("MethodTemplate", ca_order=next(order_counter), ca_missing=colander.null,
        cascade="all, delete-orphan", ca_widget=deform.widget.HiddenWidget(), ca_exclude=True)

    method = relationship("Method", ca_order=next(order_counter), ca_missing=colander.null, uselist=False, single_parent=True,
        ca_widget=deform.widget.HiddenWidget(), ca_exclude=True)


########################################################################################################################
########################################### GENERAL MODELS FOR PROJECT PAGES ###########################################
########################################################################################################################
class Region(CAModel, Base):
    """
    NOT YET IMMPLEMENTED.

    This is intended as a representation of polygons/line locations to integrate with the ingester platform.
    """
    __tablename__ = 'region'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    dam_id = Column(Integer, nullable=True, ca_widget=deform.widget.HiddenWidget())
    dam_version = Column(String(128), ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'), nullable=True, ca_widget=deform.widget.HiddenWidget())
    # TODO: Regions


# Validate that manually entered location's are correct WTK format.  Note: Multi-xxx aren't implemented.
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
    """
    Representation of a location or region on earth, this includes the coordinates in WTK format as well as a name and
    elevation above mean sea level.
    """
    order_counter = itertools.count()

    __tablename__ = 'location'
    id = Column(Integer, primary_key=True, ca_force_required=False, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dam_id = Column(Integer, nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dam_version = Column(String(128), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    metadata_id = Column(Integer, ForeignKey('metadata.id'), nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'), nullable=True, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    location_type = Column(String(10), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(), default="text")
    name = Column(String(256), ca_force_required=True,ca_order=next(order_counter), ca_help="What do you call this location?")
    location = Column(String(512), ca_validator=location_validator, ca_name="dc:coverage.vivo:GeographicLocation.0.redbox:wktRaw", ca_widget=deform.widget.TextInputWidget(css_class='map_location'),ca_order=next(order_counter),
        ca_force_required=True, ca_child_widget=deform.widget.TextInputWidget(regex_mask="^(POINT\([+-]?\d*\.?\d* [+-]?\d*\.?\d*\)) |(POLYGON\(\(([+-]?\d*\.?\d*\s[+-]?\d*\.?\d*,?\s?)*\)\))|(LINESTRING\(([+-]?\d*\.?\d*\s[+-]?\d*\.?\d*,?\s?)*\))$"),
        ca_help="<a href='http://en.wikipedia.org/wiki/Well-known_text#Geometric_Objects' title='Well-known Text (WKT) markup reference'>WTK format reference</a>")

    elevation = Column(Float(),ca_order=next(order_counter), ca_help="Elevation in meters from mean sea level", ca_widget=deform.widget.TextInputWidget(regex_mask="^(((\\\\.\\\\d*)?)|(\\\\d+(\\\\.\\\\d*)?))$", strip=False))
    # regions = relationship("Region", ca_widget=deform.widget.HiddenWidget())

    def is_point(self):
        """
        Test if this is a point rather than a polygon or other WTK type.
        """
        return self.location is not None and self.location[:5] == "POINT"

    def get_latitude(self):
        """
        get the latitude, this is only relevant for points - other types will return a NotImplementedError
        """
        if self.is_point():
            return float(self.location[6:-1].split(" ")[0].strip())

        raise NotImplementedError("Get location latitude is not implemented for anything other than points.")

    def get_longitude(self):
        """
        get the longitude, this is onlyrelevantt for points - other types will return a NotImplementedError
        """
        if self.is_point():
            return float(self.location[6:-1].split(" ")[1].strip())

        raise NotImplementedError("Get location longitude is not implemented for anything other than points.")

    def get_points(self):
        """
        NOT IMPLEMENTED - Usage is intended for integration with region's (which also aren't implemented).
        """
        return [[]]

class TransitionNote(CAModel, Base):
    """
    Simple text field to leave notes about a project on the submit page.
    """
    order_counter = itertools.count()

    __tablename__ = 'transition_note'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    date_created = Column(Date, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())

    transition =  Column(String(128), ca_widget=deform.widget.SelectWidget(values=(("none", "Note Only"),
                                                                                   ("submitted", "Submitted"), ("approved", "Approved"), ("reopened", "Re-Opened"), ("disabled", "Disabled"),
                                                                                   ("enabled", "Re-Enabled")), readonly_template="readonly/text"))
    comment = Column(Text(),
        ca_placeholder="eg. Please enter all metadata, the supplied processing script has errors, please extend the existing temperature data type so that your data is searchable, etc..."
        , ca_widget=deform.widget.TextAreaWidget(rows=3))

class ProjectNote(CAModel, Base):
    """
    Simple text field to leave notes about a project on the submit page.
    """
    order_counter = itertools.count()

    __tablename__ = 'project_note'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    comment = Column(Text(),
        ca_placeholder="eg. Please enter all metadata, the supplied processing script has errors, please extend the existing temperature data type so that your data is searchable, etc..."
        , ca_widget=deform.widget.TextAreaWidget(rows=3))

class ProjectTemplate(CAModel, Base):
    """
    Use an existing project as a template that others can use to pre-populate their projects.
    - Category allows grouping of similar templates
    - Name and description allow administrators to describe the template to users.
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

#class UntouchedFields(CAModel, Base):
#    __tablename__ = 'untouched_fields'
#    order_counter = itertools.count()
#    id = Column(Integer, ca_order=next(order_counter), primary_key=True, ca_widget=deform.widget.HiddenWidget())
#
#    project_id = Column(Integer, ForeignKey('project.id'), nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
#    dataset_id = Column(Integer, ForeignKey('dataset.id'), nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
#    method_schema_id = Column(Integer, ForeignKey('method_schema.id'), nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
#    method_schema_field_id = Column(Integer, ForeignKey('method_schema_field.id'),  nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
#    method_id = Column(Integer, ForeignKey('method.id'),nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
#
#    field_name = Column(String(100))


class UntouchedPages(CAModel, Base):
    """
    Records if a page has been submitted yet, don't validate the page until it is submitted the first time.
    """
    __tablename__ = 'untouched_pages'
    order_counter = itertools.count()
    id = Column(Integer, ca_order=next(order_counter), primary_key=True, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    general = Column(Boolean, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    description = Column(Boolean, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    information = Column(Boolean, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    methods = Column(Boolean, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    datasets = Column(Boolean, ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))


class ProjectStates(object):
    """
    Simple enumeration class for project states
    """
    OPEN, SUBMITTED, ACTIVE, DISABLED = range(4)

def project_validator(form, value):
    """
    Validate that the project as at least 1 method and at least 1 dataset.

    This is only used for checking validation on the submit page.

    :param form: The form to validate
    :param value: Appstruct used to render/validate the form
    :return: None, raise an exception if validation fails.
    """
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

def method_validator(form, value):
    """
    NOT IMPLEMENTED - Update with methods page validation if needed.

    :param form:
    :param value:
    :return:
    """
    pass

def dataset_validator(form, value):
    """
    Validates that the datasets page either doesn't publish a metadata record, or a valid publish date is given.

    :param form: Dataset schemas/form to validate
    :param value: Appstruct/values passed in for validation.
    :return: None, raise a colander.Invalid exception if the validation fails.
    """
    error = False
    exc = colander.Invalid(form) # Uncomment to add a block message: , 'At least 1 research theme or Not aligned needs to be selected')

    if value['dataset:publish_dataset'] is True and value['dataset:publish_date'] is None:
        exc['dataset:publish_date'] = "Required"
        error = True

    if error:
        raise exc


class Project(CAModel, Base):
    """
    Represents the project being setup, this is basically a wrapper tieing metadata, methods and datasets together as
    well as adding administration functionality such as project states, templating, notes and who/when it was created.

    All pages display the project schema and the ca_page attributes are used to configure what is displayed on each
    page.

    It was decided that a more logical database structure was more important than creating models that fit the
    desired page layout, so additional ColanderAlchemy functionality was implemented to support this. The ca_page
    attribute functionality is implemented in controllers/ca_scripts.
    """
    order_counter = itertools.count()

    __tablename__ = 'project'

    id = Column(Integer, ca_order=next(order_counter), primary_key=True, ca_widget=deform.widget.HiddenWidget())
    state = Column(Integer, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(), ca_missing=ProjectStates.OPEN, ca_default=ProjectStates.OPEN)

    project_creator = Column(Integer, ForeignKey('user.id'), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))

    project_creator = Column(Integer, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
    date_created = Column(Date, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
    date_modified = Column(Date, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())
    last_modified_by = Column(Integer, ForeignKey('user.id'),  ca_widget=deform.widget.HiddenWidget(), ca_order=next(order_counter))

    template_only = Column(Boolean, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget())

    information = relationship('Metadata', ca_title="", ca_order=next(order_counter),
        cascade="all, delete-orphan", ca_validator=metadata_validator,
        ca_child_collapsed=False, uselist=False,)

    #-----------------------------Method page----------------------------------------------------------

#    overall_method_description = Column(Text(), ca_order=next(order_counter), ca_title="Project wide methods description", ca_page="methods",
#        ca_widget=deform.widget.TextAreaWidget(rows=5),
#        ca_description="Provide a description for all data input methods used in the project.",
#        ca_placeholder="Provide an overview of all the data collection methods used in the project and why those methods were chosen.",
#        ca_help="<p>This will be used as the description for data collection in the project metadata record and will provide users of your data with an overview of what the project is researching.</p>"
#                "<p><i>If you aren't sure what a method is return to this description after completing the Methods page.</i></p>")

    methods = relationship('Method', ca_title="", ca_widget=deform.widget.SequenceWidget(min_len=0, template="method_sequence", readonly_template="readonly/method_sequence"), ca_order=next(order_counter), ca_page="methods",
        cascade="all, delete-orphan", ca_child_validator=method_validator,
        ca_child_collapsed=False,)
#        ca_description="Add one method for each type of data collection method (eg. temperature sensors, manually entered field observations using a form or files retrieved by polling a server...)")

    #----------------------------Dataset page------------------------------------------
    # The datasets page is dynamically generated from user input on the methods page, therefore a static
    # ColanderAlchemy schema will not be able to generate the required deform schemas:
    #   * Setup the ColanderAlchemy schema to correctly create the database
    #   * Dynamically alter the generated schema in the view
    datasets = relationship('Dataset', ca_widget=deform.widget.SequenceWidget(min_len=0, template="dataset_sequence", readonly_template="readonly/dataset_sequence"), ca_order=next(order_counter), ca_page="datasets",
        ca_child_widget=deform.widget.MappingWidget(template="dataset_mapping", readonly_template="readonly/dataset_mapping"),
        ca_child_title="Dataset", ca_child_collapsed=False, cascade="all, delete-orphan", ca_child_validator=dataset_validator)

    #-----------------------------------------Submit page---------------------------------------------------

    validated = Column(Boolean, ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(template="submit_validation"), default=False,
        ca_group_start="validation", ca_group_end="validation", ca_group_title="Validation", ca_group_collapsed=False, ca_page="submit",)

    datasets_ready = Column(Integer(), ca_order=next(order_counter), ca_widget=deform.widget.HiddenWidget(template="submit_overview"),
        ca_group_start="overview", ca_group_end="overview", ca_group_title="Summary of Datasets & Records", ca_group_collapsed=False, ca_page="submit",)

    transition_notes = relationship("TransitionNote", ca_title="State Change Notes",  ca_order=next(order_counter), ca_page="submit",
        ca_child_title="State Change Note", ca_child_name="transition_note", ca_child_widget=deform.widget.MappingWidget(template="transition_mapping"),
        cascade="all, delete-orphan", ca_widget=deform.widget.SequenceWidget(template="transition_note_sequence"),
        ca_help="Project comments that are only relevant to the provisioning system (eg. comments as to why the project was reopened after the creator submitted it).")

    project_notes = relationship("ProjectNote", ca_title="Project Notes",  ca_order=next(order_counter), ca_page="submit",
            ca_child_title="Project Note", ca_child_widget=deform.widget.MappingWidget(template="comment_mapping", readonly_template="comment_mapping"),
            cascade="all, delete-orphan", ca_widget=deform.widget.SequenceWidget(min_len=1),
            ca_help="Project comments that are only relevant to the provisioning system (eg. comments as to why the project was reopened after the creator submitted it).")

    project_template = relationship("ProjectTemplate", ca_order=next(order_counter), ca_missing=colander.null,
        cascade="all, delete-orphan", ca_widget=deform.widget.HiddenWidget(), ca_exclude=True)

    touched_pages = relationship("UntouchedPages", uselist=False, ca_order=next(order_counter),
        cascade="all, delete-orphan", ca_exclude=True)



class CreatePage(colander.MappingSchema):
    """
    The create project wizard collects the minimum required data and pre-fills as many fields as possible from the
    chosen template and grant.

    This is a direct Deform schema, not a ColanderAlchemy schema wich is assocated with an SQLalchemy database table.
    """
    use_template = colander.SchemaNode(colander.Boolean(), help="",
        title="Use a project template (only select if your project is similar to a previous one)", default=False,
        widget=deform.widget.CheckboxWidget(template="checked_conditional_input", inverted=True))

    template = colander.SchemaNode(colander.Integer(), title="Select a Project Template",
        missing=colander.null, required=False,
        widget=deform.widget.TextInputWidget(template="project_template_mapping"),
        help="<p>Templates pre-fill the project with as much information as possible to make this process as quick and easy as possible.</p><ul><li>If you don't want to use any template, select the general category and Blank template.</li><li>Please contact the administrators to request new templates.</li>",
        description="<ol><li>First select the category or organisational group on the left hand side.</li><li>Then select the most relevant template from the list on the right hand side.</li>")

    no_activity = colander.SchemaNode(colander.Boolean(), help="Must be un-selected if a research grant isn't provided below.",
        title="There is an associated research grant", default=True, widget=deform.widget.CheckboxWidget(template="checked_conditional_input", inverted=True))

    grant = colander.SchemaNode(colander.String(), title="Research Grant",
        missing=colander.null, required=False,
        help="Enter title of the research grant associated with this record (Autocomplete).  The grant will be looked up for additional information that can be pre-filled.",
        description="Un-Select 'There is an associated research grant' above if your project isn't associated with a research grant.",
        widget=search_activities_widget)

    #    services = Column(String(256), ca_title="Services - Remove this?", ca_order=next(order_counter), ca_placeholder="Autocomplete - Mint/Mint DB", ca_page="general",
    #            ca_help="Indicate any related Services to this Collection. A lookup works against Mint, or you can enter known information about remote Services."
    #            , ca_missing="",
    #            ca_group_end="associations")


    data_manager = colander.SchemaNode(colander.String(), title="Data Manager (Primary contact)",
        widget=search_parties_widget,
        help="Primary contact for the project, this should be the person in charge of the data and actively working on the project.<br /><br />"\
                "<i>Autocomplete from most universities and large organisations, if the person you are trying to select isn't available please organise an external JCU account for them.</i>")
    project_lead = colander.SchemaNode(colander.String(), title="Project Lead (Supervisor)",
        widget=search_parties_widget,
        help="Head supervisor of the project that should be contacted when the data manager is unavailable.<br /><br />"\
                "<i>Autocomplete from most universities and large organisations, if the person you are trying to select isn't available please organise an external JCU account for them.</i>")


method_template = colander.SchemaNode(colander.Integer, title="Select a template to base this method off",
    widget=deform.widget.TextInputWidget(template="project_template_mapping"),
    help="<p>Method templates provide pre-configured data collection methods and pre-fill as much information as possible to make this process as quick and easy as possible.</p>"
            "<ul><li>If you don't want to use any template, select the general category and Blank template."
            "</li><li>Please contact the administrators to request new templates.</li>",
    description="<ol><li>First select the category or organisational group on the left hand side.</li>"
                   "<li>Then select the most relevant template from the list on the right hand side.</li>")


########################################################################################################################
########################################### MODELS FOR CONTEXTUAL OPTIONS ##############################################
########################################################################################################################

class DataEntry(CAModel, Base):
    """
    NOT YET IMPLEMENTED

    Represents a point of data in the ingester platform displayed using a Deform schema dynamically generated from the
    methods data configuration (data schema).
    """
    order_counter = itertools.count()

    __tablename__ = 'data_entry'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    dam_id = Column(Integer, nullable=True, ca_widget=deform.widget.HiddenWidget())
    dam_version = Column(String(128), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'), nullable=True, ca_widget=deform.widget.HiddenWidget())

class DataCalibration(CAModel, Base):
    """
    NOT YET IMPLEMENTED

    Represents a point of data in the ingester platform displayed using a Deform schema dynamically generated from the
    methods data configuration (data schema).
    """
    order_counter = itertools.count()

    __tablename__ = 'data_calibration'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    dam_id = Column(Integer, nullable=True, ca_widget=deform.widget.HiddenWidget())
    dam_version = Column(String(128), ca_widget=deform.widget.HiddenWidget(),ca_order=next(order_counter))
    dataset_id = Column(Integer, ForeignKey('dataset.id'), nullable=True, ca_widget=deform.widget.HiddenWidget())



class IngesterLogsFiltering(colander.MappingSchema):
    """
    Provides filtering of ingester platform logs.  Filtering is based on:
    - level
    - start data
    - end date

    This is a direct Deform schema, not a ColanderAlchemy schema wich is assocated with an SQLalchemy database table.
    """

    log_levels=(("ALL","Show All"),
                ("ERROR","Errors"),
                ("INFO", "Informational"),
                #                ("WARNING", "Warnings"),
                #                ("DEBUG", "Debugging"),
        )
    start_date = colander.SchemaNode(colander.Date(), missing=colander.null, widget=deform.widget.DateInputWidget())
    end_date = colander.SchemaNode(colander.Date(), missing=colander.null, widget=deform.widget.DateInputWidget())
    level = colander.SchemaNode(colander.String(),widget=deform.widget.SelectWidget(values=log_levels,
        multiple=False),missing=colander.null)

class IngesterLogs(colander.MappingSchema):
    """
    Ingester logs provide feedback on the state of data ingestion and are looked up through the ingesterapi

    This is a direct Deform schema, not a ColanderAlchemy schema wich is assocated with an SQLalchemy database table.
    """
    filtering = IngesterLogsFiltering(widget=deform.widget.MappingWidget(template="inline_mapping", readonly_template="readonly/inline_mapping", show_label=True),
        title="Filter Logs",
        help='Filter the ingester event logs based on level (multple seletion) as well as date start, end or range.',
        missing=colander.null)
    logs = colander.SchemaNode(colander.String(), title="", widget=deform.widget.HiddenWidget(template="ingester_logs"),
        help="TODO: Provide information on what logs mean",missing=colander.null)


class SharedUser(colander.MappingSchema):
    """
    Provides an interface for editing user share permissions for the current project.

    This is a direct Deform schema, not a ColanderAlchemy schema wich is assocated with an SQLalchemy database table.
    """
    user_id = colander.SchemaNode(colander.Integer(),widget=deform.widget.HiddenWidget())
    view_permission = colander.SchemaNode(colander.Boolean(), name=DefaultPermissions.VIEW_PROJECT[0], default = True, title="View")
    edit_permission = colander.SchemaNode(colander.Boolean(), name=DefaultPermissions.EDIT_PROJECT[0],default = False, title="Edit")
    submit_permission = colander.SchemaNode(colander.Boolean(), name=DefaultPermissions.SUBMIT[0],default = False, title="Submit")
    disable_permission = colander.SchemaNode(colander.Boolean(), name=DefaultPermissions.DISABLE[0],default = False, title="Disable")
    enable_permission = colander.SchemaNode(colander.Boolean(), name=DefaultPermissions.ENABLE[0],default = False, title="Re-Enable")
    view_data_permission = colander.SchemaNode(colander.Boolean(), name=DefaultPermissions.EDIT_DATA[0],default = False, title="View Data")
    edit_data_permission = colander.SchemaNode(colander.Boolean(), name=DefaultPermissions.EDIT_DATA[0],default = False, title="Manage Data")
    edit_ingester_permission = colander.SchemaNode(colander.Boolean(), name=DefaultPermissions.EDIT_INGESTERS[0],default = False, title="Manage Ingesters")

class SharedUsers(colander.SequenceSchema):
    """
    Converts the SharedUser into a sequence/list.

    This is a direct Deform schema, not a ColanderAlchemy schema wich is assocated with an SQLalchemy database table.
    """
    user = SharedUser(widget=deform.widget.MappingWidget(template="inline_mapping", readonly_template="readonly/inline_mapping", show_label=True))
#
#@colander.deferred
#def get_users(node, kw):
#    return kw['users']

class Sharing(colander.MappingSchema):
    """
    Page that displays the list of shared user permissions.

    This is a direct Deform schema, not a ColanderAlchemy schema wich is assocated with an SQLalchemy database table.
    """
    shared_with = SharedUsers(title="Users Who This Project Is Shared With",
        widget=deform.widget.SequenceWidget(template="sharing_sequence"),
    )


class NotificationConfig(CAModel, Base):
    """
    """
    order_counter = itertools.count()

    __tablename__ = 'notification_config'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())

    state_changes = Column(Boolean(), ca_order=next(order_counter), ca_title="State Changes (eg. submitted)")
    ingester_changes = Column(Boolean(), ca_order=next(order_counter), ca_title="Dataset/Ingester changes")
    permission_changes = Column(Boolean(), ca_order=next(order_counter))
    log_errors = Column(Boolean(), ca_order=next(order_counter))
    log_warnings = Column(Boolean(), ca_order=next(order_counter))
    new_projects = Column(Boolean(), ca_order=next(order_counter), ca_widget=deform.widget.CheckboxWidget(),)

class ProjectNotificationConfig(CAModel, Base):
    """
    """
    order_counter = itertools.count()

    __tablename__ = 'project_notification_config'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'), nullable=True, ca_widget=deform.widget.HiddenWidget())
    user_notification_config_id = Column(Integer, ForeignKey('user_notification_config.id'), nullable=True,
        ca_widget=deform.widget.HiddenWidget())

    notification_config_id = Column(Integer, ForeignKey('notification_config.id'), nullable=True,
        ca_widget=deform.widget.HiddenWidget())

    notification_config = relationship('NotificationConfig', single_parent=True, uselist=False, ca_order=next(order_counter),
        cascade="all, delete-orphan", ca_title="Project Notification Settings",
        ca_widget=deform.widget.MappingWidget(template="inline_mapping", readonly_template="readonly/inline_mapping"))

class UserNotificationConfig(CAModel, Base):
    """
    """
    order_counter = itertools.count()

    __tablename__ = 'user_notification_config'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True, ca_widget=deform.widget.HiddenWidget())
    default_notification_config_id = Column(Integer, ForeignKey('notification_config.id'), nullable=True,
        ca_widget=deform.widget.HiddenWidget())

    default_notification_config = relationship('NotificationConfig', ca_title="Default Notification Settings",
        ca_help="These settings will be applied to new projects you create as well as projects that other users share with you.",
        single_parent=True, uselist=False, ca_order=next(order_counter),
        cascade="all, delete-orphan",
        ca_widget=deform.widget.MappingWidget(template="inline_mapping", readonly_template="readonly/inline_mapping", show_label=True))
    notification_configs = relationship('ProjectNotificationConfig', ca_title="Notification Settings", ca_order=next(order_counter),
        ca_help="You can configure what email notifications you will receive for each project you have created, had shared with you or added notifications on.",
        cascade="all, delete-orphan", ca_child_title="notification settings for the current project",
        ca_child_widget=deform.widget.MappingWidget(template="notifications_mapping", readonly_template="readonly/notifications_mapping"))

class ManageData(colander.MappingSchema):
    """
    NOT IMMPLEMENTED YET
    Simple Deform schema to base data mangement from, it is anticipated that a more models will be needed for data
    management and some may need to be dynamically created in the view.

    This is a direct Deform schema, not a ColanderAlchemy schema wich is assocated with an SQLalchemy database table.
    """
    user_id = colander.SchemaNode(colander.Integer())

class DataFiltering(colander.MappingSchema):
    """
    Schema for the browse projects/data page - the below fields provide the filtering and this schema should be used
    with the template set to manage_date.
    """
    type = colander.SchemaNode(colander.String(), widget=deform.widget.SelectWidget(css_class="data_filter",
        values=(("project", "Projects"), ("dataset","Datasets"), ("data","Data"),),
        ca_help="Only show the selected types of data"),
        help="Only projects in the selectedstates will be searched.",missing=colander.null)
    id_list = colander.SchemaNode(colander.String(), missing=colander.null, title="ID List",
        help="Comma separated list of unique identifiers, the unique identifier format is &lt;type&gt;_&lt;id&gt;",
        placeholder="eg. project_1, project 2", widget=deform.widget.TextInputWidget(css_class="id_list"))
    search_string = colander.SchemaNode(colander.String(), missing=colander.null,
        widget=deform.widget.TextInputWidget(css_class="search_string"))

    state = colander.SchemaNode(colander.Set(), widget=deform.widget.CheckboxChoiceWidget(css_class="states",
        values=((ProjectStates.OPEN, "Open"), (ProjectStates.SUBMITTED,"Submitted"), (ProjectStates.ACTIVE, "Active"),
                (ProjectStates.DISABLED, "Disabled"), )),
        help="Only projects in the selectedstates will be searched.",missing=colander.null)

    start_date = colander.SchemaNode(colander.Date(), widget=deform.widget.DateInputWidget(css_class="data_filter"),
        help="Only results created afterthe entered date will be shown.",missing=colander.null)
    end_date = colander.SchemaNode(colander.Date(), widget=deform.widget.DateInputWidget(css_class="data_filter"),
        help="Only results created beforethe entered date will be shown.", missing=colander.null)


class DataFilteringWrapper(colander.MappingSchema):
    """
    This class is to get around the first element in a form having its templates ignored as they are replaced with the
    form template....
    """
    data_filtering = DataFiltering(widget=deform.widget.MappingWidget(template="manage_data"),)
