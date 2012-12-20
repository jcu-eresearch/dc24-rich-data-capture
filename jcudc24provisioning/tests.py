import unittest
import jcudc24ingesterapi
from jcudc24ingesterapi.authentication import CredentialsAuthentication
from jcudc24ingesterapi.ingester_platform_api import IngesterPlatformAPI
from models.project import Project, Location, Method, Dataset, Keyword, FieldOfResearch, MethodSchema, MethodSchemaField, PollDataSource


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

        offset_schema = MethodSchema()
        offset_schema.id = 1
        offset_schema.template_schema = True
        offset_schema.name = "XYZ Offset Schema"

        x_offset = MethodSchemaField()
        x_offset.id = 0
        x_offset.method_schema_id = offset_schema.id
        x_offset.type = "Double"
        x_offset.units = "m"
        offset_schema.custom_fields.append(x_offset)

        y_offset = MethodSchemaField()
        y_offset.id = 1
        y_offset.method_schema_id = offset_schema.id
        y_offset.type = "Double"
        y_offset.units = "m"
        offset_schema.custom_fields.append(y_offset)

        z_offset = MethodSchemaField()
        z_offset.id = 2
        z_offset.method_schema_id = offset_schema.id
        z_offset.type = "Double"
        z_offset.units = "m"
        offset_schema.custom_fields.append(z_offset)

        method1.data_type.parents.append(offset_schema)

        custom_field = MethodSchemaField()
        custom_field.id = 3
        custom_field.method_schema_id = method1.data_type.id
        custom_field.type = "Double"
        custom_field.units = "m"
        method1.data_type.custom_fields.append(custom_field)
        self.project.methods.append(method1)

        dataset1 = Dataset()
        dataset1.id = 0
        dataset1.method_id = method1.id
        dataset1.project_id = self.project.id
        dataset1.disabled = False
        dataset1.description = "Test dataset"

        data_source = PollDataSource()
        data_source.id = 0
        data_source.dataset_id = dataset1.id
        data_source.poll_data_source_url = "http://test.com.au"
        dataset1.poll_data_source = data_source
        dataset1.time_period_description = "Test dataset time description"
        dataset1.date_from = 1234
        dataset1.date_to = 1234
        dataset1.location_description = "Test dataset location description"
        dataset1.elevation = 12.5

        dataset_location = Location()
        dataset_location.id = 1
        dataset_location.dataset_id = dataset1.id
        dataset_location.location = "POINT(132.8763427287297 -24.167471616893767)"
        dataset_location.elevation = 12.6
        dataset1.dataset_location.append(dataset_location)

        self.project.datasets.append(dataset1)

        self.auth = CredentialsAuthentication("casey", "password")
        self.ingester_platform = IngesterPlatformAPI("http://localhost:8080/api", self.auth)

    def add_location(self, work, location):
        if isinstance(location, Location):
            if location.location[:5] == "POINT":
                new_location = jcudc24ingesterapi.models.locations.Location(
                    latitude = location.getLatitude(),
                    longitude = location.getLongitude(),
                    location_name = location.name,
                    elevation = location.elevation
                )
                work.post(new_location)
            else:
                # TODO: Regions
                pass
        else:
            # TODO: Handle offset locations
            pass

        return new_location

    def add_project(self, work, project):
        assert isinstance(project, Project),"Trying to add a project with a model of the wrong type."

        for dataset in project.datasets:
            new_dataset = jcudc24ingesterapi.models.dataset.Dataset()

            new_dataset.id = dataset.dam_dataset_id  # This will be None if it is new (Should always be the case)
            new_dataset.processing_script = dataset.custom_processor_script
            new_dataset.redbox_uri = None   # TODO: Add redbox link
            new_dataset.enabled = True
            new_dataset.descripion = dataset.description

            for location in dataset.dataset_location:
                # TODO: Project Regions
                new_dataset.location = self.add_location(work, location )

            for method in project.methods:
                if method.id == dataset.method_id:
                    new_schema = jcudc24ingesterapi.schemas.data_entry_schemas.DataEntrySchema()
                    # TODO: Add date_entry schema as a parent to all schemas created for a dataset.

                    # TODO: Make the schema in ingesterapi objects when it is updated

                    work.post(new_schema)
                    new_dataset.schema = new_schema

            # TODO: Update datasources to add configuration
            if dataset.form_data_source is not None:
                data_source = jcudc24ingesterapi.models.data_sources.FormDataSource()
            if dataset.poll_data_source is not None:
                data_source = jcudc24ingesterapi.models.data_sources.PullDataSource()
            if dataset.push_data_source is not None:
                data_source = jcudc24ingesterapi.models.data_sources.PushDataSource()
            if dataset.sos_data_source is not None:
                data_source = jcudc24ingesterapi.models.data_sources.SOSDataSource()
            if dataset.dataset_data_source is not None:
                data_source = jcudc24ingesterapi.models.data_sources.DatasetDataSource()

            new_dataset.data_source = data_source

            work.post(new_dataset)


    def test_ingest_project(self):
        ingester_work = self.ingester_platform.createUnitOfWork()
        self.add_project(ingester_work, self.project)
        ingester_work.commit()

    def tearDown(self):
        # TODO: Does the ingesterapi connection need to be closed?
        pass

if __name__ == '__main__':
    unittest.main()