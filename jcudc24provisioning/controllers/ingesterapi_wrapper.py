"""
Wraps the jcu.dc24.ingesterapi/ingester_platform_api.py/IngesterPlatformAPI to provide transparent mappings of the
provisioning interface database models:
- If the api methods are called with ingesterapi models the IngesterPlatformAPI is called directly.
- If the api methods are called with provisioning interface models a unit of work is created and the process_model()
  method is called.  process_model calls the associated processing method which converts the provisioning interface
  model into ingesterapi model(s) and inserts/updates/deletes/posts them.
- To change how a provisioning interface model integrates with the ingester platform change the relevent proces method.
- On insert, provisioning interface dam_id's are updated when the ingesterapi model's listener is called.
"""

import ast
import copy
import logging
from beaker.cache import cache_region
from jcudc24ingesterapi.schemas.data_entry_schemas import DataEntrySchema
import jcudc24provisioning
from jcudc24ingesterapi.authentication import CredentialsAuthentication
from jcudc24ingesterapi.ingester_platform_api import IngesterPlatformAPI, Marshaller
from jcudc24ingesterapi.ingester_platform_api import UnitOfWork
import jcudc24ingesterapi
from jcudc24provisioning.models import DBSession, Base
from jcudc24provisioning.models.project import Location, LocationOffset, MethodSchema, Project, Region, Dataset, Method, MethodSchemaField, PullDataSource,FormDataSource, PushDataSource, DatasetDataSource, SOSScraperDataSource, Metadata
from jcudc24ingesterapi.schemas.data_types import DateTime, FileDataType, Integer, String, Double, Boolean
from jcudc24ingesterapi.models.sampling import PeriodicSampling
import os

__author__ = 'Casey Bajema'

logger = logging.getLogger(__name__)

def model_id_listener(self, attr, var):
    """
    This is an implementation of ingesterapi listener that is added to models before they are inserted/posted.  This
    provides functionality to update the dam_id held in the provisioning interface models.

    :param attr: attriburte that has been changed
    :param var: the value that the attribute has been set to.
    :return: None
    """
    if attr == "_id":
        self.provisioning_model.dam_id = var

        if isinstance(self, jcudc24ingesterapi.models.dataset.Dataset):
            session = DBSession
            metadata = session.query(Metadata).filter_by(dataset_id=self.provisioning_model.id)
            config = jcudc24provisioning.global_settings
            metadata.ccdam_identifier = config.get("ingesterapi.portal_url") + str(var)

#        print "Model id set: " + str(var) + " : " + str(self.provisioning_model)



class IngesterAPIWrapper(IngesterPlatformAPI):
    """
        Wrapper for the ingesterapi to specialise it for the provisioning interface:
        * Transparent conversion between provisioning interface models and ingesterapi data models
        * Added functionality to ingesterapi functions to auto generate units of work from full provisioning interface models, or just commit pre-made ingester api models directly.
        * Transparent checking for pre-existence of ingesterapi data models
        * Transparent updating/checking of provisioning schemas vs ingester schemas
        * Persistent connection using beaker sessions
    """

    def __init__(self, service_url, auth=None):
        """
            Call parent constructor, but also add cacheing of the connection
        """
        super(IngesterAPIWrapper, self).__init__(service_url, auth)
        self.session = DBSession

    def post(self, model, recursive=False):
        """
        Create a new entry using the passed in object, the entry type will be based on the objects type.

        This implementation extends the base functionality of the ingester platform api by transparently converting
        provisioning interface models to ingester api models, and back again for return.

        :param recursive - Indicate if this method should use it's knowledge of the provisioning interface to automatically use units of work to commit the provide model as well as the models it contains.
        :param provisioning interface object: Insert a new record if the ID isn't set, if the ID is set update the existing record.
        :return: The object passed in with the ID field set.
        """
        if hasattr(model, "__tablename__"):
            work = self.createUnitOfWork()
            self.process_model(model, work.post, work)
            logger.info("Project processed, exporting to ingesterplatform: %s", model)


