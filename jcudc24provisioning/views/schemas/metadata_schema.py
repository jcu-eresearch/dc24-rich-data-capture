import ConfigParser
from collections import OrderedDict
import json
import logging
import urllib2
from beaker.cache import cache_region
import os
import colander
import deform
from jcudc24provisioning.views.schemas.common_schemas import Person, WebsiteSchema, People, Notes, Attachment, OneOfDict
from jcudc24provisioning.views.schemas.dataset_schema import CoverageSchema
from jcudc24provisioning.views.schemas.widgets import SelectWithOtherWidget

__author__ = 'Casey Bajema'
logger = logging.getLogger("jcu.dc24.provisioning.views.schemas")

class ResearchTheme(colander.MappingSchema):
    ecosystems_conservation_climate = colander.SchemaNode(colander.Boolean(), widget=deform.widget.CheckboxWidget(),
        title='Tropical Ecosystems, Conservation and Climate Change')
    industries_economies = colander.SchemaNode(colander.Boolean(), widget=deform.widget.CheckboxWidget(),
        title='Industries and Economies in the Tropics')
    peoples_societies = colander.SchemaNode(colander.Boolean(), widget=deform.widget.CheckboxWidget(),
        title='Peoples and Societies in the Tropics')
    health_medicine_biosecurity = colander.SchemaNode(colander.Boolean(), widget=deform.widget.CheckboxWidget(),
        title='Tropical Health, Medicine and Biosecurity')
    not_aligned = colander.SchemaNode(colander.Boolean(), widget=deform.widget.CheckboxWidget(),
        title='Not aligned to a University theme')


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


@cache_region('long_term')
def getFORCodes():
    FOR_CODES_FILE = "for_codes.csv"

    for_codes_file = open(FOR_CODES_FILE).read()
    data = OrderedDict()
    data['---Select One---'] = dict()

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
            data[item1]['---Select One---'] = dict()

    return data


@cache_region('long_term')
def getSEOCodes():
    SEO_CODES_FILE = "seo_codes.csv"

    seo_codes_file = open(SEO_CODES_FILE).read()
    data = OrderedDict()
    data['---Select One---'] = dict()

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
            data[item1]['---Select One---'] = dict()

    return data


class FieldOfResearchSchema(colander.SequenceSchema):
    field_of_research = colander.SchemaNode(colander.String(), title="Field Of Research")
    field_of_research.data = getFORCodes()


class SocioEconomicObjectives(colander.SequenceSchema):
    socio_economic_objective = colander.SchemaNode(colander.String(), title="Socio-Economic Objective")
    socio_economic_objective.data = getSEOCodes()


class Party(colander.MappingSchema):
    relationship_types = (
        (None, "---Select One---"), ("owner", "Owned by"), ("manager", "Managed by"), ("associated", "Associated with"),
        ("aggregated", "Aggregated by")
        , ("enriched", "Enriched by"))
    relationship = colander.SchemaNode(colander.String(), title="This project is",
        widget=deform.widget.SelectWidget(values=relationship_types),
        validator=OneOfDict(relationship_types[1:]))
    person = Person(title="")


class PartySchema(colander.SequenceSchema):
    party = Party(title="Person")


class KeywordsSchema(colander.SequenceSchema):
    keyword = colander.SchemaNode(colander.String())


class CollaboratorSchema(colander.SequenceSchema):
    collaborator = colander.SchemaNode(colander.String(), title="Collaborator",
        placeholder="eg. CSIRO, University of X, Prof. Jim Bloggs, etc.")


class Associations(colander.MappingSchema):
    parties = PartySchema(title="People", widget=deform.widget.SequenceWidget(min_len=1), missing="",
        description="Enter the details of associated people as described by the dropdown box.")
    collaborators = CollaboratorSchema(
        description="Names of other collaborators in the research project where applicable, this may be a person or organisation/group of some type."
        , missing="")
    related_publications = WebsiteSchema(title="Related Publications",
        description="Include URL/s to any publications underpinning the research dataset/collection, registry/repository, catalogue or index.")
    related_websites = WebsiteSchema(title="Related Websites", description="Include URL/s for the relevant website.")
    activities = colander.SchemaNode(colander.String(), title="Grants (Activity)",
        description="Enter details of which activities are associated with this record.", missing="",
        placeholder="TODO: Autocomplete from Mint/Mint DB")
    services = colander.SchemaNode(colander.String(), placeholder="Autocomplete - Mint/Mint DB",
        description="Indicate any related Services to this Collection. A lookup works against Mint, or you can enter known information about remote Services."
        , missing="")


