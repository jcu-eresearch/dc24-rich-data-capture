import unittest
from jcudc24ingesterapi.ingester_platform_api import UnitOfWork
import jcudc24ingesterapi
from jcudc24ingesterapi.authentication import CredentialsAuthentication
from jcudc24ingesterapi.ingester_platform_api import IngesterPlatformAPI
from jcudc24ingesterapi.models.locations import LocationOffset
from models.project import Project, Location, Method, Dataset, Keyword, FieldOfResearch, MethodSchema, MethodSchemaField, PullDataSource
from jcudc24ingesterapi.schemas.data_types import Integer, Double, String, Boolean, FileDataType, DateTime, DataType
from jcudc24ingesterapi.schemas import Schema

class TestIngesterPlatform(unittest.TestCase):
    def setUp(self):
        self.project = Project()
        self.project.id = 1
#        self.project.description = "This is a test description for the DC24 provisioning interface"
#        self.project.no_activity = True
#        self.project.project_title = "This is a test title for the test DC24 project"
#        self.project.data_manager = "A Person"
#        self.project.project_lead = "Another Person"
#        self.project.brief_description = "This is a test brief description"
#        self.project.full_description = "This is a test full description"

#        keyword1 = Keyword()
#        keyword1.id = 0
#        keyword1.project_id = self.project.id
#        keyword1.keyword = "Test Keyword"
#        self.project.keywords.append(keyword1)

#        for1 = FieldOfResearch()
#        for1.id = 0
#        for1.project_id = self.project.id
#        for1.field_of_research = "010101"
#        self.project.fieldOfResearch.append(for1)
#
#        seo1 = FieldOfResearch()
#        seo1.id = 0
#        seo1.project_id = self.project.id
#        seo1.field_of_research = "010101"
#        self.project.socioEconomicObjective.append(seo1)
#        self.project.ecosystems_conservation_climate = True
#        self.project.typeOfResearch = "applied"
#        self.project.time_period_description = "Test time period description " + str(self.project.id)
#        self.project.date_from = 12345
#        self.project.date_to = 1234
#        self.project.location_description = "Test location description"

        test_location = Location()
        test_location.id = 1
        test_location.project_id = self.project.id
        test_location.location = "POINT(135.8763427287297 -24.167471616893767)"
        test_location.elevation = 12.3

        self.project.locations.append(test_location)
        self.project.retention_period = "5"
        self.project.national_significance = False

        method1 = Method()
        method1.id = 0
        method1.project_id = self.project.id
        method1.method_name = "Artificial tree sensor"
        method1.method_description = "A custom developed sensor consisting of a calibrated temperature sensor and a humidity sensor (which also has an uncalibrated temperature sensor within it)"
        method1.data_type = MethodSchema()
        method1.data_type.id=0
        method1.data_type.method_id = method1.id
        method1.data_type.name = "Test Schema"

