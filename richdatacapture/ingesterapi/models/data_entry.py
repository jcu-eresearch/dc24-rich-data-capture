from richdatacapture.ingesterapi.ingester_exceptions import UnknownParameterError

__author__ = 'Casey Bajema'

class DataEntry(dict):
    """
    Base class for individual data points of a dataset.

    DataEntry objects will be used for each data point where the actual data is passed in through the
    kwargs argument.

    The kwargs parameters must conform to the data_type schema in the dataset or an exception will be thrown on initialisation.
    """

    def __init__(self, dataset=None, datetime=None, data_entry_id = None, **kwargs):
        self.data_entry_id = data_entry_id
        self.dataset = dataset
        self.datetime = datetime

        # Push the kwargs to fields
        for key in data_type_schema.keys():
            self[key] =  kwargs.pop(key, None)

        for key, value in kwargs:
            raise UnknownParameterError(key, value)



