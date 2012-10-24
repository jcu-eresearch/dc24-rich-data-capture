import datetime
import os
import unittest
from sqlalchemy.types import BOOLEAN
import sys
import tempfile

from richdatacapture.ingesterapi.models.dataset import Dataset
from richdatacapture.ingesterapi.models.locations import Location, Region
from richdatacapture.ingesterapi.schemas.data_types import FileDataType
from richdatacapture.ingesterapi.models.data_sources import PullDataSource, PushDataSource
from richdatacapture.ingesterapi.models.data_entry import DataEntry
from richdatacapture.ingesterapi.ingester_platform_api import IngesterPlatformAPI
from richdatacapture.ingesterapi.authentication import CredentialsAuthentication
from richdatacapture.ingesterapi.models.metadata import Metadata
from richdatacapture.ingesterapi.schemas.metadata_schemas import QualityMetadataSchema, SampleRateMetadataSchema, NoteMetadataSchema, QualityMetadataSchema
from richdatacapture.ingesterapi.models.sampling import RepeatSampling, PeriodicSampling
from richdatacapture.ingesterapi.ingester_exceptions import UnsupportedSchemaError, InvalidObjectError, UnknownObjectError, AuthenticationError

class TestIngesterModels(unittest.TestCase):
    def test_authentication(self):
        pass

    def test_ingester_exceptions(self):
        pass

#    def test_ingester_platform(self):
#        self.ingester_platform = IngesterPlatformAPI()
#        dataset = self.ingester_platform.post(self.auth, self.dataset)
#        self.assertTrue(dataset is set, "Failed to add dataset to ingester API")
#        self.assertTrue(dataset.dataset_id is set and dataset.dataset_id >= 0,
#            "Ingester API returned dataset with invalid dataset_id")
#        self.dataset = dataset
#
#        data_entry = self.ingester_platform.post(self.auth, self.data_entry)
#        self.assertTrue(data_entry is set, "Failed to add data_entry to ingester API")
#        self.assertTrue(data_entry.data_entry_id is set and data_entry.data_entry_id >= 0,
#            "Ingester API returned data_entry with invalid data_entry_id")
#        self.data_entry = data_entry
#
#        datasets = self.ingester_platform.get(self.auth, Dataset())    # Get all datasets
#        self.assertTrue(len(datasets) > 0, "Ingester API failed to insert dataset")
#        self.assertIn(self.dataset, datasets, "Ingester API didn't return the inserted dataset")
#
#        data_quality = Metadata(self.data_entry, QualityMetadataSchema(), {"description": "Sensor was moved", "value": 0})
#        stored_data_quality = self.ingester_platform.post(self.auth, data_quality)
#        self.assertEquals(data_quality, stored_data_quality)
#
#        sampling_rate = Metadata(self.dataset, SampleRateMetadataSchema(), {"sampling": PeriodicSampling()})
#
#        location_elevation_type = Metadata(self.location, NoteMetadataSchema(),
#                {"name": "Elevation type", "text": "Height above ground"})


    def test_ingester_scripts(self):
        pass


class TestIngesterFunctionality(unittest.TestCase):
    """This set of tests checks that the CRUD functionality works as expected
    """
    def setUp(self):
        self.auth = CredentialsAuthentication("casey", "password")
        self.ingester_platform = IngesterPlatformAPI("http://localhost:8080", self.auth)
        self.cleanup_files = []
        
    def test_metadata_functionality(self):
        pass

    def test_location_functionality(self):
        loc = Location(10.0, 11.0, "Test Site", 100, None)
        loc1 = self.ingester_platform.post(loc)
        self.assertNotEqual(loc1.id, None, "ID should have been set")
        self.assertEqual(loc.latitude, loc1.latitude, "latitude does not match")
        self.assertEqual(loc.longitude, loc1.longitude, "longitude does not match")
        self.assertEqual(loc.elevation, loc1.elevation, "elevation does not match")
        self.assertEqual(loc.name, loc1.name, "name does not match")

    def test_manual_ingest_functionality(self):
        pass

    def test_sampling_functionality(self):
        pass

    def test_processing_functionality(self):
        pass

    def tearDown(self):
        self.ingester_platform.reset()

