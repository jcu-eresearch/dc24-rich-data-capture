from datetime import datetime
import random
import shutil
import string
from paste.deploy.converters import asint
import requests
from jcudc24provisioning.controllers.sftp_filesend import SFTPFileSend
from jcudc24provisioning.models.project import PullDataSource, Metadata, UntouchedPages, IngesterLogs, Location, \
    ProjectTemplate,method_template,DatasetDataSource, Project, project_validator, ProjectStates, CreatePage, Method, Party, Dataset, MethodSchema, grant_validator, MethodTemplate
from jcudc24provisioning.views.mint_lookup import MintLookup

from lxml import etree
import os
from jcudc24provisioning.models import DBSession

__author__ = 'casey'

class ReDBoxWraper(object):
    def __init__(self, url, identifier_pattern, ssh_host, ssh_port, tmp_dir, harvest_dir, ssh_username, rsa_private_key=None, ssh_password=None):
        self.url = url
        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.harvest_dir = harvest_dir
        self.ssh_username = ssh_username
        self.rsa_private_key = rsa_private_key
        self.ssh_password = ssh_password
        self.tmp_dir = tmp_dir
        self.identifier_pattern = identifier_pattern

        self.session = DBSession

    def insert(self, project_id=None, dataset_id=None):
        if project_id is None and dataset_id is None:
            raise ValueError("Trying to insert nothing into ReDBox, either project_id or dataset_id needs to be set.")

        if project_id is not None:
            return self.insert_project(project_id)

        if dataset_id is not None:
            return self.insert_dataset(dataset_id)

#    def insert_service(self, dataset_id):
#
#
#
#    def insert_dataset(self, dataset_id):


    def insert_project(self, project_id):
        project = self.session.query(Project).filter_by(id=project_id).first()

        # 1. Create service records.
#        dataset_services_xml = [self.dataset_to_mint_service(dataset.id) for dataset in self.project.datasets]
        # TODO: Upload service csv files to Mint and get mint url and identifier
        service_records = []

        # 2. Create relationships between each service record and it's dataset.

        # 3. Create all dataset records (the project itself creates 1 dataset record).
        project_record = self._prepare_record(self.session.query(Metadata).filter_by(id=project.information.id).first()).to_xml().getroot()

        dataset_metadata = [self._prepare_record(dataset.record_metadata) for dataset in project.datasets if dataset.publish_dataset]
        dataset_records = [metadata.to_xml().getroot() for metadata in dataset_metadata]

        # 4. Add relationships between all dataset records.
        self._add_relationships(project_record, dataset_records)

        # 5. Create the tmp directory
        self._create_working_dir()

        # 6. Write all records (dataset and service) to a tmp directory ready for upload.
        self._write_to_tmp([project_record] + dataset_records + service_records)

        # 7. Upload all files in the
        self._upload_record_files()

        #8. Alert ReDBox that there are new records
        self._alert_redbox()

        #9. Remove the tmp directory
        shutil.rmtree(self.working_dir)

        return True

    def _prepare_record(self, record):
        # Split the FOR and SEO codes into value/label pairs.
        for field_of_research in record.field_of_research:
            field_of_research.field_of_research = field_of_research.field_of_research_label.split(" ")[0]

        for socio_economic_objective in record.socio_economic_objective:
            socio_economic_objective.socio_economic_objective = socio_economic_objective.socio_economic_objective_label.split(" ")[0]

        # Set the redbox identifier
        record.redbox_identifier = self.identifier_pattern + str(record.id)

        # Only update the citation if it is empty
        if record.custom_citation is False:
            self.pre_fill_citation(record)

        # Set the record export date.
        record.record_export_date = datetime.now()

        mint_lookup = MintLookup(None)

        if record.grant is not None:
            mint_grant = mint_lookup.get_from_identifier(record.grant)
            record.grant_number = record.grant.split("/")[-1]
            record.grant_label = mint_grant['rdfs:label']

        for person in record.parties:
            mint_person = mint_lookup.get_from_identifier(person.identifier)

            person.name = str(mint_person['result-metadata']['all']['Honorific'][0]) + " " + str(mint_person['result-metadata']['all']['Given_Name'][0]) \
                                                    + " " + str(mint_person['result-metadata']['all']['Family_Name'][0])
            person.title = mint_person['Honorific']
            person.given_name = mint_person['Given_Name']
            person.family_name = mint_person['Family_Name']
