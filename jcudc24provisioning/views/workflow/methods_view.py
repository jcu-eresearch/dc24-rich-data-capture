import deform
import colander
from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.response import Response
from pyramid.view import view_config
from jcudc24provisioning.views.workflow.workflows import Workflows
from jcudc24provisioning.views.schemas.method_schema import MethodsSchema

__author__ = 'Casey Bajema'


class MethodsView(Workflows):
    title = "Methods"

    def __init__(self, request):
        self.request = request
        self.schema = MethodsSchema(
            description="Setup methods (or ways of) the project uses for collecting data, not individual datasets themselves (that will be done in the next step).  Such that a type of iButton sensor that is used to collect temperature at numerous sites would be setup once within this step as a data method and for each site it is used at in the next step (This means you don't have to enter duplicate data!).").bind(request=request)
        self.myform = Form(self.schema, action="submit_methods", buttons=('Save', 'Delete'), use_ajax=False)

    @view_config(renderer="../../templates/methods.pt", name="submit_methods")     # Use ../../templates/submit.pt for AJAX - File upload doesn't work due to jquery/deform limitations
    def submit(self):
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

