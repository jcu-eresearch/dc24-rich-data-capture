import colander
import deform
from jcudc24provisioning.models.common_schemas import ConditionalCheckboxSchema
from jcudc24provisioning.views.workflow.workflows import Workflows

__author__ = 'Casey Bajema'

from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.view import view_config

class SelectIndividualdatasetsSchema(ConditionalCheckboxSchema):
    dataset_a = colander.SchemaNode(colander.Boolean())
    dataset_b = colander.SchemaNode(colander.Boolean())
    dataset_c = colander.SchemaNode(colander.Boolean())

class SelectIndividualMethodsSchema(ConditionalCheckboxSchema):
    method_a = colander.SchemaNode(colander.Boolean())
    method_b = colander.SchemaNode(colander.Boolean())
    method_c = colander.SchemaNode(colander.Boolean())

class AddUserSequence(colander.MappingSchema):
     general_information = colander.SchemaNode(colander.Boolean())
     metadata = colander.SchemaNode(colander.Boolean())
     methods = SelectIndividualMethodsSchema()
     datasets = SelectIndividualMethodsSchema()

class View(Workflows):
    title = "Duplicate project"

    def __init__(self, request):
        self.request = request
        self.schema = AddUserSequence(description="Create a new project that duplicates this one, select the items that should be duplicated below.<br /><br />" \
                                                  "<b>Note:  Datasets will only be duplicated if the method they use is also duplicated.</b>").bind(request=request)
        self.form = Form(self.schema, action="submit_duplicate", buttons=('Create',), use_ajax=False)

    @view_config(renderer="../../templates/form.pt", name="submit_duplicate")   # Use ../../templates/submit.pt for AJAX - File upload doesn't work due to jquery/deform limitations
    def submit(self):
        controls = self.request.POST.items()
        try:
            appstruct = self.form.validate(controls)
    #            print "appstruct: " + str(appstruct)
        except ValidationFailure, e:
            return  {"page_title": self.title, 'form': e.render(), "form_only": self.form.use_ajax}

        # Process the valid form data, do some work
#        self.form.buttons = ('Delete/Disable', 'Add metadata', 'View related', 'Add metadata type')
        return {"page_title": self.title, "form": self.form.render(appstruct), "form_only": self.form.use_ajax}

    @view_config(renderer="../../templates/form.pt", name="duplicate")
    def add_data_view(self):
        return {"page_title": self.title, "form": self.form.render(), "form_only": False}

