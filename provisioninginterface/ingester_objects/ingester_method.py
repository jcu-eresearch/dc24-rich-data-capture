__author__ = 'Casey Bajema'

class IngesterMethod():
    def __init__(self, project_id = -1, name, dataset_schema, description = "", further_information = (), attachments = (), datasets = ()):
        self.project_id = project_id
        self.dataset_schema = dataset_schema
        self.name = name
        self.description = description
        self.further_information = further_information
        self.attachments = attachments
        self.datasets = datasets