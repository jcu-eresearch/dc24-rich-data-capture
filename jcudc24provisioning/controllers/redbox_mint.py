"""
Wrapper for converting provisioning interface projects and/or datasets into ReDBox metadata records and exporting them
to ReDBox over SFTP.

The ReDBox export relies on the enmasse-alerts harvester being setup as per the administrator guide and the process is:
- Create and update metadata entries for each project and dataset.  Making sure all ReDBox speicic fields are correct.
- Write the metadata entries to XML files.
- Copy the output XML files to the ReDBox server over SFTP.
- Alert ReDBox that there are new records to harvest by calling the new alerts harvester URL.
- Cleanup written XML files and set the metadata export date in the metadata table.
"""

from copy import deepcopy
from datetime import datetime, date
import random
import shutil
import string
import colander
from paste.deploy.converters import asint
import re
import requests
from jcudc24provisioning.controllers.sftp_filesend import SFTPFileSend
from jcudc24provisioning.models.project import PullDataSource, Metadata, UntouchedPages, IngesterLogs, Location, \
    ProjectTemplate,method_template,DatasetDataSource, Project, project_validator, ProjectStates, CreatePage, Method, Party, Dataset, MethodSchema, create_project_validator, MethodTemplate, Creator, CitationDate
from jcudc24provisioning.views.ajax_mint_lookup import MintLookup

from lxml import etree
import os
from jcudc24provisioning.models import DBSession
import logging

logger = logging.getLogger(__name__)

__author__ = 'casey'

# TODO: Deemed too hard/confusing for the end, but this should be most of the code + ServiceMetadata in project.  The most difficult part will be providing a user freindly way of getting service informtaion.
#class MintWrapper(object):
#    def __init__(self, tmp_dir, identifier_pattern, ssh_host, ssh_port, harvest_file, ssh_username, rsa_private_key=None, ssh_password=None):
#        self.session = DBSession
#        self.tmp_dir = tmp_dir
#        self.identifier_pattern = identifier_pattern
#        self.ssh_host = ssh_host
#        self.ssh_port = ssh_port
#        self.harvest_file = harvest_file
#        self.ssh_username = ssh_username
#        self.rsa_private_key = rsa_private_key
#        self.ssh_password = ssh_password
#
#
#    def generate_mint_metadata(self, method):
#        project = self.session.query(Project).filter_by(id=method.project_id).first()
#
#        service = ServiceMetadata()
#        service.name = method.method_name
#        service.type = "Services"
#        service.related_party_1 = project.information.parties[0].identifier
#        service.related_relationship_1 = project.information.parties[0].party_relationship
#        service.related_party_2 = project.information.parties[1].identifier
#        service.related_relationship_2 = project.information.parties[1].party_relationship
#
#        service.field_of_research = project.information.fieldsOfResearch[:]
#
#        service.keywords = project.information.keywords.join(" ")
#        service.license = project.information.license_name
#        service.license_url = project.information.license
#        service.access_rights = project.information.access_rights_url
#        service.delivery_method = "Download"
#        service.description = method.method_description
##        service.website =
##        service.website_title = self.identifier_pattern + method.id
#
#        return service
#
#    def insert(self, project_id):
#        project = self.session.query(Project).filter_by(id=project_id).first()
#
#        file_path = self.tmp_dir + "services_emas.csv"
#
#        # If this is the first service being created, add the header row.
#        if not os.path.exists(file_path):
#            with open(file_path, "w") as f:
#                f.write("ID, Name, Type, Related_party1, Related_relationship1, Related_party2, Related_relationship2, "
#                        "ANZSRC_FOR_1, ANZSRC_FOR_2, ANZSRC_FOR_3, Keywords, licence, licence_URL, "
#                        "access_rights, deliverymethod, description, Website, Website_Title")
#
#        with open(file_path, "a") as f:
#            for method in project.methods:
#                if method.service_metadata_id is None:
#                    service = self.generate_mint_metadata(method)
#                else:
#                    service = self.session.query(ServiceMetadata).filter_by(id=method.service_metadata_id).first()
#
#                csv_line = self._to_csv(service)
#
#                f.write(csv_line)
#
#        self._upload_services()
#
#    def _upload_services(self):
#        local_file = self.tmp_dir + "services_emas.csv"
#
#        file_send = SFTPFileSend(self.ssh_host, self.ssh_port, self.ssh_username, password=self.ssh_password, rsa_private_key=self.rsa_private_key)
#        file_send.upload_file(local_file, self.harvest_file)
#        file_send.close()
#
#
#    def _to_csv(self, service):
#        service_csv = "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (
#                service.mint_id,
#                service.name,
#                service.type,
#                service.related_party_1,
#                service.related_relationship_1,
#                service.related_party_2,
#                service.related_relationship_2,
#                service.field_of_research[0] or "",
#                service.field_of_research[1] or "",
#                service.field_of_research[2] or "",
#                service.keywords,
#                service.license,
#                service.license_url,
#                service.access_rights,
#                service.delivery_method,
#                service.description,
#                service.website,
#                service.website_title,
#        )
#
#        return service

