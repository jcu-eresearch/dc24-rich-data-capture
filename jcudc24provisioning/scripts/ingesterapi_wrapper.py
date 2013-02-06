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
        return new_location

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

        if True: # TODO: If the data entries don't need offsets
            new_schema = jcudc24ingesterapi.schemas.data_entry_schemas.DataEntrySchema()
        else:
            pass #TODO: new_schema = jcudc24ingesterapi.schemas.data_entry_schemas.OffsetDataEntrySchema()

        # Set the schema parents/extends
        extends = []
        for parent in model.parents:
            if parent.dam_id is not None and parent.dam_id >= 0:
                extends.append(parent.dam_id)
            else:
                new_parent = self.process_schema(parent, work.post, work)
                extends.append(new_parent.id)

        new_schema.extends = extends

        new_schema.name = model.name

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
        return new_schema

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

        if model.dam_id is not None:
            new_dataset.id = int(model.dam_id)  # This will be None if it is new (Should always be the case)
        #            new_dataset.processing_script = dataset.custom_processor_script - Moved to datasource
        new_dataset.redbox_uri = None   # TODO: Add redbox link
        new_dataset.enabled = True
        new_dataset.descripion = model.description

        # Add the location
        first_location_found = False
        for location in model.dataset_locations:
            if not first_location_found and location.is_point():
                first_location_found = True
                if location.dam_id is not None and location.dam_id >= 0:
                    new_dataset.location = int(location.dam_id)
#                    print "pervious location used: %s" + str(new_dataset.location)
                else:
                    new_dataset.location = self.process_model(location, command, work).id
#                    print "new location added: %s" + str(new_dataset.location)
            else:
                pass # TODO: Discuss regions when we get there - there is currently only 1 region in a dataset (this will fail if run)
#                if location.dam_id is None:
#                    new_dataset.regions.append(self.process_model(location, command)).id
#                else:
#                    new_dataset.regions.append(location.dam_location_id)

        # Add the location offset if it is set
        if model.location_offset is not None:
            new_dataset.location_offset = self.process_model(model.location_offset, command, work)

        # Add the data_entry schema to the dataset
        method = self.session.query(Method).filter_by(id=model.method_id).first()
        if method is None:
            raise ValueError("Trying to provision a dataset that has no associated method.  Try deleting and re-creating the dataset.")

        if method.data_type.dam_id is not None and method.data_type.dam_id >= 0:
            new_dataset.schema = int(method.data_type.dam_id)
        else:
            new_dataset.schema = self.process_model(method.data_type, command, work).id

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
                raise ValueError("Trying to provision a dataset with no data source.  Go back to the dataset step and configure the data source.")

            # Create the sampling
            sampling_object = None
            if PullDataSource.periodic_sampling.key in model.pull_data_source.selected_sampling:
                try:
                    sampling_object = jcudc24ingesterapi.models.sampling.PeriodicSampling(int(model.pull_data_source.periodic_sampling))
                except TypeError:
                    logger.exception("Trying to create a periodic sampler with invalid rate: %s" % model.pull_data_source.periodic_sampling)
                    return None
            elif PullDataSource.cron_sampling.key in model.pull_data_source.selected_sampling:
                try:
                    sampling_object = jcudc24ingesterapi.models.sampling.CronSampling(str(model.pull_data_source.cron_sampling))
                except TypeError:
                    logger.exception("Trying to create a cron sampler with an invalid cron string: %s" % model.pull_data_source.cron_sampling)
                    return None

            elif PullDataSource.custom_sampling_desc.ca_group_start in model.pull_data_source.selected_sampling:
                try:
                    sampling_object = jcudc24ingesterapi.models.sampling.CustomSampling(model.pull_data_source.custom_sampling_script)
                except TypeError:
                    logger.exception("Trying to create a custom sampler with invalid script handle: %s" % model.pull_data_source.custom_sampling_script)
                    return None
            print "SAMPLIING OBJECT: %s" % sampling_object

            # Create the data source
            try:
                data_source_field = self.session.query(MethodSchemaField).filter_by(id=model.pull_data_source.file_field).first()
                data_source = jcudc24ingesterapi.models.data_sources.PullDataSource(
                    url=model.pull_data_source.uri,
                    field=data_source_field.name,
                    pattern=model.pull_data_source.filename_pattern,
                    mime_type=model.pull_data_source.mime_type,
                    processing_script=model.pull_data_source.custom_processor_script,
                    sampling=sampling_object,
                )
            except TypeError:
                logger.exception("Trying to create an ingester pull data source with invalid parameters")
                return None

        if method.data_source == PushDataSource.__tablename__:
            if model.push_data_source is None:
                raise ValueError("Trying to provision a dataset with no data source.  Go back to the dataset step and configure the data source.")
            data_source = jcudc24ingesterapi.models.data_sources.PushDataSource()
            # TODO: Update datasource configuration
        if method.data_source == SOSDataSource.__tablename__:
            if model.sos_data_source is None:
                raise ValueError("Trying to provision a dataset with no data source.  Go back to the dataset step and configure the data source.")
            data_source = jcudc24ingesterapi.models.data_sources.SOSDataSource()
            # TODO: Update datasource configuration
        if method.data_source == DatasetDataSource.__tablename__:
            if model.dataset_data_source is None:
                raise ValueError("Trying to provision a dataset with no data source.  Go back to the dataset step and configure the data source.")
            try:
                data_source = jcudc24ingesterapi.models.data_sources.DatasetDataSource(
                    model.dataset_data_source.dataset_data_source_id,
                    model.dataset_data_source.custom_processor_script
                )
            except TypeError:
                logger.exception("Trying to create an ingester dataset data source with invalid parameters")
                return None


        new_dataset.data_source = data_source

        if model.redbox_uri is not None:
            new_dataset.redbox_uri = model.redbox_uri


        if model.dam_id is not None:
            new_dataset.id = int(model.dam_id)

        model.dam_id = command(new_dataset)
        new_dataset.provisioning_model = model
        new_dataset.set_listener(model_id_listener)
        return new_dataset

    def process_data_entry(self, model, command, work):
        pass # TODO: data_entries

    def process_metadata(self, model, command, work):
        pass # TODO: metadata






