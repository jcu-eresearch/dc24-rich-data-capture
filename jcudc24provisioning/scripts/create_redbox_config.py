"""
Create a JSON configuration and XPATH mapping of the output XML metadata record to ReDBox fields.
"""

import json
import sys

from pyramid.paster import setup_logging, get_appsettings
from jcudc24provisioning.controllers.sftp_filesend import SFTPFileSend
from jcudc24provisioning.models.project import Metadata, Party, Keyword, Collaborator, MetadataNote, CitationDate, Attachment, RelatedPublication, RelatedWebsite, FieldOfResearch, SocioEconomicObjective, Location, Creator
import os


__author__ = 'Casey Bajema'


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %(cmd)s [arguments] <file>\t\t\tWrite the configuration to a local file.\n'
          '\t(example: "%(cmd)s -s http:\\\\www.example.com\\redbox\\home\\harvest\\my-harvester\\config\\myXmlMapping.xml development.ini)"\n\n'
          'Arguments:\n'
          '\t -s <config>\t\t\tSend the created XML mapping to ReDBox over sftp using the provided configuration.' % {
              "cmd": cmd})
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) > 4 or len(argv) < 2 or\
       len(argv) > 2 and argv[1] != "-s":
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    xmlMapping = create_json_config()

    file = argv[len(argv) - 1]
    f = open(file, 'w')
    f.write(xmlMapping)

    if argv[1] == "-s":
        settings = get_appsettings(config_uri)
        file_send = SFTPFileSend(settings['redbox.ssh_host'], settings['redbox.ssh_port'],
            settings['redbox.ssh_username'],
            settings['redbox.ssh_password'],
            settings['redbox.rsa_private_key'])
        file_send.upload_file(file, settings['redbox.ssh_config_file'])
        file_send.close()


def create_json_config():
    """
    Create the mapping, the output will only change when Metadata table field(s)/names change.

    :return: JSON configuration of XPATH mappings for ReDBox.  The XPATH maps from provisioning interface metadata table
             fields to ReDBox fields.
    """
# TODO: Work out if any of these fields are needed?
#    "dc:extent": "",                                   # Size of data

# Data management fields
#na     "redbox:disposalDate": "",                      # Data owner
#na     "locrel:own.foaf:Agent.0.foaf:name": "",        # Data owner
#na     "locrel:dtm.foaf:Agent.foaf:name": "",          # Data custodian - TODO: Should this be filled with JCU?
#     "foaf:Organization.dc:identifier": "",            # Data affiliation
#     "foaf:Organization.skos:prefLabel": "",           # Data affiliation
#     "swrc:ResearchProject.dc:title": "",   # TODO: Should this be added? - would map to the project title field?
#na     "locrel:dpt.foaf:Person.foaf:name": "",         # Depositor
#na    "dc:SizeOrDuration": "",                         # Data size
#na     "dc:Policy": "",                                # Institutional data management policy
#na    "redbox:ManagementPlan.redbox:hasPlan": null,    # Data management policy
#na     "redbox:ManagementPlan.skos:note": "",          # Data management policy
#na     "skos:note.0.dc:created": "",
#na     "skos:note.0.foaf:name": "",                    # Seems to be a notes squence that is split between muliple places as individual fields
#na     "skos:note.0.dc:description": "",