#            person.organisation = mint_person['dc:title']
#            person.organisation_label = mint_person['dc:title']
            person.email = mint_person['Email']
            pass


        return record

    def pre_fill_citation(self, metadata):
       if metadata is None:
           raise ValueError("Updating citation on None metadata")

       # TODO: fill citation data

       # Fill citation fields
       self.project.information.citation_title = self.project.information.project_title
       #            self.project.information.citation_creators = self.project.information.parties  TODO: Citation creators
       self.project.information.citation_edition = None
       self.project.information.citation_publisher = "James Cook University"
       self.project.information.citation_place_of_publication = "James Cook University"
       # Type of Data?
       self.project.information.citation_url = "" # TODO:  CC-DAM Data Link
       self.project.information.citation_context = self.project.information.project_title

    def _write_to_tmp(self, records):
        for record in records:
            identifier = record.xpath("%s" % Metadata.redbox_identifier.key)
            if len(identifier) == 1:
                tmp_file_path = self.working_dir + (identifier[0].text).replace("\\", ".").replace("/", ".") + ".xml"
                f = open(tmp_file_path, 'w')
                f.write((etree.tostring(record.getroottree().getroot(), pretty_print=True)))
            else:
                raise AttributeError("Trying to create ReDBox record with no redbox_identifier set.")

    def _create_working_dir(self):
        # Create a unique directory for this operation
        self.working_dir = self.tmp_dir + ''.join(random.choice(string.letters) for i in range(20)) + os.sep
        while os.path.exists(self.working_dir):
            self.working_dir = self.tmp_dir + ''.join(random.choice(string.letters) for i in range(20)) + os.sep

        os.mkdir(self.working_dir)

    def _upload_record_files(self):
        file_send = SFTPFileSend(self.ssh_host, self.ssh_port, self.ssh_username, password=self.ssh_password, rsa_private_key=self.rsa_private_key)
        file_send.upload_directory(self.working_dir, self.harvest_dir)
        file_send.close()

    def _alert_redbox(self):
        return requests.post(self.url)

    def _add_relationships(self, project_record, dataset_records):
        original_records = {}    # Records what dataset record the relationship came from

        related_parent = self._create_relationship_node(project_record, "isPartOf")

        # Create the relationships for related data
        related_siblings = []
        related_children = []
        for related_record in dataset_records:
            sibling = self._create_relationship_node(related_record, "hasAssociationWith")
            child = self._create_relationship_node(related_record, "hasPart")

            original_records[related_record] = sibling

            related_siblings.append(sibling)
            related_children.append(child)

        # Add all records generated from datassets as related data for the project record.
        related_records = etree.SubElement(project_record, "related_records")
        for child in related_children:
            related_records.append(child)

        for record in dataset_records:
            # Add a data relationship to the project for on dataset records.
            related_records = etree.Element("related_records")
            related_records.append(related_parent)

           # Add data relationships between all datasets within the project.
            for related_record in related_siblings:
               # Don't add a relationship to itself.
                if related_record != original_records[record]:
                    record.append(related_record)


        #            # TODO: This is the related servces fields
        #            "dc:relation.vivo:Service.0.dc:identifier": "some_identifier",
        #            "dc:relation.vivo:Service.0.vivo:Relationship.rdf:PlainLiteral": "isProducedBy",
        #            "dc:relation.vivo:Service.0.vivo:Relationship.skos:prefLabel": "Is produced by:",
        #            "dc:relation.vivo:Service.0.dc:title": "Artificial tree sensor",
        #            "dc:relation.vivo:Service.0.skos:note": "test notes",


    def _create_relationship_node(self, record, relationship_type):
        related_record_node = etree.Element("related_record")

        identifier = etree.SubElement(related_record_node, "identifier")
        identifier.text = unicode(record.xpath("/metadata/%s" % Metadata.redbox_identifier.key))

        relationship = etree.SubElement(related_record_node, "relationship")
        relationship.text = relationship_type

        preflabel = etree.SubElement(related_record_node, "preflabel")
        preflabel.text = "Has association with:"

        title = etree.SubElement(related_record_node, "title")
        title.text = unicode(record.xpath("%s" % Metadata.project_title.key))

        notes = etree.SubElement(related_record_node, "notes")
        notes.text = "Related dataset from the same RDC provisioing project."

        origin = etree.SubElement(related_record_node, "origin")
        origin.text = "on"

        publish = etree.SubElement(related_record_node, "publish")
        publish.text = "on"

        return  related_record_node

#    def dataset_to_mint_service_csv(self):
#        service_csv = ""
#
#        # TODO: Dataset to mint service csv mappings
#
#        return service_csv
#