class ReDBoxMock(object):
    """
    This is a mock implementation of the ReDBox service which will be used when
    no ReDBox url is provided
    """
    def insert_project(self, project_id):
        logger.info("MOCK REDBOX: Insert project %s"%project_id)
        return
    
    def insert_dataset(self, dataset_id):
        logger.info("MOCK REDBOX: Insert dataset %s"%dataset_id)
        return
    
    def pre_fill_citation(self, metadata):
        logger.info("MOCK REDBOX: Prefill citation")
        return

class ReDBoxWrapper(object):
    """
    Provides methods to transparently export projects and datasets to ReDBox (basically direct mapping of metadata table).
    """

    def __init__(self, data_portal, url, alert_url, search_url, identifier_pattern, ssh_host, ssh_port, tmp_dir, harvest_dir, ssh_username, rsa_private_key=None, ssh_password=None):
        """
        Initialise the parameters for the connected ReDBox server and working data.

        :param data_portal: URL prefix of the address for viewing the data (metadata.id is appended to this prefix).
        :param url: Location of the ReDBox instance.
        :param identifier_pattern: Prefix for the generated ReDBox identifier (metadata.id is appended to it).
        :param ssh_host: ReDBox server SSH address (SFTP is file transfer over SSH).
        :param ssh_port: ReDBox server SSH port number (SFTP is file transfer over SSH).
        :param tmp_dir: Temporary directory to write metadata as XML files.
        :param harvest_dir: Location on the ReDBox server to copy XML files into (eg. /opt/deploy/redbox/home/harvest/enmasse-alerts).
        :param ssh_username: Username for the SSH connection.  This is only required if an key isn't provided.
        :param rsa_private_key: Private key to use for authenticating the SSH connection.
        :param ssh_password: Password of the the SSH private key or to use with the provided SSH username.
        :return: This ReDBoxWrapper instance.
        """
        self.data_portal = data_portal
        self.url = url
        self.alert_url = alert_url
        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.harvest_dir = harvest_dir
        self.ssh_username = ssh_username
        self.rsa_private_key = rsa_private_key
        self.ssh_password = ssh_password
        self.tmp_dir = tmp_dir
        self.identifier_pattern = identifier_pattern
        self.search_url = search_url

        self.session = DBSession


    def insert_project(self, project_id):
        """
        Generate metadata records for this project and associated datasets and export them to ReDBox.

        :param project_id: The project to generate and export metadata records from.
        :return: True if the export was successful, otherwise False.
        """
        project = self.session.query(Project).filter_by(id=project_id).first()

        # Set the metadata type to repository as it is about multiple collections and also provides data.
