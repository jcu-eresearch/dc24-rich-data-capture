from datetime import datetime
from sqlalchemy.dialects.mssql.base import TEXT, VARCHAR
from sqlalchemy.dialects.mysql.base import INTEGER, DOUBLE
from sqlalchemy.types import DATETIME

__author__ = 'Casey Bajema'

class _DatasetSchema():
    method_id = INTEGER()
    description = TEXT()
    time_description = VARCHAR(250)
    start_time = DATETIME()
    end_time = DATETIME()
    location_description = VARCHAR(250)
    latitude = DOUBLE()
    longitude = DOUBLE()
    processing_script = VARCHAR(250)




