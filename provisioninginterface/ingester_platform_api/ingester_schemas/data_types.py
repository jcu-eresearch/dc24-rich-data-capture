from sqlalchemy.dialects.mysql.base import VARCHAR

__author__ = 'Casey Bajema'

"""
    Base data type schema defines an empty dictionary that can have fields added to it dynamically,
    these fields will then be used by the ingester platform to setup the required table.

    Field names map to table column names
    Field values should be sqlalchemy data types defining the database column data type

    Note: ForeignKey or other table links are not supported, only single, flat tables are supported.
"""
class DataType(dict):
    pass


"""
    This schema extends the base _DataType schema and additionally defines that data will be stored as a
    flat file and each data_entry will provide the file mime_type and the file handle.

    Ingesters that want to index additional data should add fields to this schema and provide
    a custom processing script to extract that data.
"""
class FileDataType(DataType):
    mime_type = VARCHAR(100)   # eg. text/xml
    file_handle = VARCHAR(500) # URL (eg. file://c:/test_file.txt)





