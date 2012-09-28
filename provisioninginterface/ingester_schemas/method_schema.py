from sqlalchemy.dialects.mysql.base import INTEGER, VARCHAR, TEXT
from ingester_schemas.data_entry_schemas.file_type import FileType
from ingester_schemas.dataset_schemas.__dataset_schema import _DatasetSchema

__author__ = 'Casey Bajema'

class MethodSchema():
        project_id = INTEGER()
        dataset_schema = _DatasetSchema()
        name = VARCHAR(250)
        description = TEXT()
        further_information = VARCHAR(250) # TODO: work out how to explain an array of set type
        attachments = FileType()  # TODO: work out how to explain an array of set type
        datasets = _DatasetSchema()  # TODO: work out how to explain an array of set type



