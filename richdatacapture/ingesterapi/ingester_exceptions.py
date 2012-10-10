__author__ = 'Casey Bajema'


class UnknownParameterError(Exception):
    """
    Ingester objects that are created with parameters that don't exist in their schema will raise this exception.
    """

    def __init__(self, parameter_name, parameter_value):
        """
        :param parameter_name: Name of the unknown parameter
        :param parameter_value: Value of the unknown parameter
        """
        self.parameter_name = parameter_name
        self.parameter_value = parameter_value

    def __str__(self):
        return repr(self.parameter_name + " : " + self.parameter_value)


class UnsupportedSchemaError(Exception):
    """
    Schema definitions that have invalid fields or cannot be implemented for any other reason will raise this
    exception.
    """
    def __init__(self, schema):
        self.schema = schema

    def __str__(self):
        return repr(self.schema + " : " + self.schema.items())

class InvalidObjectError(Exception):
    """
    Exception that is thrown by the ingester_platform if the passed in object is in an invalid state.
    """
    def __init__(self, ingester_object, invalid_field):
        self.ingester_object = ingester_object
        self.invalid_field = invalid_field

    def __str__(self):
        return repr(self.invalid_field + " : " + self.ingester_object)

class UnknownObjectError(Exception):
    """
    Exception that is thrown by the ingester_platform if the passed in object of an unknown or incorrect type
    """
    def __init__(self, ingester_object):
        self.ingester_object = ingester_object

    def __str__(self):
        return repr(self.ingester_object)

class AuthenticationError(Exception):
    """
    Exception that is thrown by the ingester_platform user fails to authenticate.
    """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)

class InvalidCall(Exception):
    """
    Thrown when an API method call cannot be completed because it would corrupt the data state (eg. deleting a location
    that  quality data associated with it).
    """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)
