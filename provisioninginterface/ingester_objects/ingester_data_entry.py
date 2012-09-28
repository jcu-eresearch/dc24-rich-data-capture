__author__ = 'Casey Bajema'

class IngesterDataEntry():
    def __init__(self, schema, note = "", dataset_id = -1, datetime, quality = None, **kwargs):
        schema = schema
        note = note
        dataset_id = dataset_id
        datetime = datetime
        quality = quality

        #... Work out code for handling **kwargs and placing them into fields based on the schema passed in