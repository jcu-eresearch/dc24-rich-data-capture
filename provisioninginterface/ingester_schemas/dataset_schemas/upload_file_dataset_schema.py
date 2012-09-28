from ingester_schemas.data_entry_schemas.file_data_entry_schema import FileDataEntrySchema
from ingester_schemas.dataset_schemas.__dataset_schema import _DatasetSchema
from ingester_schemas.dataset_schemas.pull_data_source import PullDataSource
from ingester_schemas.dataset_schemas.upload_data_source import UploadDataSource

__author__ = 'Casey Bajema'

class UploadFileDatasetSchema(_DatasetSchema):
    data_source = UploadDataSource()
    data_type = FileDataEntrySchema()