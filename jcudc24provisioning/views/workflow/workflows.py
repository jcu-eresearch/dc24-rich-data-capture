import copy
from string import split
import string
import colander
from deform.exception import ValidationFailure
from deform.form import Form
from jcudc24ingesterapi.authentication import CredentialsAuthentication
from jcudc24ingesterapi.ingester_platform_api import IngesterPlatformAPI
from jcudc24provisioning.models.common_schemas import SelectMappingSchema
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config
from colanderalchemy.types import SQLAlchemyMapping
from jcudc24provisioning.views.layouts import Layouts
from pyramid.renderers import get_renderer
from jcudc24provisioning.models.project import DBSession, Project, Method, Base, Party, Dataset, MethodSchema
from jcudc24provisioning.views.scripts import convert_schema, create_sqlalchemy_model, convert_sqlalchemy_model_to_data
from jcudc24provisioning.scripts.ingesterapi_wrapper import IngesterAPIWrapper

__author__ = 'Casey Bajema'

WORKFLOW_STEPS = [
        {'href': 'setup', 'title': 'Setup'},
        {'href': 'description', 'title': 'Description'},
        {'href': 'metadata', 'title': 'Information'},
        {'href': 'methods', 'title': 'Methods'},
        {'href': 'datasets', 'title': 'Datasets'},
        {'href': 'submit', 'title': 'Submit & Approval'},
]

redirect_options = """
        {success:
                  function (rText, sText, xhr, form) {
                    alert('here');
                    var loc = xhr.getResponseHeader('X-Relocate');
                    if (loc) {
                      document.location = loc;
                    };
                   }
                }
                """

class Workflows(Layouts):
    def __init__(self, request):
        self.request = request

    @reify
    def workflow_menu(self):
        new_menu = WORKFLOW_STEPS[:]
        url = split(self.request.url, "?")[0]
        for menu in new_menu:
            menu['current'] = url.endswith(menu['href'])
        return new_menu

    @reify
    def workflow_template(self):
        renderer = get_renderer("../../templates/workflow_template.pt")
        return renderer.implementation().macros['layout']

    @reify
    def isDelete(self):
        return 'Delete' in self.request.POST

    def save_form(self, data):
         session = DBSession
         if data['id'] == -1 or data['id'] == colander.null:
             data.pop('id')
             model = create_sqlalchemy_model(data, model_class=Project)
             if model is not None:
                 session.add(model)
                 session.commit()
                 data['id'] = model.id
         else:
             model = session.query(Project).filter_by(id=data['id']).first()

             # Update the model with all fields in the data
             if create_sqlalchemy_model(data, model_object=model) is not None:
                 session.commit()
#             for key in data:
#                 if hasattr(model, key):
#                     setattr(model, key,data[key])
#                 else:
#                     print "Error: Trying to add invalid column to database"



    def handle_request(self):
        controls = self.request.POST.items()

        # If the form is being saved (there would be 1 item in controls if it is a fresh page with a project id set)
        if len(controls) > 0:
            # In either of the below cases get the data as a dict and get the rendered form
            try:
                appstruct = self.form.validate(controls)
                form = self.form.render(appstruct)
            except ValidationFailure, e:
                appstruct = e.cstruct
                form = e.render()

            # save the data even if it didn't validate - this allows the user to easily navigate and fill fields out as they get the info.
            self.save_form(appstruct)

            # If there is a target workflow step set then change to that page.
            if self.request.POST['target']:
                location = self.request.application_url + '/' + self.request.POST['target']
                if self.form.use_ajax:
                    return {"page_title": 'Project Setup', "form": form, "form_only": self.form.use_ajax, 'messages' : None}
                else:
                    if 'id' in appstruct:
                        location += '?id=' + str(appstruct['id'])
                    return HTTPFound(location=location)

            return {"page_title": 'Project Setup', "form": form, "form_only": self.form.use_ajax, 'messages' : self.request.session.pop_flash() or ''}

        # If the page has just been opened but it is set to a specific project
        appstruct = {}

        if 'id' in self.request.GET:
            project_id = int(self.request.GET['id'])
            session = DBSession
            model = session.query(Project).filter_by(id=project_id).first()
            appstruct = convert_sqlalchemy_model_to_data(model, self.schema)

        return {"page_title": self.title, "form": self.form.render(appstruct), "form_only": False, 'messages' : self.request.session.pop_flash() or ''}


