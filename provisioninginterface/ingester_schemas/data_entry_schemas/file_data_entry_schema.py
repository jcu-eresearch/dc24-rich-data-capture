from ingester_schemas.data_schema import _DataSchema
from ingester_schemas.quality_schema import QualitySchema
from ingester_schemas.data_types.file_data_type_schema import FileDataTypeSchema
from sqlalchemy.dialects.mysql.base import VARCHAR
from ingester_schemas.data_entry_schemas.file_type import FileType

__author__ = 'Casey Bajema'

class FileDataEntrySchema(_DataSchema):
    file = FileType()