#            marshaller = Marshaller()
#
#            schemas = []
#            locations = []
#            datasets = []
#            for item in work.to_insert:
#                if isinstance(item, jcudc24ingesterapi.schemas.data_entry_schemas.DataEntrySchema):
#                    schemas.append(item)
#                if isinstance(item, jcudc24ingesterapi.models.locations.Location):
#                    locations.append(item)
#                if isinstance(item, jcudc24ingesterapi.models.dataset.Dataset):
#                    datasets.append(item)
#
#            for schema in schemas:
#                print "Adding schema: %s" % marshaller.obj_to_dict(schema)
#                schema.id = None
#                schema.version = 1
#                super(IngesterAPIWrapper, self).post(schema)
#
#            for location in locations:
#                print "Adding location: %s" % marshaller.obj_to_dict(location)
#                location.id = None
#                super(IngesterAPIWrapper, self).post(location)
#
#            for dataset in datasets:
#                print "Adding location: %s" % marshaller.obj_to_dict(dataset)
#                dataset.id = None
#                super(IngesterAPIWrapper, self).post(dataset)



            work.commit()
            return model
        else:
            return super(IngesterAPIWrapper, self).post(model)


    def insert(self, model):
        """
        Create a new entry using the passed in object, the entry type will be based on the objects type.

        This implementation extends the base functionality of the ingester platform api by transparently converting
        provisioning interface models to ingester api models, and back again for return.

        :param provisioning interface model: If the objects ID is set an exception will be thrown.
        :return: The object passed in with the ID field set.
        """
        if hasattr(model, "__tablename__"):
            work = self.createUnitOfWork()
            self.process_model(model, work.insert, work)
            work.commit()
            return model
        else:
            return super(IngesterAPIWrapper, self).insert(model)

    def update(self, model):
        """
        Update an entry using the passed in object, the entry type will be based on the objects type.

        This implementation extends the base functionality of the ingester platform api by transparently converting
        provisioning interface models to ingester api models, and back again for return.

        :param provisioning interface model: If the passed in object doesn't have it's ID set an exception will be thrown.
        :return: The updated object (eg. :return == provisioning object should always be true on success).
        """
        if hasattr(model, "__tablename__"):
            work = self.createUnitOfWork()
            self.process_model(model, work.update, work)
            work.commit()
            return model
        else:
            return super(IngesterAPIWrapper, self).update(model)

    def delete(self, model):
        """
        Delete an entry using the passed in object, the entry type will be based on the objects type.

        This implementation extends the base functionality of the ingester platform api by transparently converting
        provisioning interface models to ingester api models, and back again for return.

        :param provisioning interface model:  All fields except the objects ID will be ignored.
        :return: The object that has been deleted, this should have all fields set.
        """

        if hasattr(model, "__tablename__"):
            work = self.createUnitOfWork()
            self.process_model(model, work.delete, work)
            work.commit()
            return model
        else:
            return super(IngesterAPIWrapper, self).delete(model)

    #---------------Provisioning interface specific functions for processing the models-------------
    def process_model(self, model, command, work):
        """
        Provides tranaparency to the ingesterapi methods so that they can be called with any provisioning model and it
        is mapped to the relevant process method below.

        :param model: The model to process, the model must be a valid provisioning interface model.
        :param command: What method of the ingesterapi has been called (eg. is this a delete or post call?)
        :param work: Unit of work that all api calls should be added to (Unit of work means the transaction is success/fail).
        :return: ingesterapi model id(s) or model(s) - depending if the ingesterapi model type has an ID.
        """
        assert hasattr(model, "__tablename__"), "Trying to process a invalid provisioning model"
        assert hasattr(command, "func_name") and hasattr(UnitOfWork, command.func_name), "Trying to process a model with an invalid command"

        new_model = None

        if isinstance(model, Project):
            new_model = self.process_project(model, command, work)
        elif isinstance(model, Dataset):
            new_model = self.process_dataset(model, command, work)
        elif isinstance(model, Location):
            new_model = self.process_location(model, command, work)
        elif isinstance(model, LocationOffset):
            new_model = self.process_location_offset(model, command, work)
        elif isinstance(model, Region):
            new_model = self.process_region(model, command, work)
        elif isinstance(model, MethodSchema):
            new_model = self.process_schema(model, command, work)
        else:
            raise ValueError("Unknown provisioning interface model: " + str(model))

