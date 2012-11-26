import deform
import colander
from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.response import Response
from pyramid.view import view_config
from jcudc24provisioning.views.workflow.workflows import Workflows
from jcudc24provisioning.models.method_schema import MethodsSchema

__author__ = 'Casey Bajema'


class MethodsView(Workflows):
    title = "Methods"

    def __init__(self, request):
        self.request = request
        self.schema = MethodsSchema(
            description="Setup methods the project uses for collecting data (not individual datasets themselves as they will be setup in the next step).  Such that a type of sensor that is used to collect temperature at numerous sites would be setup <ol><li>Once within this step as a data method</li><li>As well as for each site it is used at in the next step</li></ol>This means you don't have to enter duplicate data!").bind(request=request)
        self.form = Form(self.schema, action="submit_methods", buttons=('Save',), use_ajax=False)


    @view_config(renderer="../../templates/form.pt", name="methods")
    def submit(self):
        if self.request.POST.get('Delete') == 'confirmed':
                        location = self.request.application_url + '/'
                        message = 'Project successfully deleted'
                        return Response(self.form.render(),
                            headers=[('X-Relocate', location), ('Content-Type', 'text/html'), ('msg', message)])

        if 'Save' in self.request.POST:
            controls = self.request.POST.items()
            try:
                appstruct = self.form.validate(controls)
            except ValidationFailure, e:
                return  {"page_title": 'Methods', 'form': e.render(), "form_only": self.form.use_ajax}
                # Process the valid form data, do some work
            return {"page_title": 'Methods', "form": self.form.render(appstruct), "form_only": self.form.use_ajax}

        return {"page_title": 'Methods', "form": self.form.render(), "form_only": False}


