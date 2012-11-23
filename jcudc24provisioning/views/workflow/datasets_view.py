from colanderalchemy.declarative import Column
from colanderalchemy.types import SQLAlchemyMapping
import deform
from pyramid.response import Response
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import ForeignKey
from sqlalchemy.types import Unicode, Integer, Enum
from jcudc24provisioning.views.schemas.dataset_schema import MethodSelectSchema, DatasetSchema
from jcudc24provisioning.views.workflow.workflows import Workflows
from jcudc24provisioning.models import DBSession, MyModel, Base

__author__ = 'Casey Bajema'

from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.view import view_config

class DatasetsView(Workflows):
    title = "Datasets"

    options = """
            {success:
              function (rText, sText, xhr, form) {
                var loc = xhr.getResponseHeader('X-Relocate');
                if (loc) {
                  document.location = loc;
                };
               }
            }
            """

    def __init__(self, request):
        self.request = request
        self.schema = SQLAlchemyMapping(DatasetSchema, unknown='raise', ca_description="Add individual datasets that your project will be collecting.  This is the when and where using the selected data collection method (what, why and how).  Such that an iButton sensor that is used to collect temperature at numerous sites would have been setup once within the Methods step and should be set-up in this step for each site it is used at.").bind(request=request)
        self.form = Form(self.schema, action="datasets", buttons=('Save', 'Delete'), use_ajax=True, ajax_options=self.options)

    @view_config(renderer="../../templates/form.pt", name="datasets")
    def datasets_view(self):

        if self.request.POST.get('Delete') == 'confirmed':
            location = self.request.application_url + '/'
            message = 'Project successfully deleted'
            return Response(self.form.render(),
                headers=[('X-Relocate', location), ('Content-Type', 'text/html'), ('msg', message)])

        if 'Save' in self.request.POST:
            controls = self.request.POST.items()
    #        print "Controls: " + str(controls)
            try:
                appstruct = self.form.validate(controls)
    #            print "appstruct: " + str(appstruct)
            except ValidationFailure, e:
                return  {"page_title": 'Datasets', 'form': e.render(), "form_only": self.form.use_ajax}

            # Process the valid form data, do some work
            return {"page_title": 'Datasets', "form": self.form.render(appstruct), "form_only": self.form.use_ajax}

#        DBSession.add(MyModel("asdf","asdf"))

        return {"page_title": 'Datasets', "form": self.form.render(), "form_only": False}

