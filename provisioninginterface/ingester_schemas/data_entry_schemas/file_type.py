from sqlalchemy.dialects.mysql.base import VARCHAR

__author__ = 'Casey Bajema'


class FileType():
    mime_type = VARCHAR(100)   # eg. text/xml
    file_handle = VARCHAR(500) # URL (eg. file://c:/test_file.txt)