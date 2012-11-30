from colanderalchemy.types import SQLAlchemyMapping
from pyramid.response import Response
from jcudc24provisioning.models.metadata_schema import MetadataData
from jcudc24provisioning.views.workflow.workflows import Workflows
from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.view import view_config
from jcudc24provisioning.views.scripts import convert_schema

__author__ = 'Casey Bajema'

class MetadataView(Workflows):
    title = "Metadata"

    def __init__(self, request):
        self.request = request
        self.schema = convert_schema(SQLAlchemyMapping(MetadataData, unknown='raise', ca_description="<b>Please fill this section out completely</b> - it's purpose is to provide the majority of information for all generated metadata records so that you don't have to enter the same data more than once:"\
                                                                                                     "<ul><li>A metadata record will be created for the entire project using the entered information directly</li>"\
                                                                                                     "<li>A metadata record will be created for each dataset using a combination of the below information and the information entered in the <i>Methods</i> and <i>Datasets</i> steps</li>"\
                                                                                                     "<li>Once the project has been submitted and accepted the metadata records will be generated and exported, any further alterations will need to be entered for each record in ReDBox-Mint</li>"\
                                                                                                     "<li>If specific datasets require additional metadata that cannot be entered through these forms, you can enter it directly in the ReDBox-Mint records once the project is submitted and accepted (Look under <i>[to be worked out]</i> for a link)</li>"\
                                                                                                     "</ul>"), page='metadata').bind(request=request)
#        print self.schema.children
#        print self.schema.children[0].children
#        print self.schema.children[0].children[1]
#        print self.schema.children[0].children[1].children[0]
#        print self.schema.children[0].children[1].children[0].children
#        print self.schema.children[0].children[1].children[0].children[2]
#        print self.schema.children[0].children[1].children[0].children[2].__dict__
        self.form = Form(self.schema, action="metadata", buttons=('Save',), use_ajax=False)

    @view_config(renderer="../../templates/form.pt", name="metadata")
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
                return  {"page_title": 'Metadata', 'form': e.render(), "form_only": self.form.use_ajax}
                # Process the valid form data, do some work
            return {"page_title": 'Metadata', "form": self.form.render(appstruct), "form_only": self.form.use_ajax}

        return {"page_title": 'Metadata', "form": self.form.render(), "form_only": False}