# The data entry location offset functionality has been changed
#        offset_schema = MethodSchema()
#        offset_schema.id = 1
#        offset_schema.template_schema = True
#        offset_schema.name = "XYZ Offset Schema"
#        offset = LocationOffset()
#
#        x_offset = MethodSchemaField()
#        x_offset.id = 0
#        x_offset.method_schema_id = offset_schema.id
#        x_offset.type = "Double"
#        x_offset.units = "m"
#        offset_schema.custom_fields.append(x_offset)
#
#        y_offset = MethodSchemaField()
#        y_offset.id = 1
#        y_offset.method_schema_id = offset_schema.id
#        y_offset.type = "Double"
#        y_offset.units = "m"
#        offset_schema.custom_fields.append(y_offset)
#
#        z_offset = MethodSchemaField()
#        z_offset.id = 2
#        z_offset.method_schema_id = offset_schema.id
#        z_offset.type = "Double"
#        z_offset.units = "m"
#        offset_schema.custom_fields.append(z_offset)
#
#        method1.data_type.parents.append(offset_schema)

        custom_field = MethodSchemaField()
        custom_field.id = 3
        custom_field.method_schema_id = method1.data_type.id
        custom_field.name = "Distance"
        custom_field.type = "decimal"
        custom_field.units = "m"
        method1.data_type.custom_fields.append(custom_field)
        self.project.methods.append(method1)

        dataset1 = Dataset()
        dataset1.id = 0
        dataset1.method_id = method1.id
        dataset1.project_id = self.project.id
        dataset1.disabled = False
        dataset1.description = "Test dataset"

        data_source = PullDataSource()
        data_source.id = 0
        data_source.dataset_id = dataset1.id
        data_source.uri = "http://test.com.au"
        dataset1.pull_data_source = data_source

        dataset1.time_period_description = "Test dataset time description"
        dataset1.date_from = 1234
        dataset1.date_to = 1234
        dataset1.location_description = "Test dataset location description"
        dataset1.elevation = 12.5

        # If project location is set:
        #   Allow user to provide offset only (set dataset location to project location)
        # Else:
        #   Must set location (with optional offset)

        # TODO: For locations in project: add as region to location

        dataset_location = Location()
        dataset_location.id = 1
        dataset_location.dataset_id = dataset1.id
        dataset_location.location = "POINT(132.8763427287297 -24.167471616893767)"
        dataset_location.elevation = 12.6
        dataset1.dataset_location.append(dataset_location)

        location_offset = LocationOffset(0, 0, 5)
        dataset1.location_offset = location_offset

        self.project.datasets.append(dataset1)

        self.auth = CredentialsAuthentication("casey", "password")
        self.ingester_platform = IngesterPlatformAPI("http://localhost:8080/api", self.auth)

    def convert_location(self, location):
        assert isinstance(location, Location), "Invalid location: " + str(location)
        assert location.location[:5] == "POINT", "Provided location is not a point (only points can be used for dataset or data_entry locations).  Value: " + location.location

        new_location = jcudc24ingesterapi.models.locations.Location(
            latitude = location.get_latitude(),
            longitude = location.get_longitude(),
            location_name = location.name,
            elevation = location.elevation
        )

        return new_location

    def convert_location_offset(self, location_offset):
        assert isinstance(location_offset, LocationOffset), "Invalid location offset: " + str(location_offset)

        new_location_offset = jcudc24ingesterapi.models.locations.LocationOffset(
            location_offset.x,
            location_offset.y,
            location_offset.z
        )
        return new_location_offset

    def add_region(self, location):
        assert isinstance(location, Location), "Invalid location: " + str(location)
        assert not location.location[:5] == "POINT", "Provided location is a point (It doesn't make sense for a region to be a single point).  Value: " + location.location

        region = jcudc24ingesterapi.models.locations.Region(
            region_name = location.name,
            region_points = location.get_points()
        )
        return region

    def convert_schema(self, schema):
        assert isinstance(schema, MethodSchema), "Invalid schema: " + str(schema)

        if True: # TODO: If the data entries don't need offsets
            new_schema = jcudc24ingesterapi.schemas.data_entry_schemas.DataEntrySchema()
        else:
            pass #TODO: new_schema = jcudc24ingesterapi.schemas.data_entry_schemas.OffsetDataEntrySchema()

        # Set the schema parents/extends
        extends = []
        for parent in schema.parents:
            extends.append(parent.dam_schema_id)

        new_schema.extends = extends

        new_schema.name = schema.name

        for field in schema.custom_fields:
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

        return new_schema

    def add_project(self, work, project):
        # TODO: These functions to be refactored into a data_layer package with better modularity.

        assert isinstance(project, Project),"Trying to add a project with a model of the wrong type."
        assert isinstance(work, UnitOfWork), "Invalid unit of work"

        for dataset in project.datasets:
            new_dataset = jcudc24ingesterapi.models.dataset.Dataset()

            new_dataset.id = dataset.dam_dataset_id  # This will be None if it is new (Should always be the case)
#            new_dataset.processing_script = dataset.custom_processor_script - Moved to datasource
            new_dataset.redbox_uri = None   # TODO: Add redbox link
            new_dataset.enabled = True
            new_dataset.descripion = dataset.description

            first_location_found = False
            for location in dataset.dataset_location:
                if not first_location_found and location.is_point:
                    first_location_found = True
                    new_dataset.location = location.dam_location_id
                    if new_dataset.location is None:
                        new_dataset.location = work.post(self.convert_location(location))
                else:
                    # TODO: Discuss regions when we get here - there is currently only 1 region in a dataset (this will fail if run)
                    if location.dam_location_id is None:
                        new_dataset.regions.append(work.post(self.convert_region(location)))
                    else:
                        new_dataset.regions.append(location.dam_location_id)

            if dataset.location_offset is not None:
                new_dataset.location_offset = self.convert_location_offset(dataset.location_offset)

            for method in project.methods:
                if method.id == dataset.method_id:
                    if method.data_type.dam_schema_id is not None:
                        new_dataset.schema = method.data_type.dam_schema_id
                    else:
                        new_dataset.schema = work.post(self.convert_schema(method.data_type))


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

            work.post(new_dataset)


    def test_ingest_project(self):
        work = self.ingester_platform.createUnitOfWork()
        self.add_project(work, self.project)
        work.commit()

    def tearDown(self):
        self.ingester_platform.close()
        pass

if __name__ == '__main__':
    unittest.main()