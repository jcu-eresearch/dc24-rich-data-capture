"""
    The ingester platform API's are intended to provide a simple way of provisioning ingesters for sensors
    or other research data sources.

    Any call to an API method that doesn't meet expectations will throw an exception, common exceptions include:
        * Missing parameters
        * Parameters of an unknown type
        * Parameter values that don't make sense (eg. inserting an object that has an ID set)
"""

__author__ = 'Casey Bajema'


"""
    Create a new entry using the passed in object, the entry type will be based on the objects type.

    @ingester_object - If the objects ID is set an exception will be thrown.
    @return the object passed in with the ID field set.
"""
def insert(ingester_object):
    pass

"""
    Update an entry using the passed in object, the entry type will be based on the objects type.

    @ingester_object - If the passed in object doesn't have it's ID set an exception will be thrown.
    @return the updated object (eg. @return == ingester_object should always be true on success).
"""
def update(ingester_object):
    pass

"""
    Delete an entry using the passed in object, the entry type will be based on the objects type.

    @ingester_object - All fields except the objects ID will be ignored.
    @return the object that has been deleted, this should have all fields set.
"""
def delete(ingester_object):
    pass

"""
    Get an entry using the passed in object, the entry type will be based on the objects type.

    @ingester_object - An ingester object with either the ID or any combination of other fields set
    @return -   If the objects ID field is set an object of the correct type that matches the ID
                    will be returned.
                If the object ID field isn't set an array of all objects of the correct type that
                    match the set fields will be returned.
"""
def get(ingester_object):
    pass

"""
    Get all ingester logs for a single dataset.

    @dataset_id - ID of the dataset to get ingester logs for
    @return an array of file handles for all log files for that dataset.
"""
def get_ingester_logs(dataset_id):
    pass