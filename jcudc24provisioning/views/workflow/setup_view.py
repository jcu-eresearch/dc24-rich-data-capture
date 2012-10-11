from pyramid.response import Response
from jcudc24provisioning.views.schemas.setup_schema import setup_schema
from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.view import view_config
from jcudc24provisioning.views.workflow.workflows import Workflows

__author__ = 'Casey Bajema'

class SetupViews(Workflows):
    title = "Project Setup"

    def __init__(self, request):
        self.request = request
        self.schema = setup_schema()
        self.myform = Form(self.schema, action="setup_submit", buttons=('Save', 'Delete'), use_ajax=True)

    @view_config(renderer="../../templates/submit.pt", name="setup_submit")
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
            return  {"page_title": 'Project Setup', 'form': e.render(), 'values': False}
            # Process the valid form data, do some work
        return {"page_title": 'Project Setup', "form": self.myform.render(appstruct)}

    @view_config(renderer="../../templates/setup.pt", name="setup")
    def setup_view(self):
        return {"page_title": 'Project Setup', "form": self.myform.render()}
