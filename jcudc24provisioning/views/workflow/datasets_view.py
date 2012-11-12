from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from jcudc24provisioning.views.schemas.dataset_schema import MethodSelectSchema, DatasetSchema
from jcudc24provisioning.views.workflow.workflows import Workflows

__author__ = 'Casey Bajema'

from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.view import view_config

class DatasetsView(Workflows):
    title = "Datasets"

    def __init__(self, request):
        self.request = request
        self.schema = DatasetSchema(description="Add individual datasets that your project will be collecting.  This is the when and where using the selected data collection method (what, why and how).  Such that an iButton sensor that is used to collect temperature at numerous sites would have been setup once within the Methods step and should be set-up in this step for each site it is used at.").bind(request=request)
        self.myform = Form(self.schema, action="submit_datasets", buttons=('Save', 'Delete'), use_ajax=False)

    @view_config(renderer="../../templates/datasets.pt", name="submit_datasets")   # Use ../../templates/submit.pt for AJAX - File upload doesn't work due to jquery/deform limitations
    def submit(self):
        if self.request.POST.get('Delete') == 'confirmed':
            location = self.request.application_url + '/'
            message = 'Project successfully deleted'
            return Response(self.myform.render(),
                headers=[('X-Relocate', location), ('Content-Type', 'text/html'), ('msg', message)])

        controls = self.request.POST.items()
#        print "Controls: " + str(controls)
        try:
            appstruct = self.myform.validate(controls)
#            print "appstruct: " + str(appstruct)
        except ValidationFailure, e:
            return  {"page_title": 'Datasets', 'form': e.render()}

        # Process the valid form data, do some work
        return {"page_title": 'Datasets', "form": self.myform.render(appstruct)}

    @view_config(renderer="../../templates/datasets.pt", name="datasets")
    def datasets_view(self):
        return {"page_title": 'Datasets', "form": self.myform.render()}

