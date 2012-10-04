from ingesterapi.ingester_objects.ingester_exceptions import UnknownParameterError

__author__ = 'Casey Bajema'

"""
    Base class for individual data points of a dataset.

    DataEntry objects will be used for each data point where the actual data is passed in through the
    kwargs argument.

    The kwargs parameters must conform to the data_type schema or an exception will be thrown on initialisation.
"""
class DataEntry(dict):
    object_type = "DataEntry"

    def __init__(self, dataset_id, data_type_schema, datetime, data_entry_id = -1, quality = None, **kwargs):
        self.data_entry_id = data_entry_id
        self.dataset_id = dataset_id
        self.data_type_schema = data_type_schema
        self.datetime = datetime

        # Push the kwargs to fields
        for key in data_type_schema.keys():
            self[key] =  kwargs.pop(key, None)

        for key, value in kwargs:
            raise UnknownParameterError(key, value)



