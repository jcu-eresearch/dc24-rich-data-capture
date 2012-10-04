from ingester_platform_api.ingester_objects.ingester_exceptions import UnknownParameterError

__author__ = 'Casey Bajema'


"""
    Calibration class that provides calibration information about a single data_entry

    Calibration objects will be used for each calibration where the actual data is passed in through the
    kwargs argument.

    The kwargs parameters must conform to the calibration schema or an exception will be thrown on initialisation.
"""
class Calibration(dict):
    object_type = "Calibration"

    def __init__(self, data_entry_id, calibration_id, calibration_schema = -1, **kwargs):
        self.calibration_id = calibration_id
        self.data_entry_id =  data_entry_id
        self.calibration_schema = calibration_schema

        # Push the kwargs to fields
        for key in calibration_schema.keys():
            self[key] =  kwargs.pop(key, None)

        for key, value in kwargs:
            raise UnknownParameterError(key, value)
