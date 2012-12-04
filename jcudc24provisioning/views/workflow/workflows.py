from string import split
import colander
from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config
from colanderalchemy.types import SQLAlchemyMapping
from jcudc24provisioning.views.layouts import Layouts
from pyramid.renderers import get_renderer
from models.dataset_schema import DatasetSchema
from models.method_schema import MethodsSchema
from models.project import DBSession, ProjectSchema
from views.scripts import convert_schema

__author__ = 'Casey Bajema'

WORKFLOW_STEPS = [
        {'href': 'setup', 'title': 'Project Setup'},
        {'href': 'description', 'title': 'Description'},
        {'href': 'metadata', 'title': 'Metadata'},
        {'href': 'methods', 'title': 'Methods'},
        {'href': 'datasets', 'title': 'Datasets'},
        {'href': 'submit', 'title': 'Submit'},
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

    def is_form_empty(self, appstruct):
        for key in appstruct:
            if appstruct[key] is not None and appstruct[key] is not colander.null:
                return False

        return True

    def save_form(self, data):
         session = DBSession
         if data['id'] == -1:
             data.pop('id')
             if not self.is_form_empty(data):
                 model = ProjectSchema()
                 model.__dict__.update(data)
                 session.add(model)
                 session.commit()
                 data['id'] = model.id
         else:
             model = session.query(ProjectSchema).filter_by(id=data['id']).first()
             for key in data:
                 if hasattr(model, key):
                     setattr(model, key,data[key])
                 else:
                     print "Error: Trying to add invalid column to database"
             session.commit()

    def handle_request(self):
        controls = self.request.POST.items()

        # If the form is being saved (there would be 1 item in controls if it is a fresh page with a project id set)
        if len(controls) > 1:
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
                    return {"page_title": 'Project Setup', "form": form, "form_only": self.form.use_ajax}
                else:
                    return HTTPFound(location=location)

            return {"page_title": 'Project Setup', "form": form, "form_only": self.form.use_ajax}

        # If the page has just been opened but it is set to a specific project
        appstruct = {}
        for item in controls:
            if item[0] == 'id':
                id = item[1]
                session = DBSession
                model = session.query(ProjectSchema).filter_by(id=id).first()
                for node in self.schema.children:
                    appstruct[node.name] = model.__dict__[node.name]

        return {"page_title": self.title, "form": self.form.render(appstruct), "form_only": False}


class SetupViews(Workflows):
    title = "Project Setup"

    def __init__(self, request):
        self.request = request
        self.schema = convert_schema(SQLAlchemyMapping(ProjectSchema, unknown='raise', ca_description=""), page='setup').bind(request=request)
        self.form = Form(self.schema, action="setup", buttons=('Save',), use_ajax=False, ajax_options=redirect_options)

    @view_config(renderer="../../templates/form.pt", name="setup")
    def handle_request(self):
        return super(SetupViews, self).handle_request()


class DescriptionView(Workflows):
    title = "Description"

    def __init__(self, request):
        self.request = request
        self.schema = convert_schema(SQLAlchemyMapping(ProjectSchema, unknown='raise',
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
        self.schema = convert_schema(SQLAlchemyMapping(ProjectSchema, unknown='raise', ca_description="<b>Please fill this section out completely</b> - it's purpose is to provide the majority of information for all generated metadata records so that you don't have to enter the same data more than once:"\
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
        self.schema = convert_schema(SQLAlchemyMapping(ProjectSchema, unknown='raise', ca_description="Setup methods the project uses for collecting data (not individual datasets themselves as they will be setup in the next step).  Such that a type of sensor that is used to collect temperature at numerous sites would be setup <ol><li>Once within this step as a data method</li><li>As well as for each site it is used at in the next step</li></ol>This means you don't have to enter duplicate data!"), page="methods").bind(request=request)
        self.form = Form(self.schema, action="methods", buttons=('Save',), use_ajax=False)


    @view_config(renderer="../../templates/form.pt", name="methods")
    def handle_request(self):
        return super(MethodsView, self).handle_request()

class DatasetsView(Workflows):
    title = "Datasets"

    def __init__(self, request):
        self.request = request
        self.schema = convert_schema(SQLAlchemyMapping(ProjectSchema, unknown='raise', ca_description="Add individual datasets that your project will be collecting.  This is the when and where using the selected data collection method (what, why and how).  Such that an iButton sensor that is used to collect temperature at numerous sites would have been setup once within the Methods step and should be set-up in this step for each site it is used at."), page="datasets").bind(request=request)
        self.form = Form(self.schema, action="datasets", buttons=('Save',), use_ajax=False)

    @view_config(renderer="../../templates/form.pt", name="datasets")
    def handle_request(self):
        return super(DatasetsView, self).handle_request()

class SubmitView(Workflows):
    title = "Submit"

    def __init__(self, request):
        self.request = request
        self.schema = convert_schema(SQLAlchemyMapping(ProjectSchema, unknown='raise', ca_description="<b>Save:</b> Save the project as is, it doesn't need to be fully complete or valid.<br/><br/>"\
                                                "<b>Delete:</b> Delete the project, this can only be performed by administrators or before the project has been submitted.<br/><br/>"\
                                                "<b>Submit:</b> Submit this project for admin approval. If there are no problems the project data will be used to create ReDBox-Mint records as well as configuring data ingestion into persistent storage<br/><br/>"\
                                                "<b>Reopen:</b> Reopen the project for editing, this can only occur when the project has been submitted but not yet accepted (eg. the project may require updates before being approved)<br/><br/>" \
                                                "<b>Approve:</b> Approve this project, generate metadata records and setup data ingestion<br/><br/>" \
                                                "<b>Disable:</b> Stop data ingestion, this would usually occur once the project has finished."), page="submit").bind(request=request)
        self.form = Form(self.schema, action="submit", buttons=('Save', 'Delete', 'Submit', 'Reopen', 'Approve', 'Disable'), use_ajax=False)

    @view_config(renderer="../../templates/form.pt", name="submit")
    def handle_request(self):
        return super(SubmitView, self).handle_request()