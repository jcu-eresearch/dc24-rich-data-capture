import json
import colander
from lxml import etree
from sqlalchemy import Column
from jcudc24provisioning.models.ca_model import CAModel
from jcudc24provisioning.models.project import Metadata, Party, Keyword, Collaborator, MetadataNote, CitationDate, Attachment, RelatedPublication, RelatedWebsite, FieldOfResearch, SocioEconomicObjective, Location, Creator
from jcudc24provisioning.views.ca_scripts import fix_schema_field_name

__author__ = 'Casey Bajema'

def create_json_config():
    dict_config = {
        "comment": "This James Cook University's XML mapping is generated from the DC24 RichDataCapture provisioning interface.  It is generated on startup to create a ReDBox json configuration file that matches the models XML conversion.",
        "mappings": {
            "/%s" % Metadata.redbox_identifier.key: "",
            "/%s" % Metadata.ccdam_identifier.key: "",
            "/%s" % Metadata.project_title.key: "",
            "/%s" % Metadata.activity.key: "",
            "/%s" % Metadata.parties.key: {
                Party.party_relationship.key: "",
                Party.identifier.key: "",
            },
            "/%s" % Metadata.collaborators.key: {
                Metadata.collaborators.key: "",
            },
            "/%s" % Metadata.brief_description.key: "",
            "/%s" % Metadata.full_description.key: "",
            "/%s" % Metadata.notes.key: {
                Metadata.notes.key: "",
            },
            "/%s" % Metadata.keywords.key: {
                Keyword.keyword.key: "",
            },
            "/%s" % Metadata.fieldOfResearch.key: {
                FieldOfResearch.field_of_research.key: "",
            },
            "/%s" % Metadata.socioEconomicObjective.key: {
                SocioEconomicObjective.socio_economic_objective.key: "",
            },
            "/%s" % Metadata.ecosystems_conservation_climate.key: "",
            "/%s" % Metadata.industries_economies.key: "",
            "/%s" % Metadata.peoples_societies.key: "",
            "/%s" % Metadata.health_medicine_biosecurity.key: "",
            "/%s" % Metadata.typeOfResearch.key: "",
            "/%s" % Metadata.time_period_description.key: "",
            "/%s" % Metadata.date_from.key: "",
            "/%s" % Metadata.date_to.key: "",
            "/%s" % Metadata.location_description.key: "",
            "/%s" % Metadata.locations.key: {
                Location.name.key: "",
                Location.location.key: "",
                Location.elevation.key: "",
            },
            "/%s" % Metadata.access_rights.key: "",
            "/%s" % Metadata.access_rights_url.key: "",
            "/%s" % Metadata.rights.key: "",
            "/%s" % Metadata.rights_url.key: "",
            "/%s" % Metadata.license.key: "",
            "/%s" % Metadata.license_name.key: "",
            "/%s" % Metadata.license_url.key: "",
            "/%s" % Metadata.citation_title.key: "",
            "/%s" % Metadata.citation_creators.key: {
                Creator.title.key: "",
                Creator.given_name.key: "",
                Creator.family_name.key: "",
                Creator.email.key: "",

            },
            "/%s" % Metadata.citation_edition.key: "",
            "/%s" % Metadata.citation_publisher.key: "",
            "/%s" % Metadata.citation_place_of_publication.key: "",
            "/%s" % Metadata.citation_dates.key: {
                CitationDate.dateType.key: "",
                CitationDate.archivalDate.key: "",
            },
            "/%s" % Metadata.citation_url.key: "",
            "/%s" % Metadata.citation_context.key: "",
            "/%s" % Metadata.retention_period.key: "",
            "/%s" % Metadata.related_publications.key: {
                RelatedPublication.title.key: "",
                RelatedPublication.url.key: "",
                RelatedPublication.notes.key: "",
            },
            "/%s" % Metadata.related_websites.key: {
                RelatedWebsite.title.key: "",
                RelatedWebsite.url.key: "",
                RelatedWebsite.notes.key: "",

            },
            "/%s" % Metadata.attachments.key: {
                Attachment.type.key: "",
                Attachment.attachment.key: "",
                Attachment.note.key: "",

            }
        }, "exceptions": {},
        "defaultNamespace": {}
    }

    json_config = json.dumps(dict_config)
    print json.dumps(dict_config, sort_keys=True, indent=4, separators=(',', ': '))
    return json_config