#        project.information.record_type = "repository"

        # 1. TODO: Create service records.

        # 2. TODO: Create relationships between each service record and it's dataset.

        # 3. Create all dataset records (the project itself creates 1 dataset record).
        project_record = self._prepare_record(project.information).to_xml().getroot()

        dataset_metadata = [self._prepare_record(dataset.record_metadata) for dataset in project.datasets if dataset.publish_dataset]
        dataset_records = [metadata.to_xml().getroot() for metadata in dataset_metadata]

        # 4. Add relationships between all dataset records.
        self._add_relationships(project_record, dataset_records)

        # 5. Create the tmp directory
        self._create_working_dir()

        # 6. Write all records (dataset and service) to a tmp directory ready for upload.
        self._write_to_tmp([project_record] + dataset_records)

        # 7. Upload all files in the
        self._upload_record_files()

        #8. Alert ReDBox that there are new records
        self._alert_redbox()


        #9. Set the date that the records were added to ReDBox
        project.information.date_added_to_redbox = datetime.now()

        for dataset in project.datasets:
            dataset.record_metadata.date_added_to_redbox = datetime.now()

        #9. Remove the tmp directory
        shutil.rmtree(self.working_dir)

        return True

    def insert_dataset(self, dataset_id):
        """
        Generate metadata record for this dataset and export it to ReDBox.

        :param dataset_id: The dataset to generate and export a metadata record for.
        :return: True if the export was successful, otherwise False.
        """
        dataset = self.session.query(Dataset).filter_by(id=dataset_id).first()
        if not dataset.publish_dataset:
            return True

        project = self.session.query(Project).filter_by(id=dataset.project_id).first()

        # Set the metadata type to repository as it is about multiple collections and also provides data.
        #        project.information.record_type = "repository"

        # 1. TODO: Create service records.

        # 2. TODO: Create relationships between each service record and it's dataset.

        # 3. Create a temporary project record so that we can add the relationship
        project_record = self._prepare_record(project.information).to_xml().getroot()

        dataset_metadata = self._prepare_record(dataset.record_metadata)
        dataset_record = dataset_metadata.to_xml().getroot()

        # 4. Add relationships between all dataset records.
        self._add_relationships(project_record, dataset_record)

        # 5. Create the tmp directory
        self._create_working_dir()

        # 6. Write all records (dataset and service) to a tmp directory ready for upload.
        self._write_to_tmp([dataset_record])

        # 7. Upload all files in the
        self._upload_record_files()

        #8. Alert ReDBox that there are new records
        self._alert_redbox()

        dataset.record_metadata.date_added_to_redbox = datetime.now()

        #9. Remove the tmp directory
        shutil.rmtree(self.working_dir)

        return True

    def _process_xml(self, xml):
#        xml.replace("<%s>false</%s>" % (Metadata.industries_economies.key))

        return xml

    def _prepare_record(self, record):
        """
        Fill and update any ReDBox specific fields of the metadata table ready for exporting.

        :param record: The record (XML node) to fix.
        :return: Updated record (XML node).
        """
        # Split the FOR and SEO codes into value/label pairs.
        for field_of_research in record.field_of_research:
            field_of_research.field_of_research = "http://purl.org/asc/1297.0/2008/for/%s" % field_of_research.field_of_research_label.split(" ")[0]

        for socio_economic_objective in record.socio_economic_objective:
            socio_economic_objective.socio_economic_objective = "http://purl.org/asc/1297.0/2008/seo/%s" %socio_economic_objective.socio_economic_objective_label.split(" ")[0]

        # Set the redbox identifier
        record.redbox_identifier = self.identifier_pattern + str(record.id)

        # Set the redbox_uri
        record.redbox_uri = "%s%s%s" % (self.url, self.search_url, record.redbox_identifier)

        # Set the record export date.
        record.record_export_date = datetime.now().date()

        mint_lookup = MintLookup(None)

        if record.grant is not None and record.grant != str(colander.null):
            mint_grant = mint_lookup.get_from_identifier(record.grant)
            record.grant_number = record.grant.split("/")[-1]
            record.grant_label = mint_grant['rdfs:label']

        for person in record.parties:
            mint_person = mint_lookup.get_from_identifier(person.identifier)

            person.name = str(mint_person['result-metadata']['all']['Honorific'][0]) + " " + str(mint_person['result-metadata']['all']['Given_Name'][0]) \
                                                    + " " + str(mint_person['result-metadata']['all']['Family_Name'][0])
            person.title = mint_person['result-metadata']['all']['Honorific'][0]
            person.given_name = mint_person['result-metadata']['all']['Given_Name'][0]
            person.family_name = mint_person['result-metadata']['all']['Family_Name'][0]
