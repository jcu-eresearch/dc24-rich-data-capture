from sqlalchemy.dialects.mysql.base import VARCHAR
from sqlalchemy.engine.url import URL
from ingester_schemas.data_entry_schemas.file_data_entry_schema import FileDataEntrySchema
from ingester_schemas.data_sources.pull_data_source import PullDataSource
from ingester_schemas.dataset_schemas.__dataset_schema import _DatasetSchema
from ingester_schemas.dataset_schemas.sampling_schema import SamplingSchema

__author__ = 'Casey Bajema'


class PullFileDatasetSchema(_DatasetSchema):
    data_source = PullDataSource()
    file_server = VARCHAR(250)
    sampling = SamplingSchema()
    data_type = FileDataEntrySchema()

