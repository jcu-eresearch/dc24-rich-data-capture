__author__ = 'Casey Bajema'

"""
    Ingester objects that are created with parameters that don't exist in their schema will raise this exception.
"""
class UnknownParameterError(Exception):
    """
         @parameter_name - name of the unknown parameter
         @parameter_value - value of the unknown parameter
    """
    def __init__(self, parameter_name, parameter_value):
        self.parameter_name = parameter_name
        self.parameter_value = parameter_value

    def __str__(self):
        return repr(self.parameter_name + " : " + self.parameter_value)

"""
    Schema definitions that have invalid fields or cannot be implemented for any other reason will raise this
    exception.
"""
class UnsupportedSchemaError(Exception):
    def __init__(self, schema):
        self.schema = schema

    def __str__(self):
        return repr(self.schema + " : " + self.schema.items())

"""
    Exception that is thrown by the ingester_platform if the passed in object is in an invalid state or the
    object type is invalid.
"""
class InvalidObjectError(Exception):
    def __init__(self, ingester_object):
        self.ingester_object = ingester_object

    def __str__(self):
        return repr(self.ingester_object)

"""
    Exception that is thrown by the ingester_platform if the passed in object of an unknown type
"""
class UnknownObjectError(Exception):
    def __init__(self, ingester_object):
        self.ingester_object = ingester_object

    def __str__(self):
        return repr(self.ingester_object)

"""
    Exception that is thrown by the ingester_platform if the passed in dataset has an unknown data source.
"""
class UnknownDataSourceError(Exception):
    def __init__(self, data_source):
        self.data_source = data_source

    def __str__(self):
        return repr(self.data_source)