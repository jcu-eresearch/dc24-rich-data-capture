import ast
import copy
import logging
from beaker.cache import cache_region
from jcudc24ingesterapi.authentication import CredentialsAuthentication
from jcudc24ingesterapi.ingester_platform_api import IngesterPlatformAPI
from jcudc24ingesterapi.ingester_platform_api import UnitOfWork
import jcudc24ingesterapi
from jcudc24provisioning.models.project import Location, LocationOffset, MethodSchema, Base, Project, Region, Dataset, DBSession, Method, MethodSchemaField, PullDataSource,FormDataSource, PushDataSource, DatasetDataSource, SOSDataSource
from jcudc24ingesterapi.schemas.data_types import DateTime, FileDataType, Integer, String, Double, Boolean
from jcudc24ingesterapi.models.sampling import PeriodicSampling

__author__ = 'Casey Bajema'

logger = logging.getLogger(__name__)

def model_id_listener(self, attr, var):
    if attr == "_id":
        self.provisioning_model.dam_id = var
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

#    @cache_region('long_term') # TODO: Check that this is secure
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
            return super(IngesterAPIWrapper, self).post(model)

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
    # TODO: Update all processing to add listeners to the ingesterapi models to propagate the id changes to the provisioning interface models (on commit)
    def process_model(self, model, command, work):
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
        assert isinstance(model, LocationOffset), "Invalid location offset: " + str(model)

        new_location_offset = jcudc24ingesterapi.models.locations.LocationOffset(
            model.x,
            model.y,
            model.z
        )
        return new_location_offset

    def process_region(self, model, command, work):
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
        assert isinstance(model, MethodSchema), "Invalid schema: " + str(model)
        if model.dam_id is not None and model.dam_id >= 0:
            # Schema's cannot be changed TODO: Update this to test if shema has changed, if it has - add a new schema
            return model.dam_id

        if True: # TODO: If the data entries don't need offsets
            new_schema = jcudc24ingesterapi.schemas.data_entry_schemas.DataEntrySchema(model.name)
        else:
            pass #TODO: new_schema = jcudc24ingesterapi.schemas.data_entry_schemas.OffsetDataEntrySchema()

        # Set the schema parents/extends
        new_schema.extends = []
        for parent in model.parents:
            if parent.dam_id is not None and parent.dam_id >= 0:
                new_schema.extends.append(int(parent.dam_id))
            else:
                new_parent = self.process_schema(parent, work.post, work)
                new_schema.extends.append(int(new_parent))

        for field in model.custom_fields:
            if field.type == 'integer':
                schema_field =  Integer(field.name, field.description, field.units)
            elif field.type == 'decimal':
                schema_field =  Double(field.name, field.description, field.units)
            elif field.type == 'text_input' or field.type == 'text_area' or field.type == 'select' or\
                 field.type == 'radio' or field.type == 'website' or field.type == 'email'\
                 or field.type == 'phone' or field.type == 'hidden':
                schema_field =  String(field.name, field.description, field.units)
            elif field.type == 'checkbox':
                schema_field =  Boolean(field.name, field.description, field.units)
            elif field.type == 'file':
                schema_field =  FileDataType(field.name, field.description, field.units)
            elif field.type == 'date':
                schema_field =  DateTime(field.name, field.description, field.units)
            else:
                assert True, "Unknown field typ: " + field.type

            new_schema.addAttr(schema_field)


        if model.dam_id is not None:
            new_schema.id = int(model.dam_id)

        model.dam_id = command(new_schema)
        new_schema.provisioning_model = model
        new_schema.set_listener(model_id_listener)
        return new_schema.id

    def process_project(self, project, command, work):
        assert isinstance(project, Project),"Trying to add a project with a model of the wrong type."

        datasets = []

        for dataset in project.datasets:
            new_dataset = self.process_dataset(dataset, command, work)
            datasets.append(new_dataset)

        return datasets

    def process_dataset(self, model, command, work):
        assert isinstance(model, Dataset),"Trying to add a project with a model of the wrong type."

        new_dataset = jcudc24ingesterapi.models.dataset.Dataset()

        #            new_dataset.processing_script = dataset.custom_processor_script - Moved to datasource
        new_dataset.redbox_uri = None   # TODO: Add redbox link
        new_dataset.enabled = True
        new_dataset.descripion = model.description

        # Add the location
        first_location_found = False
        for location in model.dataset_locations:
            if not first_location_found and location.is_point():
                first_location_found = True
                try:
                    new_dataset.location = self.process_model(location, command, work)
                except Exception as e:
                    logger.exception("Failed to add/update location: %s for dataset: %s" % (location.name, model.title))
                    raise ValueError("Failed to add/update location: %s for dataset: %s, error: %s" % (location.name, model.title, e))
            else:
                pass # TODO: Discuss regions when we get there - there is currently only 1 region in a dataset (this will fail if run)

        # Add the location offset if it is set
        if model.location_offset is not None:
            new_dataset.location_offset = self.process_model(model.location_offset, command, work)

        # Add the data_entry schema to the dataset
        method = self.session.query(Method).filter_by(id=model.method_id).first()
        if method is None:
            raise ValueError("Trying to provision a dataset that has no associated method.  Try deleting and re-creating the dataset.")

        try:
            new_dataset.schema = self.process_model(method.data_type, command, work)
        except Exception as e:
            logger.exception("Failed to add/update data schema for method: %s" % (method.method_name))
            raise ValueError("Failed to add/update data schema for method: %s, Error: %s" % (method.method_name, e))

        # Add the data source configuration
        if method.data_source is None:
            raise ValueError("Trying to provision a dataset with an undefined data source type.  Go back to the methods step and select the data source, then configure the data source in the datasets step.")

        if method.data_source == FormDataSource.__tablename__:
            if model.form_data_source is None:
                raise ValueError("Trying to provision a dataset with no data source.  Go back to the dataset step and configure the data source.")
            data_source = jcudc24ingesterapi.models.data_sources.FormDataSource()
            # TODO: Update datasource configuration
        if method.data_source == PullDataSource.__tablename__:
            if model.pull_data_source is None:
                raise ValueError("Trying to provision a dataset with no data source.  Go back to the dataset step and configure the data source: %s" % model.title)

            # Create the sampling
            sampling_object = None
            if PullDataSource.periodic_sampling.key in model.pull_data_source.selected_sampling:
                try:
                    sampling_object = jcudc24ingesterapi.models.sampling.PeriodicSampling(int(model.pull_data_source.periodic_sampling))
                except TypeError:
                    logger.exception("Trying to create a periodic sampler with invalid rate: %s for %s" % (model.pull_data_source.periodic_sampling, model.title))
                    raise ValueError("Trying to create a periodic sampler with invalid rate: %s for %s" % (model.pull_data_source.periodic_sampling, model.title))

            elif PullDataSource.cron_sampling.key in model.pull_data_source.selected_sampling:
                try:
                    sampling_object = jcudc24ingesterapi.models.sampling.CronSampling(str(model.pull_data_source.cron_sampling))
                except TypeError:
                    logger.exception("Trying to create a cron sampler with an invalid cron string: %s for %s" % (model.pull_data_source.cron_sampling, model.title))
                    raise ValueError("Trying to create a cron sampler with an invalid cron string: %s for %s" % (model.pull_data_source.cron_sampling, model.title))

            elif PullDataSource.custom_sampling_desc.ca_group_start in model.pull_data_source.selected_sampling:
                try:
                    sampling_object = jcudc24ingesterapi.models.sampling.CustomSampling(model.pull_data_source.custom_sampling_script)
                except TypeError:
                    logger.exception("Trying to create a custom sampler with invalid script handle: %s" % model.pull_data_source.custom_sampling_script)
                    raise ValueError("Trying to create a custom sampler with invalid script handle: %s" % model.pull_data_source.custom_sampling_script)

            print "SAMPLIING OBJECT: %s" % sampling_object

            # Create the data source
            try:
                print "URI: %s" % model.pull_data_source.uri
                data_source_field = self.session.query(MethodSchemaField).filter_by(id=model.pull_data_source.file_field).first()
                data_source = jcudc24ingesterapi.models.data_sources.PullDataSource(
                    url=model.pull_data_source.uri,
                    field=data_source_field.name,
#                    pattern=model.pull_data_source.filename_pattern,
#                    mime_type=data_source_field.mime_type,
#                    processing_script=model.pull_data_source.custom_processor_script,
                    sampling=sampling_object,
                    recursive=True
                )

                if model.pull_data_source.custom_processor_script is not None:
                    try:
                        script_path = ast.literal_eval(model.dataset_data_source.custom_processor_script)['filepath']
                        with open(script_path) as f:
                            script = f.read()
                            if model.pull_data_source.custom_processing_parameters is not None:
                                params = model.pull_data_source.custom_processing_parameters.split(",")
                                for param in params:
                                    param.strip()
                                script = script % tuple(params)
                            data_source.processing_script = script
                    except IOError as e:
                        logger.exception("Could not read custom processing script for dataset: %s" % model.title)
                        raise ValueError("Could not read custom processing script for dataset: %s" % model.title)
            except Exception as e:
                logger.exception("Trying to create an ingester pull data source with invalid parameters: %s, Error: %s" % (model.title, e))
                raise ValueError("Trying to create an ingester pull data source with invalid parameters: %s, Error: %s" % (model.title, e))

        if method.data_source == PushDataSource.__tablename__:
            if model.push_data_source is None:
                raise ValueError("Trying to provision a dataset with no data source.  Go back to the dataset step and configure the data source: %s" % model.title)
            data_source = jcudc24ingesterapi.models.data_sources.PushDataSource()
            # TODO: Update datasource configuration
        if method.data_source == SOSDataSource.__tablename__:
            if model.sos_data_source is None:
                raise ValueError("Trying to provision a dataset with no data source.  Go back to the dataset step and configure the data source: %s" % model.title)
            data_source = jcudc24ingesterapi.models.data_sources.SOSDataSource()
            # TODO: Update datasource configuration
        if method.data_source == DatasetDataSource.__tablename__:
            if model.dataset_data_source is None:
                raise ValueError("Trying to provision a dataset with no data source.  Go back to the dataset step and configure the data source: %s" % model.title)
            try:
                observed_dataset = self.session.query(Dataset).filter_by(id=model.dataset_data_source.dataset_data_source_id).first()
                if observed_dataset is None:
                    raise ValueError("The selected source dataset doesn't exist.  Go back to the datasets step and fix %s." % model.title)

                try:
                    source_dataset_id = self.process_dataset(observed_dataset, work.post, work)
                except Exception as e:
                    logger.exception("Failed to add/update source dataset to dam: %s, Error: %s for dataset: %s" % (observed_dataset.title, e, model.title))
                    raise ValueError("Failed to add/update source dataset to dam: %s, Error: %s for dataset: %s" % (observed_dataset.title, e, model.title))

                data_source = jcudc24ingesterapi.models.data_sources.DatasetDataSource(
                    int(source_dataset_id),
                )
                if model.dataset_data_source.custom_processor_script is not None:
                    try:
                        script_path = ast.literal_eval(model.dataset_data_source.custom_processor_script)['filepath']
                        with open(script_path) as f:
                            script = f.read()
                            if model.dataset_data_source.custom_processing_parameters is not None:
                                params = model.dataset_data_source.custom_processing_parameters.split(",")
                                for param in params:
                                    param.strip()
                                script = script % tuple(params)
                            data_source.processing_script = script
                    except IOError as e:
                        logger.exception("Could not read custom processing script for dataset: %s" % model.title)
                        raise ValueError("Could not read custom processing script for dataset: %s" % model.title)
            except TypeError:
                logger.exception("Trying to create an ingester dataset data source with invalid parameters: %s" % model.title)
                raise ValueError("Trying to create an ingester dataset data source with invalid parameters: %s" % model.title)


        new_dataset.data_source = data_source

        if model.redbox_uri is not None:
            new_dataset.redbox_uri = model.redbox_uri


        if model.dam_id is not None:
            new_dataset.id = int(model.dam_id)

        model.dam_id = command(new_dataset)
        new_dataset.provisioning_model = model
        new_dataset.set_listener(model_id_listener)
        return new_dataset.id

    def process_data_entry(self, model, command, work):
        pass # TODO: data_entries

    def process_metadata(self, model, command, work):
        pass # TODO: metadata






