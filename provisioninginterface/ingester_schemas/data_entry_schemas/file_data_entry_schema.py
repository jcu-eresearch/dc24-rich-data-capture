from ingester_schemas.data_entry_schemas.__data_entry_schema import _DataEntrySchema
from ingester_schemas.data_entry_schemas.file_type import FileType

__author__ = 'Casey Bajema'

class FileDataEntrySchema(_DataEntrySchema):
    file = FileType()