#        if new_model is not None:
#            if isinstance(new_model, list):
#                for a_model in new_model:
#                    a_model.provisioning_model = model
#                    a_model.set_listener(model_id_listener)
#            else:
#                new_model.provisioning_model = model
#                new_model.set_listener(model_id_listener)

        return new_model


    def process_location(self, model, command, work):
        """
        Convert the provisioning interface location model into an ingesterapi location model.

        :param model: The model to process/convert
        :param command: How the ingesterapi should be called with the model (eg. delete/post/...)
        :param work: Unit of work that the command will be called on with the created ingesterapi model.
        :return: Created ingesterapi model
        """
        assert isinstance(model, Location), "Invalid location: " + str(model)
        assert model.location[:5] == "POINT", "Provided location is not a point (only points can be used for dataset or data_entry locations).  Value: " + model.location

        new_location = jcudc24ingesterapi.models.locations.Location(
            latitude = model.get_latitude(),
            longitude = model.get_longitude(),
            location_name = model.name,
            elevation = model.elevation
        )
        if model.dam_id is not None:
            new_location.id = int(model.dam_id)

        model.dam_id = command(new_location)
        new_location.provisioning_model = model
        new_location.set_listener(model_id_listener)
        return new_location.id

    def process_location_offset(self, model, command, work):
        """
        Convert the provisioning interface location offset model into an ingesterapi location offset model.

        :param model: The model to process/convert
        :param command: How the ingesterapi should be called with the model (eg. delete/post/...)
        :param work: Unit of work that the command will be called on with the created ingesterapi model.
        :return: Created ingesterapi model
        """
        assert isinstance(model, LocationOffset), "Invalid location offset: " + str(model)

        new_location_offset = jcudc24ingesterapi.models.locations.LocationOffset(
            model.x,
            model.y,
            model.z
        )
        return new_location_offset

    def process_region(self, model, command, work):
        """
        Convert the provisioning interface region model into an ingesterapi model.

        :param model: The model to process/convert
        :param command: How the ingesterapi should be called with the model (eg. delete/post/...)
        :param work: Unit of work that the command will be called on with the created ingesterapi model.
        :return: Created ingesterapi model
        """
        assert isinstance(model, Location), "Invalid location: " + str(model)
        assert not model.location[:5] == "POINT", "Provided location is a point (It doesn't make sense for a region to be a single point).  Value: " + model.location

        region = jcudc24ingesterapi.models.locations.Region(
            region_name = model.name,
            region_points = model.get_points()
        )

        if model.dam_id is not None:
            region.id = int(model.dam_id)

        model.dam_id = command(region)
        region.provisioning_model = model
        region.set_listener(model_id_listener)
        return region

    def process_schema(self, model, command, work):
        """
        Convert the provisioning interface schema model into an ingesterapi model and call the ingesterapi command with it.

        :param model: The model to process/convert
        :param command: How the ingesterapi should be called with the model (eg. delete/post/...)
        :param work: Unit of work that the command will be called on with the created ingesterapi model.
        :return: ID of the created ingesterapi model
        """
        assert isinstance(model, MethodSchema), "Invalid schema: " + str(model)
        if model.dam_id is not None:# and model.dam_id >= 0:
            # Schema's cannot be changed
            return model.dam_id

        if model.schema_type == jcudc24ingesterapi.schemas.data_entry_schemas.DataEntrySchema.__xmlrpc_class__:
            new_schema = jcudc24ingesterapi.schemas.data_entry_schemas.DataEntrySchema(model.name)
        elif model.schema_type == jcudc24ingesterapi.schemas.metadata_schemas.DataEntryMetadataSchema.__xmlrpc_class__:
            new_schema = jcudc24ingesterapi.schemas.metadata_schemas.DataEntryMetadataSchema(model.name)
        if model.schema_type == jcudc24ingesterapi.schemas.metadata_schemas.DatasetMetadataSchema.__xmlrpc_class__:
            new_schema = jcudc24ingesterapi.schemas.metadata_schemas.DatasetMetadataSchema(model.name)

        # Set the schema parents/extends
        new_schema.extends = []
        for parent in model.parents:
            if parent.dam_id is not None:# and parent.dam_id >= 0:
                new_schema.extends.append(int(parent.dam_id))
            else:
                new_parent = self.process_schema(parent, work.post, work)
                new_schema.extends.append(int(new_parent))

        for field in model.custom_fields:
            if field.type == 'integer':
                schema_field =  Integer(field.internal_name, field.description, field.units)
            elif field.type == 'decimal':
                schema_field =  Double(field.internal_name, field.description, field.units)
            elif field.type == 'text_input' or field.type == 'text_area' or field.type == 'select' or\
                 field.type == 'radio' or field.type == 'website' or field.type == 'email'\
                 or field.type == 'phone' or field.type == 'hidden':
                schema_field =  String(field.internal_name, field.description, field.units)
            elif field.type == 'checkbox':
                schema_field =  Boolean(field.internal_name, field.description, field.units)
            elif field.type == 'file':
                schema_field =  FileDataType(field.internal_name, field.description, field.units)
            elif field.type == 'date':
                schema_field = DateTime(field.internal_name, field.description, field.units)
            else:
                raise ValueError("Unknown field typ: " + field.type)

            new_schema.addAttr(schema_field)


        if model.dam_id is not None:
            new_schema.id = int(model.dam_id)

        model.dam_id = command(new_schema)
        new_schema.provisioning_model = model
        new_schema.set_listener(model_id_listener)
        return new_schema.id

    def process_project(self, project, command, work):
        """
        Convert the provisioning interface project model into ingesterapi dataset model(s) and call the ingesterapi
        command with them.

        This method basically calls process_dataset with each dataset associated with the project.

        :param model: The model to process/convert
        :param command: How the ingesterapi should be called with the model (eg. delete/post/...)
        :param work: Unit of work that the command will be called on with the created ingesterapi model.
        :return: ID of the created ingesterapi model
        """
        assert isinstance(project, Project),"Trying to add a project with a model of the wrong type."

        datasets = []

        for dataset in project.datasets:
            new_dataset = self.process_dataset(dataset, command, work)
            datasets.append(new_dataset)

        return datasets

    def process_dataset(self, model, command, work):
        """
        Convert the provisioning interface dataset into an ingesterapi dataset and call the ingesterapi command with it.

        :param model: The model to process/convert
        :param command: How the ingesterapi should be called with the model (eg. delete/post/...)
        :param work: Unit of work that the command will be called on with the created ingesterapi model.
        :return: ID of the created ingesterapi model
        """
        assert isinstance(model, Dataset),"Trying to add a project with a model of the wrong type."

        # Get the datasets method.
        method = self.session.query(Method).filter_by(id=model.method_id).first()
        if method is None:
            raise ValueError("Trying to provision a dataset that has no associated method.  Try deleting and re-creating the dataset.")

        # Create the dataset and setup standard fields.
        new_dataset = jcudc24ingesterapi.models.dataset.Dataset()
        new_dataset.enabled = True
        new_dataset.description = model.record_metadata.project_title

        # Set the metadata record address
        if model.record_metadata is not None and model.record_metadata.redbox_uri is not None:
            new_dataset.redbox_uri = model.record_metadata.redbox_uri

        # Add the location and optionally an offset to that location.
        self._set_dataset_locations(new_dataset, model, work, command)

        # Add the data source to this dataset.
        new_dataset.data_source = self._create_data_source(model, method)

        # Add the DataEntrySchema for this dataset
        try:
            if method.data_type.dam_id is None:
                new_dataset.schema = int(self.process_model(method.data_type, command, work))
            else:
                new_dataset.schema = int(method.data_type.dam_id)
        except Exception as e:
            logger.exception("Failed to add/update data schema for method: %s" % (method.method_name))
            raise ValueError("Failed to add/update data schema for method: %s, Error: %s" % (method.method_name, e))


        # Set the ID and add the new dataset to the unit of work
        if model.dam_id is not None:
            new_dataset.id = int(model.dam_id)

        model.dam_id = command(new_dataset)
        new_dataset.provisioning_model = model
        new_dataset.set_listener(model_id_listener)
        model.disabled = False
        return new_dataset.id


    def _set_dataset_locations(self, dataset, provisioning_dataset, work, command):
        """
        Break the dataset location processing out to make the code more legible.  This method finds the first point
        location and adds it to the ingesterapi dataset.

        It also adds the location offset to the ingesterapi dataset.

        :param dataset: Ingesterapi dataset model
        :param provisioning_dataset: Provisioning interface dataset model
        :param work: Unit of work that holds all ingesterapi commands for this transaction.
        :param command: Type of ingesterapi call that is being used.
        :return: None
        """
        first_location_found = False
        for location in provisioning_dataset.dataset_locations:
            if not first_location_found and location.is_point():
                first_location_found = True
                try:
                    if location.dam_id is None:
                        dataset.location = self.process_model(location, command, work)
                    else:
                        dataset.location = int(location.dam_id)
                except Exception as e:
                    logger.exception("Failed to add/update location: %s for dataset: %s" % (location.name, provisioning_dataset.record_metadata.project_title))
                    raise ValueError("Failed to add/update location: %s for dataset: %s, error: %s" % (location.name, provisioning_dataset.record_metadata.project_title, e))
            else:
                pass # TODO: Discuss regions when we get there - there is currently only 1 region in a dataset (this will fail if run)

        # Add the location offset if it is set
        if provisioning_dataset.location_offset is not None:
            dataset.location_offset = self.process_model(provisioning_dataset.location_offset, command, work)


    def _create_data_source(self, provisioning_dataset, method=None):
        """
        Break the data source processing out of process_dataset to make the code more legible.  This method finds the
        type of data source and creates the ingesterapi datasource object.

        :param provisioning_dataset: Provisioning interface dataset model
        :param method: Provisioning interface model associated with this dataset.
        :return: Created ingesterapi datasource model.
        """
        try:
            if method is None:
                method = provisioning_dataset.method

            # Create the data source with type specific configurations.
            data_source = None
            provisioning_data_source = None
            if method.data_source == FormDataSource.__tablename__:
                provisioning_data_source = provisioning_dataset.form_data_source
                data_source = jcudc24ingesterapi.models.data_sources.FormDataSource()

            elif method.data_source == PullDataSource.__tablename__:
                provisioning_data_source = provisioning_dataset.pull_data_source
                data_file = self.session.query(MethodSchemaField).filter_by(id=provisioning_data_source.data_file).first()
                data_source = jcudc24ingesterapi.models.data_sources.PullDataSource(
                    mime_type=data_file.units,
                    pattern = provisioning_data_source.filename_pattern,
                    recursive=True
                )

            elif method.data_source == SOSScraperDataSource.__tablename__:
                provisioning_data_source = provisioning_dataset.sos_scraper_data_source
                data_source = jcudc24ingesterapi.models.data_sources.SOSScraperDataSource(
                    variant=provisioning_data_source.variant,
                    version=provisioning_data_source.version,
                )

            elif method.data_source == PushDataSource.__tablename__:
                provisioning_data_source = provisioning_dataset.push_data_source
                data_source = jcudc24ingesterapi.models.data_sources.PushDataSource()

            elif method.data_source == DatasetDataSource.__tablename__:
                provisioning_data_source = provisioning_dataset.dataset_data_source

                observed_dataset = self.session.query(Dataset).filter_by(id=provisioning_data_source.dataset_data_source_id).first()
                if observed_dataset is None:
                    raise ValueError("The selected source dataset doesn't exist.  Go back to the datasets step and fix %s." % provisioning_dataset.record_metadata.project_title)

                try:
                    if observed_dataset.dam_id is None:
                        source_dataset_id = self.process_dataset(observed_dataset, work.post, work)
                    else:
                        source_dataset_id = observed_dataset.dam_id
                except Exception as e:
                    logger.exception("Failed to add/update source dataset to dam: %s, Error: %s for dataset: %s" % (observed_dataset.name, e, provisioning_dataset.record_metadata.project_title))
                    raise ValueError("Failed to add/update source dataset to dam: %s, Error: %s for dataset: %s" % (observed_dataset.name, e, provisioning_dataset.record_metadata.project_title))

                data_source = jcudc24ingesterapi.models.data_sources.DatasetDataSource(int(source_dataset_id))

            if hasattr(provisioning_data_source, "uri"):
                data_source.url = provisioning_data_source.uri

            if hasattr(data_source, "field"):
                data_file = self.session.query(MethodSchemaField).filter_by(id=provisioning_data_source.data_file).first()
                data_source.field = data_file.internal_name


            # Add the processing script
            script = None
            if hasattr(provisioning_data_source, 'custom_processor') and provisioning_data_source.custom_processor is not None:
                script = self._create_custom_processing_script(provisioning_data_source.custom_processor)
                data_source.processing_script = script


            # Add the sampling
            try:
                sampling_object = None
                if hasattr(provisioning_data_source, 'periodic_sampling'):
                        sampling_object = jcudc24ingesterapi.models.sampling.PeriodicSampling(int(provisioning_data_source.periodic_sampling*60000))
                        data_source.sampling = sampling_object
            except TypeError:
                logger.exception("Trying to create a periodic sampler with invalid rate: %s for %s" % (provisioning_data_source, provisioning_dataset.record_metadata.project_title))
                raise ValueError("Trying to create a periodic sampler with invalid rate: %s for %s" % (provisioning_data_source, provisioning_dataset.record_metadata.project_title))

            return data_source

        except Exception as e:
            logger.exception("Trying to create an ingester data source with invalid parameters: %s, Error: %s" % (provisioning_dataset.record_metadata.project_title, e))
            raise ValueError("Trying to create an ingester data source with invalid parameters: %s, Error: %s" % (provisioning_dataset.record_metadata.project_title, e))

    def _create_custom_processing_script(self, custom_processor):
        """
        Break the custom processing script processing out of process_dataset to make the code more legible.  This method
        finds the gets the script if there is one and processes any script parameters.

        :param custom_processor: The custom processor file to read as a string and process parameters into.
        :return: Processing script as a string.
        """
        script = None
        try:
            script_path = custom_processor.custom_processor_script
            with open(script_path) as f:
                script = f.read()
                if custom_processor.custom_processing_parameters is not None:
                    temp_params = [param.strip() for param in custom_processor.custom_processing_parameters.split(",")]
                    named_params = {'args': custom_processor.custom_processing_parameters}
                    unnamed_params = []
                    for param in temp_params:
                        if '=' in param:
                            param_parts = param.split("=")
                            named_params[param_parts[0]] = param_parts[1]
                        else:
                            unnamed_params.append(param)

                    try:
                        script = script.format(*unnamed_params, **named_params)
                    except KeyError as e:
                        raise ValueError("Invalid custom processing parameters for {}".format(custom_processor.custom_processor_script))
        except IOError as e:
            logger.exception("Could not read custom processing script: %s" % custom_processor.custom_processor_script)
            raise ValueError("Could not read custom processing script: %s" % custom_processor.custom_processor_script)

        return script