#            person.organisation = mint_person['dc:title']
#            person.organisation_label = mint_person['dc:title']
            person.email = mint_person['result-metadata']['all']['Email'][0]

            school_group_match = "[^0]{3}0"
            person.association = mint_person['result-metadata']['all']['GroupID_1'][0]
            if not re.match(school_group_match, str(person.association)):
                if re.match(school_group_match, str(mint_person['result-metadata']['all']['GroupID_2'][0])):
                    person.association = mint_person['result-metadata']['all']['GroupID_2'][0]
                if re.match(school_group_match, str(mint_person['result-metadata']['all']['GroupID_3'][0])):
                    person.association = mint_person['result-metadata']['all']['GroupID_3'][0]
            person.association = "jcu.edu.au/parties/group/%s" % person.association

            mint_association = mint_lookup.get_from_identifier(person.association)
            person.association_label = mint_association['dc:title']

            person.short_display_name = mint_person['dc:title']

        record.data_storage_location = self.data_portal + str(record.id)

        # Only update the citation if it is empty
        if record.custom_citation is not True:
            self.pre_fill_citation(record)

        # Make sure all parties are unique
        party_ids = []
        for i in range(len(record.parties)):
            if record.parties[i].identifier in party_ids:
                del record.parties[i]
            else:
                party_ids.append(record.parties[i].identifier)

#        if len(record.parties) > 1 and record.parties[0].identifier == record.parties[1].identifier:
#            del record.parties[1]

        # Use other license instead if it is entered.

        return record

    def pre_fill_citation(self, metadata):
        """
        Use the project and dataset data to generate the metadata records citation.

        :param metadata: Metadata table model to generate a citation in.
        :return: None
        """
        if metadata is None:
            raise ValueError("Updating citation on None metadata")

        del metadata.citation_creators[:]
        added_parties = []
        for party in metadata.parties:
            if party.identifier not in added_parties:
                added_parties.append(party.identifier)
                metadata.citation_creators.append(Creator(party.title, party.given_name, party.family_name))

        if metadata.dataset_id is not None:
            dataset = self.session.query(Dataset).filter_by(id=metadata.dataset_id).first()
            metadata.citation_publish_date = dataset.publish_date
        else:
            metadata.citation_publish_date = metadata.record_export_date

        del metadata.citation_dates[:]
        metadata.citation_dates.append(CitationDate(metadata.citation_publish_date, "publicationDate", "Publication Date"))

       # Fill citation fields
        metadata.citation_title = metadata.project_title

#       metadata.citation_edition = None
        metadata.citation_publisher = "James Cook University"
        metadata.citation_place_of_publication = None
       # Type of Data?
        metadata.citation_url = metadata.data_storage_location
#       metadata.citation_context = metadata.project_title
        metadata.citation_data_type = "Data Files"

        people_string = ""
        for person in metadata.parties:
            if len(people_string) > 0:
                people_string += "; "
            people_string += "%s, %s" % (person.family_name, person.given_name)

        # The publish date may be None if this s being pre-filled but isn't being approved yet.
        if metadata.citation_publish_date is not None:
            metadata.citation_string = "%s (%s). %s. %s. [%s] {ID_WILL_BE_HERE}" % (people_string, metadata.citation_publish_date.year, metadata.citation_title,
                                 metadata.citation_publisher, metadata.citation_data_type)

        metadata.record_origin = "external"
        metadata.use_curation = "useCuration"


    def _write_to_tmp(self, records):
        """
        Write the passed in records (XML trees) to the temporary directory.

        :param records: Metadata records as XML trees.
        :return: None
        """
        for record in records:
            identifier = record.xpath("%s" % Metadata.redbox_identifier.key)
            if len(identifier) == 1:
                identifier = (identifier[0].text).replace("\\", ".").replace("/", ".")
                number = int(identifier[identifier.rindex('.')+1:])
                formatted_identifier = (identifier[:identifier.rindex('.')] + '.{:0>9}').format(number)
                tmp_file_path = self.working_dir + formatted_identifier + ".xml"
                f = open(tmp_file_path, 'w')
                f.write(self._process_xml((etree.tostring(record.getroottree().getroot(), pretty_print=True))))
            else:
                raise AttributeError("Trying to create ReDBox record with no redbox_identifier set.")

    def _create_working_dir(self):
        """
        Create the working directory for this export, each project exports to its own directory that is randomly created.
        :return:
        """
        # Create a unique directory for this operation
        self.working_dir = self.tmp_dir + ''.join(random.choice(string.letters) for i in range(20)) + os.sep
        while os.path.exists(self.working_dir):
            self.working_dir = self.tmp_dir + ''.join(random.choice(string.letters) for i in range(20)) + os.sep

        os.mkdir(self.working_dir)

    def _upload_record_files(self):
        """
        Upload all XML files in the temporary directory to ReDBox ready for harvesting.

        :return: None
        """
        file_send = SFTPFileSend(self.ssh_host, self.ssh_port, self.ssh_username, password=self.ssh_password, rsa_private_key=self.rsa_private_key)
        file_send.upload_directory(self.working_dir, self.harvest_dir)
        file_send.close()

    def _alert_redbox(self):
        """
        Poll the ReDBox new alerts URL to indicate there is new metadata records ready to harvest.

        :return: None
        """
        return requests.post(self.alert_url)

    def _add_relationships(self, project_record, dataset_records):
        """
        Add parent-child relationships between the project record and each dataset records.

        :param project_record: Project record that is the parent (has part) of each dataset record
        :param dataset_records: Dataset records that are each children (part of) the project record.
        :return:
        """
        original_records = {}    # Records what dataset record the relationship came from

        related_parent = self._create_relationship_node(project_record, "isPartOf")

