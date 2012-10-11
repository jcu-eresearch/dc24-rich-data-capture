__author__ = 'Casey Bajema'
import xmlrpclib

class IngesterPlatformAPI():
    """
    The ingester platform API's are intended to provide a simple way of provisioning ingesters for sensors
    or other research data sources.

    Any call to an API method that doesn't meet expectations will throw an exception, common exceptions include:
        * Missing parameters
        * Parameters of an unknown type
        * Parameter values that don't make sense (eg. inserting an object that has an ID set)
    """
    
    def __init__(self, service_url, auth=None):
        """Initialise the client connection using the given URL
        @param service_url: The server URL. HTTP and HTTPS only.
        
        >>> s = IngesterPlatformAPI("")
        Traceback (most recent call last):
        ...
        ValueError: Invalid server URL specified
        >>> s = IngesterPlatformAPI("ssh://")
        Traceback (most recent call last):
        ...
        ValueError: Invalid server URL specified
        >>> c = IngesterPlatformAPI("http://localhost:8080")
        """
        if not service_url.startswith("http://") and not service_url.startswith("https://"):
            raise ValueError("Invalid server URL specified")
        self.server = xmlrpclib.ServerProxy(service_url, allow_none=True)
        self.auth = auth

    def ping(self):
        """A simple diagnotic method which should return "PONG"
        """
        return self.server.ping()

    def post(self, ingester_object):
        """
        Create a new entry using the passed in object, the entry type will be based on the objects type.

        :param ingester_object: Insert a new record if the ID isn't set, if the ID is set update the existing record.
        :return: The object passed in with the ID field set.
        """
        pass

    def insert(self, ingester_object):
        """
        Create a new entry using the passed in object, the entry type will be based on the objects type.

        :param ingester_object: If the objects ID is set an exception will be thrown.
        :return: The object passed in with the ID field set.
        """
        pass

    def update(self, ingester_object):
        """
        Update an entry using the passed in object, the entry type will be based on the objects type.

        :param ingester_object: If the passed in object doesn't have it's ID set an exception will be thrown.
        :return: The updated object (eg. :return == ingester_object should always be true on success).
        """
        pass

    def delete(self, ingester_object):
        """
        Delete an entry using the passed in object, the entry type will be based on the objects type.

        :param ingester_object:  All fields except the objects ID will be ignored.
        :return: The object that has been deleted, this should have all fields set.
        """
        pass

    def get(self, ingester_object, ingester_object_range = None):
        """
        Get object(s) using the passed parameters from ingester_object or the value ranges between ingester_object
            and ingester_object_range, the returned type will be based on the ingester_object type.

        Comparison of values to ranges will be provided using the default python >= and <= operators.

        :param ingester_object: An ingester object with either the ID or any combination of other fields set
        :param ingester_object_range: If the second object is set get all objects that have values between those
                                set in both ingester_object and ingester_object_range
        :return: :If ingester_object_range is set, return all objects of the same type that have values between
                        those set in ingester_object and ingester_object_range.
                    Otherwise, if the ingester_object ID field is set an object of the correct type that matches
                        the ID will be returned.
                    Or an array of all objects of the correct type that match the set fields.
        """
        pass

    def get_ingester_logs(self, dataset_id):
        """
        Get all ingester logs for a single dataset.

        :param dataset_id: ID of the dataset to get ingester logs for
        :return: an array of file handles for all log files for that dataset.
        """
        pass


def push_data(self, authentication, data_entry, dataset_id):
    """
        For datasets that use a PushDataSource, data can be entered using this method.

        If the data_entry_id is set the upd

        :param data_entry: The actual data to save, an InvalidObjectError will be raised if the data_entry_id is set.
        :param key:
        :param username:
        :param password:
        :return: The data_entry object with the data_entry_id set on success, otherwise raise an AuthenticationError
    """
    pass