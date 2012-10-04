"""
    The ingester platform API's are intended to provide a simple way of provisioning ingesters for sensors
    or other research data sources.

    Any call to an API method that doesn't meet expectations will throw an exception, common exceptions include:
        * Missing parameters
        * Parameters of an unknown type
        * Parameter values that don't make sense (eg. inserting an object that has an ID set)
"""

__author__ = 'Casey Bajema'

class IngesterPlatformAPI():
    """
        Create a new entry using the passed in object, the entry type will be based on the objects type.

        @ingester_object - If the objects ID is set an exception will be thrown.
        @return the object passed in with the ID field set.
    """
    def insert(self, ingester_object):
        pass

    """
        Update an entry using the passed in object, the entry type will be based on the objects type.

        @ingester_object - If the passed in object doesn't have it's ID set an exception will be thrown.
        @return the updated object (eg. @return == ingester_object should always be true on success).
    """
    def update(self, ingester_object):
        pass

    """
        Delete an entry using the passed in object, the entry type will be based on the objects type.

        @ingester_object - All fields except the objects ID will be ignored.
        @return the object that has been deleted, this should have all fields set.
    """
    def delete(self, ingester_object):
        pass

    """
        Get object(s) using the passed parameters from ingester_object or the value ranges between ingester_object
            and ingester_object_range, the returned type will be based on the ingester_object type.

        Comparison of values to ranges will be provided using the default python >= and <= operators.

        @ingester_object - An ingester object with either the ID or any combination of other fields set
        @ingester_object_range - If the second object is set get all objects that have values between those
                                set in both ingester_object and ingester_object_range
        @return -   If ingester_object_range is set, return all objects of the same type that have values between
                        those set in ingester_object and ingester_object_range.
                    Otherwise, if the ingester_object ID field is set an object of the correct type that matches
                        the ID will be returned.
                    Or an array of all objects of the correct type that match the set fields.
    """
    def get(self, ingester_object, ingester_object_range = None):
        pass

    """
        Get all ingester logs for a single dataset.

        @dataset_id - ID of the dataset to get ingester logs for
        @return an array of file handles for all log files for that dataset.
    """
    def get_ingester_logs(self, dataset_id):
        pass