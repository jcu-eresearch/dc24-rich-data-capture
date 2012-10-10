from richdatacapture.ingesterapi.ingester_exceptions import UnknownParameterError

__author__ = 'Casey Bajema'

class Metadata(dict):
    """
    Metadata class that provides further information about a single object, this could be a data_entry,
    dataset or any other stored object.

    This class represents any metadata where the schema passed in defines the metadata and the actual data
    is passed in through the kwargs argument.

    The kwargs parameters must conform to the calibration schema or an exception will be thrown on initialisation.
    """

    def __init__(self, ingester_object = None, metadata_schema = None, metadata_id=None, **kwargs):
        self.metadata_id = metadata_id
        self.ingester_object = ingester_object
        self.metadata_schema = metadata_schema

        # Push the kwargs to fields
        for key in metadata_schema.keys():
            self[key] = kwargs.pop(key, None)

        for key, value in kwargs:
            raise UnknownParameterError(key, value)
