from colanderalchemy.types import SQLAlchemyMapping
from pyramid.response import Response
from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.view import view_config
from jcudc24provisioning.views.workflow.workflows import Workflows
from jcudc24provisioning.views.workflow.setup_view import convert_schema
from jcudc24provisioning.models.project import ProjectSchema

__author__ = 'Casey Bajema'

class DescriptionView(Workflows):
    title = "Description"

    def __init__(self, request):
        self.request = request
        self.schema = convert_schema(SQLAlchemyMapping(ProjectSchema, unknown='raise',
            ca_description="Fully describe this project and the key people responsible for the project:"\
                                       "<ul><li>The entered title and description will be used for metadata record generation, provide detailed information that is relevant to the project as a whole and all datasets.</li>"\
                                       "<li>Focus on what is being researched, why it is being researched and who is doing the research. The research locations and how the research is being conducted will be covered in the <i>Methods</i> and <i>Datasets</i> steps</li></ul>"
        ), page="description").bind(
            request=request)

        self.form = Form(self.schema, action="description", buttons=('Save',), use_ajax=False)

    @view_config(renderer="../../templates/form.pt", name="description")
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
                return  {"page_title": 'Project Setup', 'form': e.render(), "form_only": self.form.use_ajax}
                # Process the valid form data, do some work
        return {"page_title": 'Project Setup', "form": self.form.render(), "form_only": False}
