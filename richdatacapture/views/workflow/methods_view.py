from pickle import dump
import deform
import colander
from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.response import Response
from pyramid.view import view_config
from layouts import Layouts
from views.schemas.method_schema import DataSource
from views.workflow.workflows import Workflows, MemoryTmpStore

__author__ = 'Casey Bajema'


class DataSchemas(colander.SequenceSchema):
    dataSource = DataSource(title="Data collection method")

class MethodsSchema(colander.Schema):
    description = colander.SchemaNode(colander.String(), title="Overall methods description",
        widget=deform.widget.TextAreaWidget(rows=5),
        default="Provide an overview of all the data collection methods used in the project why those methods were chosen."
        ,
        description="Provide a description for all data input methods used in the project.  This will be used as the description for data collection in the project metadata record and will provide users of your data with an overview of what the project is researching.")
    dataSources = DataSchemas(title="Methods", widget=deform.widget.SequenceWidget(min_len=1),
        description="Add 1 method for each type of data collection method (eg. streaming temperature sensors, field observations using a form and file uploads from iButton sensors...)")

class MethodsView(Workflows):
    title = "Methods"

    def __init__(self, request):
        self.request = request
        self.schema = MethodsSchema(
            description="Setup methods (or ways of) the project uses for collecting data, not individual datasets themselves (that will be done in the next step).  Such that an iButton sensor that is used to collect temperature at numerous sites would be setup once within this step as a data method and for each site it is used at in the next step (This means you don't have to enter duplicate data!).")
        self.myform = Form(self.schema, action="methods_submit", buttons=('Save', 'Delete'), use_ajax=True)

    @view_config(renderer="../../templates/submit.pt", name="methods_submit")
    def methods_submit(self):
        if self.request.POST.get('Delete') == 'confirmed':
            location = self.request.application_url + '/'
            message = 'Project successfully deleted'
            return Response(self.myform.render(),
                headers=[('X-Relocate', location), ('Content-Type', 'text/html'), ('msg', message)])

        controls = self.request.POST.items()
        try:
            appstruct = self.myform.validate(controls)
        except ValidationFailure, e:
            return  {"page_title": 'Methods', 'form': e.render(), 'values': False}
            # Process the valid form data, do some work
        return {"page_title": 'Methods', "form": self.myform.render(appstruct)}

    @view_config(renderer="../../templates/methods.pt", name="methods")
    def methods_view(self):
        return {"page_title": 'Methods', "form": self.myform.render(), "values": None}

