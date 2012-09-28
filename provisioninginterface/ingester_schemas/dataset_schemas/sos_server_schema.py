from ingester_schemas.data_entry_schemas.file_data_entry_schema import FileDataEntrySchema
from ingester_schemas.data_sources.push_data_source import PushDataSource
from ingester_schemas.data_sources.sos_data_source import SOSDataSource
from ingester_schemas.dataset_schemas.__dataset_schema import _DatasetSchema

__author__ = 'Casey Bajema'


class SOSDatasetSchema(_DatasetSchema):
    data_source = SOSDataSource()
    data_type = FileDataEntrySchema()