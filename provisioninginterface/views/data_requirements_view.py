import deform
import colander
from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.view import view_config
from layouts import Layouts

__author__ = 'Casey Bajema'

types = (('form', 'Form'),('video', 'Video'), ('audio', 'Audio'), ('file', 'File'), ('sensor', 'Sensor'))

class DataSource(colander.Schema):
    description = colander.SchemaNode(colander.String(), title="Description")
    dataType = colander.SchemaNode(colander.String(), title="Data Type", widget=deform.widget.SelectWidget(values=types), validator=colander.OneOf(['Form','Video', 'Audio', 'File', 'Sensor']))
    attach = colander.SchemaNode(colander.String(), title='Attachment (eg. datasheet)')
    url = colander.SchemaNode(colander.String(), title='URL')
    contact = colander.SchemaNode(colander.String(), title='Contact')
    storage = colander.SchemaNode(colander.String(), title="Storage schema - todo")

class DataSchemas(colander.SequenceSchema):
    dataSource = DataSource()

class Schema(colander.Schema):
    dataSources = DataSchemas()

class DataRequirementsView(Layouts):
    def __init__(self, request):
        self.request = request

    @view_config(renderer="../templates/data_requirements.pt", name="data_requirements")
    def setup_view(self):
        schema = Schema()
        myform = Form(schema, buttons=('submit',))

        if 'submit' in self.request.POST:
            controls = self.request.POST.items()
            try:
                appstruct = myform.validate(controls)
            except ValidationFailure, e:
                return {"page_title": 'Data Requirements', 'form': e.render(), 'values': False}
                # Process the valid form data, do some work
            values = {
                "name": appstruct['name'],
                "shoe_size": appstruct['shoe_size'],
                }
            return {"page_title": 'Data Requirements', "form": myform.render(), "values": values}

        # We are a GET not a POST
        return {"page_title": 'Data Requirements', "form": myform.render(), "values": None}

