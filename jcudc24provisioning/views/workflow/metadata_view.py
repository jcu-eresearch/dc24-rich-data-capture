from pyramid.response import Response
from jcudc24provisioning.views.schemas.metadata_schema import MetadataData
from jcudc24provisioning.views.workflow.workflows import Workflows
from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.view import view_config

__author__ = 'Casey Bajema'

class MetadataView(Workflows):
    title = "Metadata"

    def __init__(self, request):
        self.request = request
        self.schema = MetadataData()
        self.myform = Form(self.schema, action="metadata_submit", buttons=('Save', 'Delete'), use_ajax=True)

    @view_config(renderer="../../templates/submit.pt", name="metadata_submit")
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
            return  {"page_title": 'Metadata', 'form': e.render(), 'values': False}
            # Process the valid form data, do some work
        return {"page_title": 'Metadata', "form": self.myform.render(appstruct)}

    @view_config(renderer="../../templates/metadata.pt", name="metadata")
    def metadata_view(self):
        return {"page_title": 'Metadata', "form": self.myform.render(), "values": None}