#    redbox_identifier = etree.SubElement(xml_record, "redbox_identifier")
#    redbox_identifier.text = metadata_record.redbox_identifier
#
#    data_address = etree.SubElement(xml_record, "")
#    data_address.text = ""
#
#    project_title = etree.SubElement(xml_record, "")
#    project_title.text = ""
#
#
#    parties = etree.SubElement(xml_record, "")
#    for model_party in metadata_record.parties:
#        party = etree.SubElement(parties, "")
#        party.text = ""
#
#    collaborators = etree.SubElement(xml_record, "")
#    for model_collaborator in metadata_record.collaborators:
#        collaborator = etree.SubElement(collaborators, "")
#        collaborator.text = ""
#
#
#    brief_description = etree.SubElement(xml_record, "")
#    brief_description.text = ""
#
#    full_description = etree.SubElement(xml_record, "")
#    full_description.text = ""
#
#    notes = etree.SubElement(xml_record, "")
#    for model_note in metadata_record.notes:
#        note = etree.SubElement(xml_record, "")
#        note.text = ""
#
#    keywords = etree.SubElement(xml_record, "")
#    for model_keyword in metadata_record.keywords:
#        keyword = etree.SubElement(xml_record, "")
#        keyword.text = ""
#
#    fieldsOfResearch = etree.SubElement(xml_record, "")
#    for model_for in metadata_record.fieldOfResearch:
#        fieldOfResearch = etree.SubElement(xml_record, "")
#        fieldOfResearch.text = ""
#
#    socioEconomicObjectives = etree.SubElement(xml_record, "")
#    for model_seo in metadata_record.socioEconomicObjective:
#        socioEconomicObjective = etree.SubElement(xml_record, "")
#        socioEconomicObjective.text = ""
#
#    ecosystems_conservation_climate = etree.SubElement(xml_record, "")
#    ecosystems_conservation_climate.text = ""
#    industries_economies = etree.SubElement(xml_record, "")
#    industries_economies.text = ""
#    peoples_societies = etree.SubElement(xml_record, "")
#    peoples_societies.text = ""
#    health_medicine_biosecurity = etree.SubElement(xml_record, "")
#    health_medicine_biosecurity.text = ""
#
#    typeOfResearch = etree.SubElement(xml_record, "")
#    typeOfResearch.text = ""
#
#    time_period_description = etree.SubElement(xml_record, "")
#    time_period_description.text = ""
#    date_from = etree.SubElement(xml_record, "")
#    date_from.text = ""
#    date_to = etree.SubElement(xml_record, "")
#    date_to.text = ""
#
#    location_description = etree.SubElement(xml_record, "")
#    location_description.text = ""
#
#    locations = etree.SubElement(xml_record, "")
#    for model_location in metadata_record.locations:
#        location = etree.SubElement(xml_record, "")
#        location.text = ""
#
#    access_rights = etree.SubElement(xml_record, "")
#    access_rights.text = ""
#    access_rights_url = etree.SubElement(xml_record, "")
#    access_rights_url.text = ""
#
#    rights = etree.SubElement(xml_record, "")
#    rights.text = ""
#    rights_url = etree.SubElement(xml_record, "")
#    rights_url.text = ""
#
#    license = etree.SubElement(xml_record, "")
#    license.text = ""
#
#    license_name = etree.SubElement(xml_record, "")
#    license_name.text = ""
#    license_url = etree.SubElement(xml_record, "")
#    license_url.text = ""
#
#    citation_title = etree.SubElement(xml_record, "")
#    citation_title.text = ""
#    citation_creators = etree.SubElement(xml_record, "")
#    for model_creator in metadata_record.citation_creators:
#        creator = etree.SubElement(xml_record, "")
#        creator.text = ""
#    citation_edition = etree.SubElement(xml_record, "")
#    citation_edition.text = ""
#    citation_publisher = etree.SubElement(xml_record, "")
#    citation_publisher.text = ""
#    citation_place_of_publication = etree.SubElement(xml_record, "")
#    citation_place_of_publication.text = ""
#
#    citation_dates = etree.SubElement(xml_record, "")
#    for model_date in metadata_record.citation_dates:
#        citation_date = etree.SubElement(xml_record, "")
#        citation_date.text = ""
#
#    citation_url = etree.SubElement(xml_record, "")
#    citation_url.text = ""
#    citation_context = etree.SubElement(xml_record, "")
#    citation_context.text = ""
#
#    retention_period = etree.SubElement(xml_record, "")
#    retention_period.text = ""
#
#    related_publications = etree.SubElement(xml_record, "")
#    for model_publication in metadata_record:
#        related_publication = etree.SubElement(xml_record, "")
#        related_publication.text = ""
#
#    related_websites = etree.SubElement(xml_record, "")
#    for model_website in metadata_record.related_websites:
#        related_website = etree.SubElement(xml_record, "")
#        related_website.text = ""
#
#    attachments = etree.SubElement(xml_record, "")
#    for model_attachment in metadata_record.attachments:
#        attachment = etree.SubElement(xml_record, "")
#        attachment.text = ""

