from ingester_schemas.data_entry_schemas.form_data_schema import FormDataSchema
from ingester_schemas.data_sources.upload_data_source import UploadDataSource
from ingester_schemas.dataset_schemas.__dataset_schema import _DatasetSchema

__author__ = 'Casey Bajema'

class FormDatasetSchema(_DatasetSchema):
    data_source = UploadDataSource()
    data_type = FormDataSchema()
