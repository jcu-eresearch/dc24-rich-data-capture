from ingester_schemas.data_entry_schemas.file_data_entry_schema import FileDataEntrySchema
from ingester_schemas.data_sources.upload_data_source import UploadDataSource
from ingester_schemas.dataset_schemas.__dataset_schema import _DatasetSchema
__author__ = 'Casey Bajema'

class UploadFileDatasetSchema(_DatasetSchema):
    data_source = UploadDataSource()
    data_type = FileDataEntrySchema()