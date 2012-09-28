from sqlalchemy.dialects.mysql.base import VARCHAR, DOUBLE

__author__ = 'Casey Bajema'

class QualitySchema():
    unit = VARCHAR(50)
    description = VARCHAR(250)
    value = DOUBLE()

