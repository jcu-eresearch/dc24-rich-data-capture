import colander
import deform
from views.schemas.dataset_schema import CoverageSchema
from views.workflow.workflows import MemoryTmpStore

__author__ = 'Casey Bajema'

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
        exc = colander.Invalid(form, 'At least 1 research theme or Not aligned needs to be selected')
        exc['ecosystems_conservation_climate'] = 'At least 1 research theme needs to be selected'
        exc['industries_economies'] = 'At least 1 research theme needs to be selected'
        exc['peoples_societies'] = 'At least 1 research theme needs to be selected'
        exc['health_medicine_biosecurity'] = 'At least 1 research theme needs to be selected'
        exc['not_aligned'] = 'Select this if the none above are applicable'
        raise exc

class Person(colander.MappingSchema):
    title = colander.SchemaNode(colander.String(), title="Title")
    givenName = colander.SchemaNode(colander.String(), title="Given name")
    familyName = colander.SchemaNode(colander.String(), title="Family name")
    email = colander.SchemaNode(colander.String(), title="Email", missing="")

class Party(colander.MappingSchema):
    relationshipTypes = (
        ("owner", "Owned by"), ("manager", "Managed by"), ("associated", "Associated with"),
        ("aggregated", "Aggregated by")
        , ("enriched", "Enriched by"))
    relationship = colander.SchemaNode(colander.String(), title="This project is",
        widget=deform.widget.SelectWidget(values=relationshipTypes),
        validator=colander.OneOf(
            [relationshipTypes[0][0], relationshipTypes[1][0], relationshipTypes[2][0], relationshipTypes[3][0],
             relationshipTypes[4][0]]))
    person = Person(title="")


class PartySchema(colander.SequenceSchema):
    party = Party(title="Person")

class People(colander.SequenceSchema):
    person = Person()

class WebResource(colander.MappingSchema):
    url = colander.SchemaNode(colander.String(), title="URL")
    title = colander.SchemaNode(colander.String(), title="Title")
    notes = colander.SchemaNode(colander.String(), title="Notes")

class PublicationSchema(colander.SequenceSchema):
    publication = WebResource()

class WebsiteSchema(colander.SequenceSchema):
    website = WebResource()

class KeywordsSchema(colander.SequenceSchema):
    keyword = colander.SchemaNode(colander.String())

class CollaboratorSchema(colander.SequenceSchema): collaborator = colander.SchemaNode(colander.String(),
    title="Collaborator")

class Associations(colander.MappingSchema):
    parties = PartySchema(title="People", widget=deform.widget.SequenceWidget(min_len=1))
    collaborators = CollaboratorSchema()
    relatedPublications = PublicationSchema(title="Related Publications")
    relatedWebsites = WebsiteSchema(title="Related Websites")
    activities = colander.SchemaNode(colander.String(), title="Grants")
    services = colander.SchemaNode(colander.String(), default="Autocomplete - Mint/Mint DB")

class CitationDate(colander.MappingSchema):
    dateType = colander.SchemaNode(colander.String(), title="Date type")
    archivalDate = colander.SchemaNode(colander.Date(), title="")

class CitationDates(colander.SequenceSchema):
    date = CitationDate()

class Citation(colander.MappingSchema):
    title = colander.SchemaNode(colander.String())
    creators = People()
    edition = colander.SchemaNode(colander.String())
    publisher = colander.SchemaNode(colander.String())
    placeOfPublication = colander.SchemaNode(colander.String(), title="Place of publication")
    dates = CitationDates(title="Date(s)")
    url = colander.SchemaNode(colander.String(), title="URL")
    context = colander.SchemaNode(colander.String())

researchTypes = (
    ('select', 'Please select one...'), ('applied', 'Applied research'), ('experimental', 'Experimental development'),
    ('pure_basic', 'Pure basic research'), ('pure_strategic', 'Strategic basic research'))


class Subject(colander.MappingSchema):
    keywords = KeywordsSchema()

    typeOfResearch = colander.SchemaNode(colander.String(), widget=deform.widget.SelectWidget(values=researchTypes),
        validator=colander.OneOf(
            [researchTypes[0][0], researchTypes[1][0], researchTypes[2][0], researchTypes[3][0], researchTypes[4][0]]),
        title="Type of Research Activity")

    researchThemes = ResearchTheme(title="Research Themes", validator=research_theme_validator,
        description="Select one or more of the 4 themes, or 'not aligned'.", required=True)

    fieldOfResearch = colander.SchemaNode(colander.String(), title="Fields of Research",
        default="To be redeveloped similar to ReDBox")

    socioEconomicObjective = colander.SchemaNode(colander.String(), title="Socio-Economic Objectives",
        default="To be redeveloped similar to ReDBox")


