import deform

__author__ = 'Casey Bajema'

import colander
from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.view import view_config
from layouts import Layouts

types = (('form', 'Form'),('video', 'Video'), ('audio', 'Audio'), ('file', 'File'), ('sensor', 'Sensor'))

class DataInputData(colander.MappingSchema):
    description = colander.SchemaNode(colander.String())
    timePeriod = colander.SchemaNode(colander.String(), title="Time Period (Descriptive)")
    dateFrom = colander.SchemaNode(colander.Date(), default="", title="Date From",widget=deform.widget.DatePartsWidget(),description='Date data will start being collected')
    dateTo = colander.SchemaNode(colander.Date(), default="", title="Date To",widget=deform.widget.DatePartsWidget(),description='Date data will stop being collected')

    researchLocation = colander.SchemaNode(colander.String(), default="To be redeveloped similar to ReDBox")

    expectedDataSize = colander.SchemaNode(colander.Integer(), title="Expected Data Size")
    dataType = colander.SchemaNode(colander.String(), title="Data Type", widget=deform.widget.SelectWidget(values=types), validator=colander.OneOf(['Form','Video', 'Audio', 'File', 'Sensor']))

    videoURL = colander.SchemaNode(colander.String(), title="Audio\Video URL")
    sampleStart = colander.SchemaNode(colander.String(), title="Sampling Start Conditions")
    sampleStop = colander.SchemaNode(colander.String(), title="Sampling Stop Conditions")

    sosID = colander.SchemaNode(colander.String(), title="Sensor ID (SOS)", validator=colander.OneOf(['1','2', '3', '4', '5']))

    customProcessor = colander.SchemaNode(colander.String(), title="Upload custom processing script")

class DataInputSchemas(colander.SequenceSchema):
    dataSource = DataInputData()

class Schema(colander.Schema):
    dataInputs = DataInputSchemas()

class DataInputsView(Layouts):
    def __init__(self, request):
        self.request = request

    @view_config(renderer="../templates/data_inputs.pt", name="data_inputs")
    def setup_view(self):
        schema = Schema()
        myform = Form(schema, buttons=('submit',))

        if 'submit' in self.request.POST:
            controls = self.request.POST.items()
            try:
                appstruct = myform.validate(controls)
            except ValidationFailure, e:
                return {"page_title": 'Data Inputs', 'form': e.render(), 'values': False}
                # Process the valid form data, do some work
            values = {
                "name": appstruct['name'],
                "shoe_size": appstruct['shoe_size'],
                }
            return {"page_title": 'Data Inputs', "form": myform.render(), "values": values}

        # We are a GET not a POST
        return {"page_title": 'Data Inputs', "form": myform.render(), "values": None}