#        # Create the relationships for related data
#        related_siblings = []
#        related_children = []
#        for related_record in dataset_records:
##            sibling = self._create_relationship_node(related_record, "hasAssociationWith") - Don't do this, circular relationships!
#            child = self._create_relationship_node(related_record, "hasPart")
#
##            original_records[related_record] = sibling
#
##            related_siblings.append(sibling)
#            related_children.append(child)
#
#        # Add all records generated from datasets as related data for the project record.
#        related_records = etree.SubElement(project_record, "related_records")
#        for child in related_children:
#            related_records.append(child)

        for record in dataset_records:
            # Add a data relationship to the project for on dataset records.
            related_records = etree.SubElement(record, "related_records")
            related_records.append(deepcopy(related_parent))

#           # Add data relationships between all datasets within the project.
#            for related_record in related_siblings:
#               # Don't add a relationship to itself.
#                if related_record != original_records[record]:
#                    record.append(related_record)
#
#
#        #            # TODO: This is the related services fields
#        #            "dc:relation.vivo:Service.0.dc:identifier": "some_identifier",
#        #            "dc:relation.vivo:Service.0.vivo:Relationship.rdf:PlainLiteral": "isProducedBy",
#        #            "dc:relation.vivo:Service.0.vivo:Relationship.skos:prefLabel": "Is produced by:",
#        #            "dc:relation.vivo:Service.0.dc:title": "Artificial tree sensor",
#        #            "dc:relation.vivo:Service.0.skos:note": "test notes",


    def _create_relationship_node(self, record, relationship_type):
        """
        Create an XML node that is a ReDBox relationship of relationship_type for record.

        :param record: The record that this relationship is about (not the record the relationship is being added to).
        :param relationship_type: Type of relationship as per ReDBox (eg. hasPart, isPartOf)
        :return: Create XML relationship node.
        """
        related_record_node = etree.Element("related_record")

        identifier = etree.SubElement(related_record_node, "identifier")
        identifier.text = unicode(record.xpath("/metadata/%s" % Metadata.redbox_identifier.key)[0].text)

        relationship = etree.SubElement(related_record_node, "relationship")
        relationship.text = relationship_type

        preflabel = etree.SubElement(related_record_node, "preflabel")
        preflabel.text = "Has association with:"

        title = etree.SubElement(related_record_node, "title")
        title.text = unicode(record.xpath("%s" % Metadata.project_title.key)[0].text)

        notes = etree.SubElement(related_record_node, "notes")
        notes.text = "Related dataset from the same EMAS project."

        origin = etree.SubElement(related_record_node, "origin")
        origin.text = "on"

        publish = etree.SubElement(related_record_node, "publish")
        publish.text = "on"

        return  related_record_node



