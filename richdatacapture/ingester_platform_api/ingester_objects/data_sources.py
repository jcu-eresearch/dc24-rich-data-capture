from sqlalchemy.dialects.mysql.base import VARCHAR, INTEGER, TEXT
from ingester_platform_api.ingester_objects.sampling import _Sampling

"""
    Defines all possible data sources or in other words data input methods that can be provisioned.
"""

__author__ = 'Casey Bajema'

"""
    Base data source class that does nothing beyond defining a known type.

    Data sources are known types that provide a known set of information but are unrelated to the data type.
    The ingester platform will need to implement data type specific ingesters for each data source.
"""
class _DataSource():
    pass

"""
    A data source that polls a URI for data of the dataset's data type.
"""
class PullDataSource(_DataSource):
    pull_server = VARCHAR(250)
    sampling = _Sampling()

"""
    A data source that provides a web service for external applications to pass data into.

    The dataset_id will need to be passed into the push data source API to differentiat between different data
    sources and to support multiple ingesters for a single datasource.  This may be part of the authentication.

    Authentication will be required based on the users configuration.
"""
class PushDataSource(_DataSource):
    # TODO: Authentication implementation.
    pass


"""
    A data source that provides a Sensor Observation Service accessible over the web.

    SOS standards will be followed such as:
    * No authentication required
    * Invalid data is dropped
""" # TODO: Work out the exact implementation details
class SOSDataSource(_DataSource):
    sensor_id = INTEGER()   # Need to check the sensor_id type
    sensorml = TEXT()
    pass

"""
    A data source where the user manually uploads a file using the provisioning system.

    This data source will be very similar to PushDataSource but:
    * Won't require authentication as it is using the standard provisioning system API by passing a data_entry object
    * The provisioning system will setup an upload form.
"""
class UploadDataSource(_DataSource):
    pass

"""
    A data source where the user manually enters data into a form within the provisioning interface

    The data entry's will be passed to the ingester platform through the API as data_entry objects.
"""
class FormDataSource(_DataSource):
    pass