class Legality(colander.MappingSchema):
    class AccessRights(colander.Schema):
        accessRights = colander.SchemaNode(colander.String(), title="Access Rights", default="Open access",
            missing="Open access")
        accessRightsURL = colander.SchemaNode(colander.String(), title="URL", missing="")

    class UsageRights(colander.Schema):
        rights = colander.SchemaNode(colander.String(), default="Public under ???", missing="Public under ???")
        rightsURL = colander.SchemaNode(colander.String(), title="URL", missing="")

    class OtherLicense(colander.MappingSchema):
        name = colander.SchemaNode(colander.String(), title="License Name", default="", missing="")
        url = colander.SchemaNode(colander.String(), title="License URL", default="", missing="")

    #    TODO: Link to external sources
    choices = (
        ('none', 'No License'),
        ('creative_commons_by', 'Creative Commons - Attribution alone (by)'),
        ('creative_commons_bync', 'Creative Commons - Attribution + Noncommercial (by-nc)'),
        ('creative_commons_bynd', 'Creative Commons - Attribution + NoDerivatives (by-nd)'),
        ('creative_commons_bysa', 'Creative Commons - Attribution + ShareAlike (by-sa)'),
        ('creative_commons_byncnd', 'Creative Commons - Attribution + Noncommercial + NoDerivatives (by-nc-nd)'),
        ('creative_commons_byncsa', 'Creative Commons - Attribution + Noncommercial + ShareAlike (by-nc-sa)'),
        ('restricted_license', 'Restricted License'),
        )

    accessRights = AccessRights(title="Access Rights",
        description="Information about access to the collection or service, including access restrictions or embargoes based on privacy, security or other policies. A URI is optional.  "\
                    "eg. Contact Chief Investigator to negotiate access to the data. "\
                    "eg. Embargoed until 1 year after publication of the research.")
    rights = UsageRights(title="Usage Rights",
        description="Information about rights held in and over the collection such as copyright, licences and other intellectual property rights, eg. This dataset is made available under the Public Domain Dedication and License v1.0 whose full text can be found at: http://www.opendatacommons.org/licences/pddl/1.0/"\
                    "A URI is optional. ")

    license = colander.SchemaNode(colander.String(), title="License", default="creative_commons_by",
        widget=deform.widget.SelectWidget(values=choices))
    other = OtherLicense(title="Other")
    otherLegalRights = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget(),
        title="Other Legal Rights")

class Notes(colander.SequenceSchema):
    note = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget())

class Attachment(colander.MappingSchema):
    attachmentTypes = (("data", "Data file"), ("supporting", "Supporting material"), ("readme", "Readme"))
    type = colander.SchemaNode(colander.String(), widget=deform.widget.SelectWidget(values=attachmentTypes),
        validator=colander.OneOf(
            [attachmentTypes[0][0], attachmentTypes[1][0], attachmentTypes[2][0]]),
        title="Attachment type", css_class="inline")
    attachment = MemoryTmpStore()
    attachFile = colander.SchemaNode(deform.FileData(), widget=deform.widget.FileUploadWidget(attachment),
        title="Attach File", missing=attachment, css_class="inline")

class Attachments(colander.SequenceSchema):
    attachment = Attachment(widget=deform.widget.MappingWidget(template="inline_mapping"))

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
#    grantNumber = colander.SchemaNode(colander.String(), default="linked", title="Grant Number")
#    dataAffiliation = colander.SchemaNode(colander.String(), title="Data Affiliation")


class MetadataData(colander.MappingSchema):
    subject = Subject()
    coverage = CoverageSchema()
    associations = Associations()
    legal = Legality(title="Legality")
    citation = Citation()
    attachments = Attachments()
    retentionPeriods = (
        ("indefinite", "Indefinite"), ("1", "1 Year"), ("5", "5 Years"), ("7", "7 Years"), ("10", "10 Years"),
        ("15", "15 Years"))
    retentionPeriod = colander.SchemaNode(colander.String(), title="Retention period",
        widget=deform.widget.SelectWidget(values=retentionPeriods),
        validator=colander.OneOf(
            [retentionPeriods[0][0], retentionPeriods[1][0], retentionPeriods[2][0], retentionPeriods[3][0],
             retentionPeriods[4][0], retentionPeriods[5][0]]))
    nationalSignificance = colander.SchemaNode(colander.Boolean(), title="Is the data nationally significant?",
        widget=deform.widget.RadioChoiceWidget(values=(("yes", "Yes"), ("no", "No"))))
    notes = Notes()