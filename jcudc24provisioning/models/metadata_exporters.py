import json
import colander
from lxml import etree
from sqlalchemy import Column
from jcudc24provisioning.models.ca_model import CAModel
from jcudc24provisioning.views.ca_scripts import fix_schema_field_name

__author__ = 'Casey Bajema'

class ReDBoxExportWrapper(CAModel):
    def _add_xml_elements(self, root, data):
        for key, value in data.items():
            key = fix_schema_field_name(key)
            element = etree.SubElement(root, key)
            if value is colander.null or value is None or (isinstance(value, list) and len(value) == 0):
                continue

            if isinstance(value, dict):
                self._add_xml_elements(element, value)
            elif isinstance(value, list):
                for i in range(len(value)):
                    child_element = etree.SubElement(element, key + ".%i" % i)
                    self._add_xml_elements(child_element, value[i])
            else:
                element.text = str(value)
        return element

    def to_xml(self):
        root = etree.Element(self.__class__.__name__.lower())
        root.append(self._add_xml_elements(root, self.dictify()))

        print (etree.tostring(root.getroottree().getroot(), pretty_print=True))
        return etree.ElementTree(root.getroottree().getroot())


    def _create_mapping(self, data, list_item=False):
        if len(data) == 1:
            return ""
        elif len(data) > 1:
            result = {}

            for key, value in data.items():
                rdc_key = "/%s" % fix_schema_field_name(key)
                if list_item:
                    rdc_key += ".0"

                if isinstance(value, dict):
                    result[key] = self._create_mapping(value)
                elif isinstance(value, list):
                    result[key] = self._create_mapping(value[0], True)
                else:
                    result["."] = str(value)
        return result

    def to_json_config(self):
        dict_config = {
            "comment": "This James Cook University's XML mapping is generated from the DC24 RichDataCapture provisioning interface.  It is generated on startup to create a ReDBox json configuration file that matches the models XML conversion.",
            "mappings": self._create_mapping(self.dictify(force_not_empty_lists=True)),
            "exceptions": {
            },
            "defaultNamespace": {}
        }




        json_config = json.dumps(dict_config)
        print json_config
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