class SetupViews(Workflows):
    title = "Project Setup"

    def __init__(self, request):
        self.request = request
        self.schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise', ca_description="TODO: Restrict navigation to other steps until the setup page is adequately completed."), page='setup').bind(request=request)
        self.form = Form(self.schema, action="setup", buttons=('Save',), use_ajax=False, ajax_options=redirect_options)

    @view_config(renderer="../../templates/form.pt", name="setup")
    def handle_request(self):
        controls = self.request.POST.items()

        # If the form is being saved (there would be 1 item in controls if it is a fresh page with a project id set)
        if len(controls) > 0:
            # In either of the below cases get the data as a dict and get the rendered form
            try:
                appstruct = self.form.validate(controls)
            except ValidationFailure, e:
                if 'target' in self.request.POST:
                    self.request.POST['target'] = ''
                    self.request.session.flash('Valid project setup data must be entered before entering more data.')

        return super(SetupViews, self).handle_request()


class DescriptionView(Workflows):
    title = "Description"

    def __init__(self, request):
        self.request = request
        self.schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise',
            ca_description="Fully describe your project to encourage other researchers to reuse your data:"\
                                       "<ul><li>The entered descriptions will be used for metadata record generation (ReDBox), provide detailed information that is relevant to the project as a whole.</li>"\
                                       "<li>Focus on what is being researched, why it is being researched and who is doing the research. The research locations and how the research is being conducted will be covered in the <i>Methods</i> and <i>Datasets</i> steps later on.</li></ul>"
        ), page="description").bind(
            request=request)

        self.form = Form(self.schema, action="description", buttons=('Save',), use_ajax=False)

    @view_config(renderer="../../templates/form.pt", name="description")
    def handle_request(self):
        return super(DescriptionView, self).handle_request()

class MetadataView(Workflows):
    title = "Metadata"

    def __init__(self, request):
        self.request = request
        self.schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise', ca_description="<b>Please fill this section out completely</b> - it's purpose is to provide the majority of information for all generated metadata records so that you don't have to enter the same data more than once:"\
                                                                                                     "<ul><li>A metadata record (ReDBox) will be created for the entire project using the entered information directly.</li>"\
                                                                                                     "<li>A metadata record (ReDBox) will be created for each dataset using a combination of the below information and the information entered in the <i>Methods</i> and <i>Datasets</i> steps.</li>"\
                                                                                                     "<li>Once the project has been submitted and accepted the metadata records will be generated and exported, any further alterations will need to be entered for each record in ReDBox-Mint.</li>"\
                                                                                                     "<li>If specific datasets require additional metadata that cannot be entered through these forms, you can enter it directly in the ReDBox-Mint records once the project is submitted and accepted (Look under <i>[to be worked out]</i> for a link).</li>"\
                                                                                                     "</ul>"), page='metadata').bind(request=request)
        self.form = Form(self.schema, action="metadata", buttons=('Save',), use_ajax=False)

    @view_config(renderer="../../templates/form.pt", name="metadata")
    def handle_request(self):
        return super(MetadataView, self).handle_request()

class MethodsView(Workflows):
    title = "Methods"

    def __init__(self, request):
        self.request = request
        self.session = DBSession

#    @reify
#    def get_schema(self, schema_id):
#        return self.session.query(MethodSchema).filter_by(id=schema_id).first()
#
    def get_template_schemas(self):
        return self.session.query(MethodSchema).filter_by(template_schema=1).all()
#
#    @reify
#    def get_shared_schemas(self):
#        return self.session.query(MethodSchema).filter_by(share_schema=1).all()
#
#    @reify
#    def get_own_schemas(self):
#        return self.session.query(Project).join(Method).join(MethodSchema).\
#        filter(Project.project_creator==self.user_id).\
#        all()

    @view_config(renderer="../../templates/form.pt", name="methods")
    def handle_request(self):
        self.schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise', ca_description="Setup methods the project uses for collecting data (not individual datasets themselves as they will be setup in the next step).  Such that a type of sensor that is used to collect temperature at numerous sites would be setup: <ol><li>Once within this step as a data method</li><li>As well as for each site it is used at in the next step</li></ol>This means you don't have to enter duplicate data!"), page="methods").bind(request=self.request)

        self.schema.children[3].children[0].children[5].children[5].template_schemas = self.get_template_schemas()
        self.form = Form(self.schema, action="methods", buttons=('Save',), use_ajax=False)

        return super(MethodsView, self).handle_request()

