from sqlalchemy.schema import Table

__author__ = 'Casey Bajema'


class Dataset(dict):
    """
    Represents a single dataset and contains the information required to ingest the data as well as location
    metadata.
    """

    def __init__(self, location = None, data_type = None, data_source = None, processing_script = None, redbox_link = None, dataset_id = None):
        self.dataset_id = dataset_id                    # Primary key, Integer
        self.location = location
        self.data_type = data_type                      # subclass of DataType
        self.data_source = data_source                  # subclass of _DataSource
        self.processing_script = processing_script      # handle to a file containing a python script, the script can access the data_entry through self.data_entry
        self.redbox_link = redbox_link                  # URL to the ReDBox collection.