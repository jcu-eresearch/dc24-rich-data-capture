# This line is needed to activate the virtualenv for running the tests in Intellij IDEA - update to your own virtualenv location.
import ConfigParser
from sqlalchemy.engine import engine_from_config
import transaction

#execfile("D:/Repositories/JCU-DC24/venv/Scripts/activate_this.py", dict(__file__="D:/Repositories/JCU-DC24/venv/Scripts/activate_this.py"))

import unittest
from deform import Form
from colanderalchemy import SQLAlchemyMapping
import jcudc24ingesterapi
from jcudc24ingesterapi.authentication import CredentialsAuthentication
from jcudc24provisioning.models.project import Project, Location, Base, LocationOffset, Method, Dataset, Keyword, FieldOfResearch, MethodSchema, MethodSchemaField, PullDataSource, Metadata, DBSession
from jcudc24provisioning.models.ingesterapi_wrapper import IngesterAPIWrapper
from jcudc24provisioning.views.ca_scripts import convert_schema

class TestModelConversion(unittest.TestCase):
    def test_conversion_equality(self):
        session = DBSession
        PROJECT_ID = 2

        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise',))
        form = Form(schema, action='test', project_id=PROJECT_ID, buttons=('Save', 'Delete', 'Submit', 'Reopen', 'Approve', 'Disable'), use_ajax=False)
        model = session.query(Project).filter_by(id=2).first()
        data = model.dictify(schema)
        new_model = Project(appstruct=data)

        public_props = (name for name in dir(object) if not name.startswith('_'))
        for name in public_props:
            print name
            assert model.getattr(name) == new_model.getattr(name), "Converted models don't equal: %s, %s" % model.getattr(name) % new_model.getattr(name)

        print "Successfully read model, converted to data, converted back to model and the models are the same."


class TestIngesterPlatform(unittest.TestCase):
    def setUp(self):
        self.config = ConfigParser.SafeConfigParser()
        self.config.read('../../development.ini')
        settings = self.config._sections["app:main"]
        engine = engine_from_config(settings, 'sqlalchemy.')
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)
        self.session = DBSession

        self.auth = CredentialsAuthentication(self.config.get("app:main", "ingesterapi.username"), self.config.get("app:main", "ingesterapi.password"))
        self.ingester_api = IngesterAPIWrapper(self.config.get("app:main", "ingesterapi.url"), self.auth)

        self.project = Project()
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
        test_location.name = "Test Location"
        test_location.location = "POINT(135.8763427287297 -24.167471616893767)"
        test_location.elevation = 12.3

        self.project.information = Metadata()
        self.project.information.locations.append(test_location)
        self.project.information.retention_period = "5"
        self.project.metadata.national_significance = False

        method1 = Method()
        method1.method_name = "Artificial tree sensor"
        method1.method_description = "A custom developed sensor consisting of a calibrated temperature sensor and a humidity sensor (which also has an uncalibrated temperature sensor within it)"
        method1.data_source = PullDataSource.__tablename__

        temperature_schema = self.session.query(MethodSchema).filter_by(id=1).first()

        method1.data_type = MethodSchema()
        method1.data_type.name = "Test Schema"
        method1.data_type.parents.append(temperature_schema) # This is the default template schema that is setup on first run within scripts\initialise_database.py


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
        custom_field.name = "Distance"
        custom_field.type = "file"
        custom_field.units = "text/cvs"
        method1.data_type.custom_fields.append(custom_field)
        self.project.methods.append(method1)

        self.session.add(method1)
        self.session.flush()

        dataset1 = Dataset()
        dataset1.method_id = method1.id
        dataset1.disabled = False
        dataset1.description = "Test dataset"

        data_source = PullDataSource()
        data_source.uri = "http://localhost/test_ingestion"
        data_source.mime_type = custom_field.units
        data_source.selected_sampling = PullDataSource.periodic_sampling.key
        data_source.file_field = custom_field.id
        data_source.periodic_sampling = 1

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
        dataset_location.name = "Test Dataset Location"
        dataset_location.location = "POINT(132.8763427287297 -24.167471616893767)"
        dataset_location.elevation = 12.6
        dataset1.dataset_locations.append(dataset_location)

        location_offset = LocationOffset(0, 0, 5)
        dataset1.location_offset = location_offset

        self.project.datasets.append(dataset1)

        self.session.add(self.project)
        self.session.flush()

    def test_ingest_project(self):
        self.ingester_api.post(self.project)
        assert self.project.datasets[0].dam_id >= 0, "Project id listener didn't update project dam_id"
        assert self.project.datasets[0].dataset_locations[0].dam_id >= 0, "Project id listener didn't update project dam_id"
        assert self.project.methods[0].data_type.dam_id >= 0, "Project id listener didn't update project dam_id"
        transaction.commit()
        pass


    def test_listeners(self):
        test_location = Location()
        test_location.location = "POINT(132.8763427287297 -24.167471616893767)"
        
        self.ingester_api.post(test_location)

        self.assertGreater(test_location.dam_id, 0, "Not a valid ID")

    def tearDown(self):
        self.ingester_api.reset()
        self.ingester_api.close()
        self.ingester_api.reset()

if __name__ == '__main__':
    unittest.main()