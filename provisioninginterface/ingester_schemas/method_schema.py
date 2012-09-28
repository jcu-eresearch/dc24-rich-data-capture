from ingester_schemas.schema_data import SchemaData
from ingester_schemas.dataset_schema import DatasetSchema
import string
from ingester_schemas.__dataset_schema import _DatasetSchema
from sqlalchemy.dialects.mssql.base import VARCHAR, TEXT
from ingester_schemas.type_schema import TypeSchema
from sqlalchemy.dialects.mysql.base import INTEGER
from ingester_schemas.data_entry_schemas.file_data_entry_schema import FileDataEntrySchema
from ingester_schemas.data_entry_schemas.file_type import FileType

__author__ = 'Casey Bajema'

class MethodSchema():
        project_id = INTEGER()
        dataset_schema = _DatasetSchema()
        name = VARCHAR(250)
        description = TEXT()
        further_information = VARCHAR(250)()
        attachments = FileType()()
        datasets = _DatasetSchema()()



