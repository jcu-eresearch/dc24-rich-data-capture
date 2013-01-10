from beaker.cache import cache_region
from jcudc24ingesterapi.authentication import CredentialsAuthentication
from jcudc24ingesterapi.ingester_platform_api import IngesterPlatformAPI
from jcudc24ingesterapi.ingester_platform_api import UnitOfWork
import jcudc24ingesterapi
from jcudc24provisioning.models.project import Location, LocationOffset, MethodSchema, Base, Project, Region
from jcudc24ingesterapi.schemas.data_types import DateTime, FileDataType, Integer, String, Double, Boolean

__author__ = 'Casey Bajema'

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
            self.process_model(model, work.post)
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
            self.process_model(model, work.insert)
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
            self.process_model(model, work.update)
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
            self.process_model(model, work.delete)
            work.commit()
            return model
        else:
            return super(IngesterAPIWrapper, self).delete(model)

    #---------------Provisioning interface specific functions for processing the models-------------
    def process_model(self, model, command):
        assert hasattr(model, "__tablename__"), "Trying to process a invalid provisioning model"
        assert hasattr(command, "func_name") and hasattr(UnitOfWork, command.func_name), "Trying to process a model with an invalid command"

        if isinstance(model, Project):
            return self.process_project(model, command)
        elif isinstance(model, Location):
            return self.process_location(model, command)
        elif isinstance(model, LocationOffset):
            return self.process_location_offset(model, command)
        elif isinstance(model, Region):
            return self.process_region(model, command)
        elif isinstance(model, MethodSchema):
            return self.process_schema(model, command)
        else:
            print model
            raise ValueError("Unknown provisioning interface model")


    def process_location(self, model, command):
        assert isinstance(model, Location), "Invalid location: " + str(model)
        assert model.location[:5] == "POINT", "Provided location is not a point (only points can be used for dataset or data_entry locations).  Value: " + model.location

        new_location = jcudc24ingesterapi.models.locations.Location(
            latitude = model.get_latitude(),
            longitude = model.get_longitude(),
            location_name = model.name,
            elevation = model.elevation
        )
        if model.dam_id is not None:
            new_location.id = model.dam_id

        def test():
            print "test"

        model.dam_id = command(new_location)
        return model.dam_id

    def process_location_offset(self, model, command):
        assert isinstance(model, LocationOffset), "Invalid location offset: " + str(model)

        new_location_offset = jcudc24ingesterapi.models.locations.LocationOffset(
            model.x,
            model.y,
            model.z
        )
        return new_location_offset

    def process_region(self, model, command):
        assert isinstance(model, Location), "Invalid location: " + str(model)
        assert not model.location[:5] == "POINT", "Provided location is a point (It doesn't make sense for a region to be a single point).  Value: " + model.location

        region = jcudc24ingesterapi.models.locations.Region(
            region_name = model.name,
            region_points = model.get_points()
        )

        if model.dam_id is not None:
            region.id = model.dam_id

        model.dam_id = command(region)
        return model

    def process_schema(self, model, command):
        assert isinstance(model, MethodSchema), "Invalid schema: " + str(model)

        if True: # TODO: If the data entries don't need offsets
            new_schema = jcudc24ingesterapi.schemas.data_entry_schemas.DataEntrySchema()
        else:
            pass #TODO: new_schema = jcudc24ingesterapi.schemas.data_entry_schemas.OffsetDataEntrySchema()

        # Set the schema parents/extends
        extends = []
        for parent in model.parents:
            extends.append(parent.dam_schema_id)

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
            new_schema.id = model.dam_id

        model.dam_id = command(new_schema)
        return model.dam_id

    def process_project(self, project, command):
        assert isinstance(project, Project),"Trying to add a project with a model of the wrong type."

        for dataset in project.datasets:
            new_dataset = jcudc24ingesterapi.models.dataset.Dataset()

            new_dataset.id = dataset.dam_id  # This will be None if it is new (Should always be the case)
            #            new_dataset.processing_script = dataset.custom_processor_script - Moved to datasource
            new_dataset.redbox_uri = None   # TODO: Add redbox link
            new_dataset.enabled = True
            new_dataset.descripion = dataset.description

            first_location_found = False
            for location in dataset.dataset_location:
                if not first_location_found and location.is_point:
                    first_location_found = True
                    new_dataset.location = location.dam_id
                    if new_dataset.location is None:
                        new_dataset.location = self.process_location(location, command)
                else:
                    # TODO: Discuss regions when we get here - there is currently only 1 region in a dataset (this will fail if run)
                    if location.dam_location_id is None:
                        new_dataset.regions.append(self.process_region(location, command))
                    else:
                        new_dataset.regions.append(location.dam_location_id)

            if dataset.location_offset is not None:
                new_dataset.location_offset = self.process_location_offset(dataset.location_offset, command)

            for method in project.methods:
                if method.id == dataset.method_id:
                    if method.data_type.dam_id is not None:
                        new_dataset.schema = method.data_type.dam_id
                    else:
                        new_dataset.schema = self.process_schema(method.data_type, command)

            if dataset.form_data_source is not None:
                data_source = jcudc24ingesterapi.models.data_sources.FormDataSource()
                # TODO: Update datasource configuration
            if dataset.pull_data_source is not None:
                data_source = jcudc24ingesterapi.models.data_sources.PullDataSource(
                    dataset.pull_data_source.uri,
                    dataset.pull_data_source.file_field,
                    dataset.pull_data_source.filename_pattern,
                    dataset.pull_data_source.mime_type,
                    dataset.custom_processor_script,
                    dataset.pull_data_source.custom_sampling_script,

                )
            if dataset.push_data_source is not None:
                data_source = jcudc24ingesterapi.models.data_sources.PushDataSource()
                # TODO: Update datasource configuration
            if dataset.sos_data_source is not None:
                data_source = jcudc24ingesterapi.models.data_sources.SOSDataSource()
                # TODO: Update datasource configuration
            if dataset.dataset_data_source is not None:
                data_source = jcudc24ingesterapi.models.data_sources.DatasetDataSource()
                # TODO: Update datasource configuration

            new_dataset.data_source = data_source


            if dataset.dam_id is not None:
                new_dataset.id = dataset.dam_id

            dataset.dam_id = command(new_dataset)