class CitationDate(colander.MappingSchema):
    dateType = colander.SchemaNode(colander.String(), title="Date type",
        widget=deform.widget.TextInputWidget(size="40", css_class="full_width"))
    archivalDate = colander.SchemaNode(colander.Date(), title="Date")


class CitationDates(colander.SequenceSchema):
    date = CitationDate(widget=deform.widget.MappingWidget(template="inline_mapping"))


class Citation(colander.MappingSchema):
    title = colander.SchemaNode(colander.String(), placeholder="Mr, Mrs, Dr etc.", missing="")
    creators = People(missing=None)
    edition = colander.SchemaNode(colander.String(), missing="")
    publisher = colander.SchemaNode(colander.String())
    place_of_publication = colander.SchemaNode(colander.String(), title="Place of publication")
    dates = CitationDates(title="Date(s)")
    url = colander.SchemaNode(colander.String(), title="URL")
    context = colander.SchemaNode(colander.String(), placeholder="citation context", missing="")

researchTypes = (
    ('select', 'Please select one...'), ('applied', 'Applied research'), ('experimental', 'Experimental development'),
    ('pure_basic', 'Pure basic research'), ('pure_strategic', 'Strategic basic research'))


class Subject(colander.MappingSchema):
    keywords = KeywordsSchema(
        description="Enter keywords that users are likely to search on when looking for this projects data.")

    fieldOfResearch = FieldOfResearchSchema(title="Fields of Research",
        widget=deform.widget.SequenceWidget(template='multi_select_sequence'),
        description="Select or enter Fields of Research (FoR) from the drop-down menus, and click the 'Add Field Of Research' button - which is hidden until a code is selected)."
        ,
        missing="")
    #    colander.SchemaNode(colander.String(), title="Fields of Research",
    #        placeholder="To be redeveloped similar to ReDBox", description="Select relevant FOR code/s. ")

    socioEconomicObjective = SocioEconomicObjectives(title="Socio-Economic Objectives",
        widget=deform.widget.SequenceWidget(template='multi_select_sequence'),
        description="Select relevant SEO code/s.", missing="")

    researchThemes = ResearchTheme(title="Research Themes", validator=research_theme_validator,
        description="Select one or more of the 4 themes, or \'Not aligned to a University theme\'.", required=True)

    typeOfResearch = colander.SchemaNode(colander.String(), widget=deform.widget.SelectWidget(values=researchTypes),
        validator=OneOfDict(researchTypes[1:]),
        title="Type of Research Activity",
        description="1297.0 Australian Standard Research Classification (ANZSRC) 2008. </br></br>"\
                    "<b>Pure basic research</b> is experimental and theoretical work undertaken to acquire new knowledge without looking for long term benefits other than the advancement of knowledge.</br></br>"\
                    "<b>Strategic basic research</b> is experimental and theoretical work undertaken to acquire new knowledge directed into specified broad areas in the expectation of useful discoveries. It provides the broad base of knowledge necessary for the solution of recognised practical problems.</br></br>"\
                    "<b>Applied research</b> is original work undertaken primarily to acquire new knowledge with a specific application in view. It is undertaken either to determine possible uses for the findings of basic research or to determine new ways of achieving some specific and predetermined objectives.</br></br>"\
                    "<b>Experimental development</b> is systematic work, using existing knowledge gained from research or practical experience, that is directed to producing new materials, products or devices, to installing new processes, systems and services, or to improving substantially those already produced or installed."
    )


