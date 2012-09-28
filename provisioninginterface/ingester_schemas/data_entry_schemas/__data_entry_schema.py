from sqlalchemy.dialects.mysql.base import INTEGER
from sqlalchemy.types import DATETIME
from ingester_schemas.data_entry_schemas.quality_schema import QualitySchema

__author__ = 'Casey Bajema'

class _DataEntrySchema():
    note = ""
    dataset_id = INTEGER()
    datetime = DATETIME() # TODO: Check that this is the correct type
    quality = QualitySchema()