#class TestProjectFunctionality(unittest.TestCase):
#    #---------------Create example data---------------
#    def setUp(self):
#        self.auth = CredentialsAuthentication("casey", "password")
#        self.ingester_platform = IngesterPlatformAPI("http://localhost:8080", self.auth)
#        self.cleanup_files = []
#
#    def test_connection(self):
#        result = self.ingester_platform.ping()
#        self.assertEquals(result, "PONG", "Could not ping service")
#
#    def test_ingest_functionality(self):
#        self.region = Region(
#            "Queensland",
#                [(2314, 1234), (1234, 1234), (1234, 1234), (1234, 2134)]
#        )
#
#        self.location = Location(1234, 1234, "Example Point", 1.5, self.region)
#
#        self.data_type = FileDataType()
#        self.data_type.extra_data_example = BOOLEAN()
#
#        self.script_handle = os.path.join(tempfile.gettempdir(), 'test_script_file.py')
#        self.cleanup_files.append(self.script_handle)
#        
#        script = "class TestProcessingScript(_ProcessingScript):"\
#                 "  def process_it(self, data_entry):"\
#                 "      assertIsInstance(data_entry, FileDataType)"\
#                 "      return {data_entry, DataEntry(data_entry.dataset, data_entry.data_type_schema, data_entry.datetime, {'processed':True})}"\
#                 ""
#        script_file = open(self.script_handle, 'w')
#        script_file.write(script)
#
#        self.dataset = Dataset(self.location, self.data_type, PushDataSource(sampling_script), self.script_handle)
#
#        self.data_entry = DataEntry(self.dataset, FileDataType(), 123456789,
#                {"mime_type": "text/xml", "file_handle": "c:/test.xml", "extra_data_example": False})
#
#        self.data_quality = Metadata(self.data_entry, QualityMetadataSchema(),
#                {"description": "The entered data was invalid."})
#        self.dataset_sampling_changed = Metadata(self.dataset, SampleRateMetadataSchema(),
#                {"change_time": datetime.today(), "sampling": PeriodicSampling(1000)})
#    # Datasets
#        try:
#            # Add a dataset
#            self.dataset = self.ingester_platform.post(self.dataset)
#
#            # Update the dataset with a ReDBox link after the metadata is entered.
#            self.dataset.redbox_link = "https://eresearch.jcu.edu.au/researchdata/123456789" # After entry into ReDBox
#            self.dataset = self.ingester_platform.post(self.dataset)
#
#            # Change the sampling rate of the dataset
#            self.dataset = self.ingester_platform.post(self.dataset_sampling_changed)
#
#            # Add a manual data entry
#            self.data_entry = self.ingester_platform.post(self.data_entry)
#
#            # Provide quality information on the data_entry
#            self.data_entry = self.ingester_platform.post(self.data_quality)
#
#            # Example of searching a range
#            start_search_id_range = DataEntry(data_entry_id=0)
#            start_search_id_range = DataEntry(data_entry_id=self.data_entry.data_entry_id)
#            found_data_entries = self.ingester_platform.get(start_search_id_range, start_search_id_range)
#            found = False
#            for data_entry in found_data_entries:
#                if data_entry == self.data_entry:
#                    # Delete the data_entry
#                    found = True
#            self.assertTrue(found, "id range search failed")
#
#            a_data_entry = DataEntry(kwargs={"extra_data_example": False})
#            data_entry = self.ingester_platform.get(DataEntry)
#            self.ingester_platform.delete(self.auth, self.data_entry)
#
#            # Get all datasets at the location
#            location_search = Dataset(self.location, None, None)
#            found_datasets = self.ingester_platform.get(location_search)
#            found = False
#            for dataset in found_datasets:
#                if dataset == self.dataset:
#                    # Delete the dataset
#                    self.ingester_platform.delete(self.auth, self.dataset)
#                    found = True
#            self.assertTrue(found, "location search failed")
#
#        except UnsupportedSchemaError:
#            assert True, "The data_type schema was an unknown type (this should never happen except under development"
#
#        except InvalidObjectError:
#            assert True, "Will occur if the model is invalid due to a not set required field or fields that are set "\
#                         "incorrectly (eg. data_schema is missing, location is an integer instead of a location object)"
#        except UnknownObjectError:
#            assert True, "Will occur if a non-ingester model object is posted. (eg. data_entry, dataset, location or metadata "\
#                         "are valid - sampling, data_sources or any other object are not)."
#        except AuthenticationError:
#            assert True, "The ingester API couldn't authenticate."
#        except ValueError:
#            assert True, "Any parameter that has an invalid value such as location.location_id isn't set"
#        except:
#            assert True, "Any other run time error that the ingester platform throws."
#
#    def tearDown(self):
#        self.ingester_platform.reset()
#        for f_name in self.cleanup_files:
#            if os.path.exists(f_name):
#                try:
#                    os.remove(f_name)
#                except:
#                    print "Exception: ", str(sys.exc_info())

if __name__ == '__main__':
    unittest.main()