__author__ = 'Casey Bajema'

"""
    Base class for individual data points of a dataset.

    DataEntry objects will be used for each data point where the actual data is passed in through the
    kwargs argument.

    The kwargs parameters must conform to the data_type schema or an exception will be thrown on initialisation.
"""
class DataEntry(dict):
    def __init__(self, dataset_id, schema, datetime, data_entry_id = -1, quality = None, **kwargs):
        self.data_entry_id = data_entry_id
        self.dataset_id = dataset_id
        self.schema = schema
        self.datetime = datetime
        # TODO: Work out code for handling **kwargs and placing them into fields based on the schema passed in