class Legality(colander.MappingSchema):
    class AccessRights(colander.Schema):
        access_rights = colander.SchemaNode(colander.String(), title="Access Rights", default="Open access")
        access_rights_url = colander.SchemaNode(colander.String(), title="URL", missing="")

    class UsageRights(colander.Schema):
        rights = colander.SchemaNode(colander.String(), placeholder="TODO: replaced with default license", missing="")
        rights_url = colander.SchemaNode(colander.String(), title="URL", missing="")

    class OtherLicense(colander.MappingSchema):
        name = colander.SchemaNode(colander.String(), title="License Name", placeholder="", missing="")
        url = colander.SchemaNode(colander.String(), title="License URL", placeholder="", missing="")

    access_rights = AccessRights(title="Access Rights",
        description="Information about access to the collection or service, including access restrictions or embargoes based on privacy, security or other policies. A URI is optional.</br></br>"\
                    "eg. Contact Chief Investigator to negotiate access to the data.</br></br>"\
                    "eg. Embargoed until 1 year after publication of the research.")
    rights = UsageRights(title="Usage Rights",
        description="Information about rights held in and over the collection such as copyright, licences and other intellectual property rights, eg. This dataset is made available under the Public Domain Dedication and License v1.0 whose full text can be found at: <b>http://www.opendatacommons.org/licences/pddl/1.0/</b></br>"\
                    "A URI is optional. ")
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

    license = colander.SchemaNode(colander.String(), title="License", placeholder="creative_commons_by",
        default="creative_commons_by",
        widget=deform.widget.SelectWidget(values=licenses, template="select_with_other"),
        description="This list contains data licences that this server has been configured with. For more information about Creative Commons licences please <a href=\'http://creativecommons.org.au/learn-more/licences\' alt=\'licenses\'>see here</a>. ")

    other = OtherLicense(title="Other",
            description="If you want to use a license not included in the above list you can provide details below.</br></br>"\
                        "<ul><li>If you are using this field frequently for the same license it would make sense to get your system administrator to add the license to the field above.</li>"\
                        "<li>If you provide two licenses (one from above, plus this one) only the first will be sent to RDA in the RIF-CS.</li>"\
                        "<li>Example of another license: http://www.opendefinition.org/licenses</li></ul>")


#class DataDetails(colander.MappingSchema):
#    dataOwner = colander.SchemaNode(colander.String(), title="Data Owner (IP)")
#    dataCustodian = colander.SchemaNode(colander.String(), title="Data Custodian", missing="")

#    disposalDate = colander.SchemaNode(colander.Date(), title="Disposal Date", widget=deform.widget.DateInputWidget(),
#        description='Date that the data should be deleted', missing="")
#    archivalDate = colander.SchemaNode(colander.Date(), title="Archival Date",
#        description='Date that the data should be deleted', missing="")
#    depositor = colander.SchemaNode(colander.String())
#    institutionalDataManagementPolicy = colander.SchemaNode(colander.String(),
#        title="Institutional Data Management Policy")
#    fundingBody = colander.SchemaNode(colander.String(), title="Funding Body")
#    grantNumber = colander.SchemaNode(colander.String(), placeholder="linked", title="Grant Number")
#    dataAffiliation = colander.SchemaNode(colander.String(), title="Data Affiliation")


class MetadataAttachment(colander.MappingSchema):
    attachment_types = (("data", "Data file"), ("supporting", "Supporting material"), ("readme", "Readme"))
    type = colander.SchemaNode(colander.String(), widget=deform.widget.SelectWidget(values=attachment_types),
        validator=colander.OneOf(
            [attachment_types[0][0], attachment_types[1][0], attachment_types[2][0]]),
        title="Attachment type", css_class="inline")
    attachment = Attachment()


class MetadataAttachments(colander.SequenceSchema):
    attachment = MetadataAttachment(widget=deform.widget.MappingWidget(template="inline_mapping"), missing=None)


class MintPerson(colander.MappingSchema):
    mint = colander.SchemaNode(colander.String(),
        widget=deform.widget.AutocompleteInputWidget(size=60, min_length=1, template="mint_users_autocomplete"))

    non_mint = Person()


class MetadataData(colander.MappingSchema):
#    test = MintPerson()

    subject = Subject()
    coverage = CoverageSchema()
    associations = Associations()
    legal = Legality(title="Legality")
    citation = Citation(
        description="Provide metadata that should be used for the purposes of citing this record. Sending a citation to RDA is optional, but if you choose to enable this there are quite specific mandatory fields that will be required by RIF-CS.")
    attachments = MetadataAttachments(missing=None)
    retention_periods = (
        ("indefinite", "Indefinite"), ("1", "1 Year"), ("5", "5 Years"), ("7", "7 Years"), ("10", "10 Years"),
        ("15", "15 Years"))
    retention_period = colander.SchemaNode(colander.String(), title="Retention period",
        widget=deform.widget.SelectWidget(values=retention_periods),
        description="Record the period of time that the data must be kept in line with institutional/funding body retention policies.")
    national_significance = colander.SchemaNode(colander.Boolean(), title="Is the data nationally significant?",
        widget=deform.widget.RadioChoiceWidget(values=(("true", "Yes"), ("false", "No"))),
        description="Do you know or believe that this projects data may be Nationally Significant?")
    notes = Notes(description="Enter administrative notes as required.", missing=None)