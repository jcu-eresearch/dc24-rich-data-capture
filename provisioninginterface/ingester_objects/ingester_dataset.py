__author__ = 'Casey Bajema'

class IngesterDataset():
    def __init__(self, dataset_schema, method_id = -1, description = "", time_description = "", start_time = None, end_time = None, locaiton_description = "", longitude = None, latitude = None, processing_script = None, **kwargs):
        self.schema = dataset_schema
        self.method_id = method_id
        self.description = description
        self.time_description = time_description
        self.start_time = start_time
        self.end_time = end_time
        self.location_description = location_description
        self.latitude = latitude
        self.longitude = longitude
        self.processing_script = processing_script

        #... Work out code for handling **kwargs and placing them into fields based on the schema passed in