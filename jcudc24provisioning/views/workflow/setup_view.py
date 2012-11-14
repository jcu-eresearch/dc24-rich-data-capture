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
        self.schema = setup_schema(description="Fully describe this project and the key people responsible for the project:" \
                                               "<ul><li>The entered title and description will be used for metadata record generation, provide detailed information that is relevant to the project as a whole and all datasets.</li>" \
                                               "<li>Focus on what is being researched, why it is being researched and who is doing the research. The research locations and how the research is being conducted will be covered in the <i>Methods</i> and <i>Datasets</i> steps</li></ul>").bind(request=request)
        self.form = Form(self.schema, action="submit_setup", buttons=('Save', 'Delete'), use_ajax=False)

    @view_config(renderer="../../templates/form.pt", name="submit_setup")     # Use ../../templates/submit.pt for AJAX - File upload doesn't work due to jquery/deform limitations
    def submit(self):
        if self.request.POST.get('Delete') == 'confirmed':
            location = self.request.application_url + '/'
            message = 'Project successfully deleted'
            return Response(self.form.render(),
                headers=[('X-Relocate', location), ('Content-Type', 'text/html'), ('msg', message)])

        controls = self.request.POST.items()
        try:
            appstruct = self.form.validate(controls)
        except ValidationFailure, e:
            return  {"page_title": 'Project Setup', 'form': e.render(), 'values': False}
            # Process the valid form data, do some work
        return {"page_title": 'Project Setup', "form": self.form.render(appstruct)}

    @view_config(renderer="../../templates/form.pt", name="setup")
    def setup_view(self):
        return {"page_title": 'Project Setup', "form": self.form.render()}
