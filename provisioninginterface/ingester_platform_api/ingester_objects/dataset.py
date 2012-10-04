from sqlalchemy.schema import Table

__author__ = 'Casey Bajema'

"""
    Represents a single dataset and contains the information required to ingest the data as well as location
    metadata.
"""
class Dataset(dict):
    object_type = "Dataset"

    def __init__(self, latitude, longitude, data_type, data_source, processing_script = None, redbox_link = None, dataset_id = -1, calibration_schemas = ()):
        self.dataset_id = dataset_id                    # Primary key, Integer
        self.latitude = latitude                        # double
        self.longitude = longitude                      # double
        self.data_type = data_type                      # subclass of _DataType
        self.data_source = data_source                  # subclass of _DataSource
        self.processing_script = processing_script      # handle to a file containing a python script, the script can access the data_entry through self.data_entry
        self.redbox_link = redbox_link                  # URL to the ReDBox collection.
        self.calibration_schemas = calibration_schemas  # An array of calibration schemas that will be used.