class DatasetsView(Workflows):
    title = "Datasets"

    def __init__(self, request):
        self.request = request

    @view_config(renderer="../../templates/form.pt", name="datasets")
    def handle_request(self):
#        if 'id' in self.request.POST.items():
#            project_id = self.request.POST['id']
#            session = DBSession
#            print self.form
#            self.form.methods = session.query(Method).filter_by(project_id=project_id).all()

        self.schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise', ca_description="Add individual datasets that your project will be collecting.  This is the when and where using the selected data collection method (what, why and how).  Such that an iButton sensor that is used to collect temperature at numerous sites would have been setup once within the Methods step and should be set-up in this step for each site it is used at."), page="datasets").bind(request=self.request)
        dataset_items = self.schema.children[2].children[0].children

        if 'id' in self.request.GET:
            id = int(self.request.GET['id'])
            session = DBSession
            methods = session.query(Method).filter_by(project_id=id).all()

            method_schemas = []
            for method in methods:
                method_children = convert_schema(SQLAlchemyMapping(Dataset, unknown='raise')).children

                if method.data_source is not None:
                    for data_source in method_children[4].children:
                        if data_source.name == method.data_source:
                            method_children[4].children = [data_source]
                            break
                else:
                    method_children[4].children = []

                for child in method_children:
                    if child.name == 'method_id':
                        child.default = method.id
                        break

                method_schemas.append(colander.MappingSchema(*method_children, name=(method.method_name and method.method_name or 'Un-named')))

            method_select_schema = SelectMappingSchema(*method_schemas, title="Method")
        else:
            method_select_schema = SelectMappingSchema(title="Method")

        self.schema.children[2].children[0].children = [method_select_schema]
        self.form = Form(self.schema, action="datasets", buttons=('Save',), use_ajax=False)

        return super(DatasetsView, self).handle_request()

class SubmitView(Workflows):
    title = "Submit"

    def __init__(self, request):
        self.request = request
        self.schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise',
            ca_description="TODO: The submission and approval should both follow a process of:"
                           "<ol><li>Automated validation</li>"
                           "<li>User fixes validation errors</li>"
                           "<li>Reminders/action items for users to complete that can't be auto-validated</li>"
                           "<li>Final confirmation and approval</li>"
                           "<li>Recommendations and next steps</li></ol><br />"
                "<b>Save:</b> Save the project as is, it doesn't need to be fully complete or valid.<br/><br/>"\
                "<b>Delete:</b> Delete the project, this can only be performed by administrators or before the project has been submitted.<br/><br/>"\
                "<b>Submit:</b> Submit this project for admin approval. If there are no problems the project data will be used to create ReDBox-Mint records as well as configuring data ingestion into persistent storage<br/><br/>"\
                "<b>Reopen:</b> Reopen the project for editing, this can only occur when the project has been submitted but not yet accepted (eg. the project may require updates before being approved)<br/><br/>" \
                "<b>Approve:</b> Approve this project, generate metadata records and setup data ingestion<br/><br/>" \
                "<b>Disable:</b> Stop data ingestion, this would usually occur once the project has finished."), page="submit").bind(request=request)
        self.form = Form(self.schema, action="submit", buttons=('Save', 'Delete', 'Submit', 'Reopen', 'Approve', 'Disable'), use_ajax=False)

    @view_config(renderer="../../templates/form.pt", name="submit")
    def handle_request(self):
        if 'Approve' in self.request.POST and 'id' in self.request.POST:
            print self.request.POST
            project_id = int(self.request.POST['id'])
            session = DBSession
            project = session.query(Project).filter_by(id=project_id).first()

            auth = CredentialsAuthentication("casey", "password")
            ingester_api = IngesterAPIWrapper("http://localhost:8080/api", auth)

            ingester_api.post(project)
            ingester_api.close()

            print 'project approved - TODO: Success message'

        return super(SubmitView, self).handle_request()