#    # TODO: What is the metalist?
##    "metaList": [...]



    dict_config = {
        "comment": "This James Cook University's XML mapping is generated from the DC24 RichDataCapture provisioning interface.  It is generated on startup to create a ReDBox json configuration file that matches the models XML conversion.",
        "mappings": {
            "/metadata": {
                Metadata.record_export_date.key: "dc:created",
                Metadata.dc_spec.key: "xmlns:dc",
                Metadata.foaf_spec.key: "xmlns:foaf",
                Metadata.anzsrc_spec.key: "xmlns:anzsrc",
                Metadata.view_id.key: "viewId",
                Metadata.package_type.key: "packageType",
                Metadata.record_origin.key: "dc:identifier.redbox:origin",
                #TODO: What should this be prefilled with? Internal or something like rdc?
                Metadata.new_redbox_form.key: "redbox:newForm", #TODO: Should this be true?
                Metadata.redbox_form_version.key: "redbox:formVersion",
                Metadata.record_type.key: "dc:type.rdf:PlainLiteral",
                Metadata.record_type_label.key: "dc:type.skos:prefLabel",
                Metadata.language.key: "dc:language.dc:identifier",
                Metadata.language_label.key: "dc:language.skos:prefLabel",
                Metadata.use_record_id.key: "dc:identifier.checkbox",
                Metadata.type_of_identifier.key:"dc:identifier.dc:type.rdf:PlainLiteral",
                Metadata.type_of_identifier_label.key:"dc:identifier.dc:type.skos:prefLabel",
                Metadata.redbox_identifier.key: ["dc:identifier.rdf:PlainLiteral", "known_ids"],

                Metadata.data_storage_location.key: "bibo:Website.1.dc:identifier",
                Metadata.data_storage_location_name.key: "vivo:Location.vivo:GeographicLocation.gn:name",
                Metadata.ccdam_identifier.key: "bibo:Website.0.dc:identifier",
                Metadata.project_title.key: ["title", "dc:title", "redbox:submissionProcess.dc:title"],
                Metadata.internal_grant.key: "foaf:fundedBy.vivo:Grant.0.redbox:internalGrant",
                Metadata.grant_number.key: "foaf:fundedBy.vivo:Grant.0.redbox:grantNumber",
                Metadata.grant_label.key: "foaf:fundedBy.vivo:Grant.0.skos:prefLabel",
                Metadata.grant.key: "foaf:fundedBy.vivo:Grant.0.dc:identifier",
                Metadata.parties.key + "/*": {
                    Party.party_relationship_label.key: "dc:creator.foaf:Person.0.jcu:relationshipLabel",
                    Party.party_relationship.key: "dc:creator.foaf:Person.0.jcu:relationshipType",
                    Party.identifier.key: ["dc:creator.foaf:Person.0.dc:identifier", "locrel:prc.foaf:Person.dc:identifier"],
                    Party.name.key: "dc:creator.foaf:Person.0.foaf:name",
                    Party.title.key: ["dc:creator.foaf:Person.0.foaf:title", "locrel:prc.foaf:Person.foaf:title"],
                    #                Party.coprimary: "dc:creator.foaf:Person.0.redbox:isCoPrimaryInvestigator",       # TODO: Are these needed?
                    #                Party.primary: "dc:creator.foaf:Person.0.redbox:isPrimaryInvestigator",
                    Party.given_name.key: ["dc:creator.foaf:Person.0.foaf:givenName", "locrel:prc.foaf:Person.foaf:givenName"],
                    Party.family_name.key: ["dc:creator.foaf:Person.0.foaf:familyName", "locrel:prc.foaf:Person.foaf:familyName"],
                    Party.association.key: "dc:creator.foaf:Person.0.foaf:Organization.dc:identifier",
                    Party.association_label.key: "dc:creator.foaf:Person.0.foaf:Organization.skos:prefLabel",
                    Party.email.key: "locrel:prc.foaf:Person.foaf:email",            # Primary contact
                    Party.short_display_name.key: "locrel:prc.foaf:Person.foaf:name",
                },
                Metadata.collaborators.key + "/*": {
                    Collaborator.collaborator.key: "dc:contributor.locrel:clb.0.foaf:Agent",
                },
#                "descriptions": {
                Metadata.brief_desc_label.key + " | " + Metadata.full_desc_label.key  + " | " + Metadata.notes.key + "/*/" + MetadataNote.note_desc_label.key: "rif:description.0.label",
                Metadata.brief_desc_type.key + " | " + Metadata.full_desc_type.key + " | " + Metadata.notes.key + "/*/" + MetadataNote.note_desc_type.key: "rif:description.0.type",
                Metadata.brief_desc.key + " | " + Metadata.full_desc.key + " | " + Metadata.notes.key + "/*/" + MetadataNote.note_desc.key: "rif:description.0.value",
                Metadata.brief_desc.key: ["description", "dc:description"],
                Metadata.keywords.key + "/*": {
                    Keyword.keyword.key: "dc:subject.vivo:keyword.0.rdf:PlainLiteral",
                },
                Metadata.field_of_research.key + "/*": {
                    FieldOfResearch.field_of_research.key: "dc:subject.anzsrc:for.0.rdf:resource",
                    FieldOfResearch.field_of_research_label.key: "dc:subject.anzsrc:for.0.skos:prefLabel",
                },
                Metadata.socio_economic_objective.key + "/*": {
                    SocioEconomicObjective.socio_economic_objective.key: "dc:subject.anzsrc:seo.0.rdf:resource",
                    SocioEconomicObjective.socio_economic_objective_label.key: "dc:subject.anzsrc:seo.0.skos:prefLabel",
                },
                Metadata.no_research_theme.key: "jcu:research.themes.notAligned",
                Metadata.ecosystems_conservation_climate.key: "jcu:research.themes.tropicalEcoSystems",
                Metadata.industries_economies.key: "jcu:research.themes.industriesEconomies",
                Metadata.peoples_societies.key: "jcu:research.themes.peopleSocieties",
                Metadata.health_medicine_biosecurity.key: "jcu:research.themes.tropicalHealth",
                Metadata.type_of_research_label.key: "dc:subject.anzsrc:toa.skos:prefLabel",
                Metadata.type_of_research.key: "dc:subject.anzsrc:toa.rdf:resource",
                Metadata.time_period_description.key: "dc:coverage.redbox:timePeriod",
                Metadata.date_from.key: "dc:coverage.vivo:DateTimeInterval.vivo:start",
                Metadata.date_to.key: "dc:coverage.vivo:DateTimeInterval.vivo:end",

#                Metadata.location_description.key: "",
                Metadata.locations.key + "/*": {
                    Location.location_type.key: "dc:coverage.vivo:GeographicLocation.0.dc:type",
                    # TODO: create hidden field prefilled with text.
                    Location.name.key: "", #TODO: Do something with location names and elevations.
                    Location.location.key: ["dc:coverage.vivo:GeographicLocation.0.redbox:wktRaw",
                                            "dc:coverage.vivo:GeographicLocation.0.rdf:PlainLiteral"],
                    Location.elevation.key: "",
                },
                Metadata.access_rights.key: "dc:accessRights.skos:prefLabel",
                Metadata.access_rights_url.key: "dc:accessRights.dc:identifier",
                Metadata.rights.key: "dc:accessRights.dc:RightsStatement.skos:prefLabel",
                Metadata.rights_url.key: "dc:accessRights.dc:RightsStatement.dc:identifier",

                Metadata.license_label.key: "dc:license.skos:prefLabel",
                Metadata.license.key: "dc:license.dc:identifier",
                Metadata.other_license_name.key: "dc:license.rdf:Alt.skos:prefLabel",
                Metadata.other_license_url.key: "dc:license.rdf:Alt.dc:identifier",
                Metadata.citation_title.key: "dc:biblioGraphicCitation.dc:hasPart.dc:title",
                Metadata.citation_creators.key + "/*": {
                    Creator.title.key: "dc:biblioGraphicCitation.dc:hasPart.locrel:ctb.0.foaf:title",
                    Creator.given_name.key: "dc:biblioGraphicCitation.dc:hasPart.locrel:ctb.0.foaf:givenName",
                    Creator.family_name.key: "dc:biblioGraphicCitation.dc:hasPart.locrel:ctb.0.foaf:familyName",
                },
                Metadata.citation_edition.key: "dc:biblioGraphicCitation.dc:hasPart.dc:hasVersion.rdf:PlainLiteral",
                Metadata.citation_publisher.key: "dc:biblioGraphicCitation.dc:hasPart.dc:publisher.rdf:PlainLiteral",
                Metadata.citation_place_of_publication.key: [
                    "dc:biblioGraphicCitation.dc:hasPart.vivo:Publisher.vivo:Location",
                    "dc:biblioGraphicCitation.dc:hasPart.dc:date.0.rdf:PlainLiteral"],
#                Metadata.citation_publish_date.key: "publication-date-citation",
                Metadata.citation_dates.key + "/*": {
                    CitationDate.label.key: "dc:biblioGraphicCitation.dc:hasPart.dc:date.0.dc:type.skos:prefLabel",
                    # TODO: Get this label as the name in the dropdown (datetype is the value)
                    CitationDate.type.key: "dc:biblioGraphicCitation.dc:hasPart.dc:date.0.dc:type.rdf:PlainLiteral",
                    CitationDate.date.key: "dc:biblioGraphicCitation.dc:hasPart.dc:date.0.rdf:PlainLiteral",
                },
                Metadata.citation_url.key: "dc:biblioGraphicCitation.dc:hasPart.bibo:Website.dc:identifier",
                Metadata.citation_data_type.key: "dc:biblioGraphicCitation.dc:hasPart.jcu:dataType",
                Metadata.citation_context.key: "dc:biblioGraphicCitation.dc:hasPart.skos:scopeNote",
                Metadata.send_citation.key: "dc:biblioGraphicCitation.redbox:sendCitation",
                Metadata.citation_string.key: "dc:biblioGraphicCitation.skos:prefLabel",
                Metadata.use_curation.key: "dc:biblioGraphicCitation.dc:hasPart.dc:identifier.skos:note",
                # TODO: Citation->use identifier provided during curation? - Ask if this should be on?
                Metadata.retention_period.key: "redbox:retentionPeriod",
                Metadata.related_publications.key + "/*": {
                        RelatedPublication.title.key: "dc:relation.swrc:Publication.0.dc:title",
                        RelatedPublication.url.key: "dc:relation.swrc:Publication.0.dc:identifier",
                        RelatedPublication.notes.key: "dc:relation.swrc:Publication.0.skos:note",
                },
                Metadata.related_websites.key + "/*": {
                    RelatedWebsite.title.key: "dc:relation.bibo:Website.0.dc:title",
                    RelatedWebsite.url.key: "dc:relation.bibo:Website.0.dc:identifier",
                    RelatedWebsite.notes.key: "dc:relation.bibo:Website.0.skos:note",

                },
                Metadata.attachments.key + "/*": {
                    Attachment.type.key: "",
                    Attachment.attachment.key: "", # TODO: How to add attachments?
                    Attachment.note.key: "",

                },
                "related_records/*": {
                    "identifier": "dc:relation.vivo:Dataset.0.dc:identifier",
                    "relationship": "dc:relation.vivo:Dataset.0.vivo:Relationship.rdf:PlainLiteral",
                    "preflabel": "dc:relation.vivo:Dataset.0.vivo:Relationship.skos:prefLabel",
                    "title": "dc:relation.vivo:Dataset.0.dc:title",
                    "notes": "dc:relation.vivo:Dataset.0.skos:note",
                    "origin": "dc:relation.vivo:Dataset.0.redbox:origin",
                    "publish": "dc:relation.vivo:Dataset.0.redbox:publish",
                }
                #
                #
                #            # TODO: This is the related servces fields
                #            "dc:relation.vivo:Service.0.dc:identifier": "some_identifier",
                #            "dc:relation.vivo:Service.0.vivo:Relationship.rdf:PlainLiteral": "isProducedBy",
                #            "dc:relation.vivo:Service.0.vivo:Relationship.skos:prefLabel": "Is produced by:",
                #            "dc:relation.vivo:Service.0.dc:title": "Artificial tree sensor",
                #            "dc:relation.vivo:Service.0.skos:note": "test notes",
            }
        }, "exceptions": {
            "fields": {}
        },
        "defaultNamespace": {}
    }

    json_config = json.dumps(dict_config, sort_keys=True, indent=4, separators=(',', ': '))
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

