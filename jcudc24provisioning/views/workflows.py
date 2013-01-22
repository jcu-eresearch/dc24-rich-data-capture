import ConfigParser
import copy
from datetime import datetime, date
import json
from string import split
import string
import urllib2
from sqlalchemy.orm.properties import ColumnProperty, RelationProperty
from sqlalchemy.orm.util import object_mapper
import colander
from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.url import route_url
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from pyramid_debugtoolbar.utils import logger
import time
import transaction
from jcudc24ingesterapi.authentication import CredentialsAuthentication
from jcudc24ingesterapi.ingester_platform_api import IngesterPlatformAPI
from jcudc24provisioning.models.common_schemas import SelectMappingSchema
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config, view_defaults
from colanderalchemy.types import SQLAlchemyMapping
from jcudc24provisioning.views.views import Layouts
from pyramid.renderers import get_renderer
from jcudc24provisioning.models.project import DBSession, ProjectTemplate, Project, CreatePage, Method, Base, Party, Dataset, MethodSchema, grant_validator, MethodTemplate
from jcudc24provisioning.views.ca_scripts import convert_schema, create_sqlalchemy_model, convert_sqlalchemy_model_to_data,fix_schema_field_name
from jcudc24provisioning.scripts.ingesterapi_wrapper import IngesterAPIWrapper
from jcudc24provisioning.views.mint_lookup import MintLookup


__author__ = 'Casey Bajema'

WORKFLOW_STEPS = [
        {'href': 'setup', 'title': 'Setup', 'page_title': 'Setup a New Project', 'hidden': True},
        {'href': 'general', 'title': 'Details', 'page_title': 'General Details'},
        {'href': 'description', 'title': 'Description', 'page_title': 'Description'},
        {'href': 'information', 'title': 'Information', 'page_title': 'Associated Information'},
        {'href': 'methods', 'title': 'Methods', 'page_title': 'Data Collection Methods'},
        {'href': 'datasets', 'title': 'Datasets', 'page_title': 'Datasets (Collections of Data)'},
        {'href': 'submit', 'title': 'Submit', 'page_title': 'Submit & Approval'},
        {'href': 'manage', 'title': 'Manage', 'page_title': 'Manage Project Data', 'hidden': True},
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


@view_defaults(renderer="../templates/form.pt")
class Workflows(Layouts):
    def __init__(self, request):
        self.request = request
        self.session = DBSession

        self.project_id = None
        if 'project_id' in self.request.matchdict:
            self.project_id = self.request.matchdict['project_id']

    @reify
    def workflow_menu(self):
        new_menu = WORKFLOW_STEPS[:]
        url = split(self.request.url, "?")[0]
        hidden = []
        for menu in new_menu:
            menu['current'] = url.endswith(menu['href'])
            if 'hidden' in menu and menu['hidden'] is True:
                hidden.append(menu)

        for menu in hidden:
            new_menu.remove(menu)

        return new_menu

    @reify
    def is_hidden_workflow(self):
        new_menu = WORKFLOW_STEPS[:]
        url = split(self.request.url, "?")[0]

        for menu in new_menu:
            if url.endswith(menu['href']) and 'hidden' in menu and menu['hidden'] is True:
                return True

        return False

    def find_page_title(self, href):
        for menu in WORKFLOW_STEPS:
            if menu['href'] == href:
                return menu['page_title']

        raise ValueError("There is no page title for this href: " + str(href))


    @reify
    def workflow_template(self):
        renderer = get_renderer("../templates/workflow_template.pt")
        return renderer.implementation().macros['layout']

    @reify
    def isDelete(self):
        return 'Delete' in self.request.POST

    def save_form(self, data):
         model = self.session.query(Project).filter_by(id=data['project:id']).first()

         if model is None or not isinstance(model, Project):
             if self.project_id is None:
                 data.pop('project:id')
                 model = create_sqlalchemy_model(data, model_class=Project)
                 if model is not None:
                     self.session.add(model)
             else:
                 raise ValueError("No project found for the given project id(" + self.project_id + "), please do not directly edit the address bar")

         else:
             # Update the model with all fields in the data
             if create_sqlalchemy_model(data, model_object=model) is None:
                 return # There were no changes (if there were changes they will still be commited through the internals of sqlalchemy though).
             else:
                 self.session.merge(model)

         self.session.flush()
         self.project_id = model.id
         data['project:id'] = model.id

#         self.session.remove()

    def handle_form(self, form, schema):
        # If the form is being saved (there would be 1 item in controls if it is a fresh page with a project id set)
        if len(self.request.POST) > 0:
            self.request.POST['id'] = self.project_id # Make sure the correct project is being saved (eg. user edits nav bar directly)
            controls = self.request.POST.items()

            # In either of the below cases get the data as a dict and get the rendered form
            try:
                appstruct = form.validate(controls)
                display = form.render(appstruct)
            except ValidationFailure, e:
                appstruct = e.cstruct
                display = e.render()

            print appstruct

            # save the data even if it didn't validate - this allows the user to easily navigate and fill fields out as they get the info.
            self.save_form(appstruct)
            # TODO: Walk through schema saving to look at parent schemas (throws duplicate id error)
#            If there is a target workflow step set then change to that page.
            if self.request.POST['target']:
                target = self.request.POST['target']
            else:
                target = self.request.matched_route.name
            if form.use_ajax:
                return {"page_title": self.find_page_title(self.request.matched_route.name), "form": display, "form_only": form.use_ajax,  'messages' : self.request.session.pop_flash() or ''}
            else:
                return HTTPFound(self.request.route_url(target, project_id=self.project_id))

#            return {"page_title": self.find_page_title(self.request.matched_route.name), "form": display, "form_only": form.use_ajax, 'messages' : self.request.session.pop_flash() or ''}

        # If the page has just been opened but it is set to a specific project
        appstruct = {}

        if self.project_id is not None:
            model = self.session.query(Project).filter_by(id=self.project_id).first()
            appstruct = convert_sqlalchemy_model_to_data(model, schema)

        return {"page_title": self.find_page_title(self.request.matched_route.name), "form": form.render(appstruct), "form_only": False, 'messages': self.request.session.pop_flash() or ''}


    def clone (self, source):
        """
        Clone a database model
        """
        new_object = type(source)()
        for prop in object_mapper(source).iterate_properties:
            if (isinstance(prop, ColumnProperty) or isinstance(prop, RelationProperty) and prop.secondary):
                setattr(new_object, prop.key, getattr(source, prop.key))

        return new_object



    @view_config(route_name="setup")
    def setup_view(self):
        schema = CreatePage(description="This project creation wizard helps pre-fill as many fields as possible to make the process as painless as possible!",
            validator=grant_validator)
        templates = self.session.query(ProjectTemplate).order_by(ProjectTemplate.category).all()
        categories = []
        for template in templates:
            if not template.category in categories:
                categories.append(template.category)

        schema.children[0].templates_data = templates
        schema.children[0].template_categories = categories

#        print self.get_grants("a")

        form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Save',), use_ajax=False, ajax_options=redirect_options)

        controls = self.request.POST.items()
        appstruct = {}

        # If the form is being saved (there would be 1 item in controls if it is a fresh page with a project id set)
        if len(controls) > 0:
            # In either of the below cases get the data as a dict and get the rendered form
            try:
                appstruct = form.validate(controls)

                new_project = Project()

                if 'template' in appstruct:
                    template = self.session.query(Project).filter_by(id=appstruct['template']).first()
                    if template is not None:
                        new_project = self.clone(template)
                        new_project.id = None


                new_parties = []
                if 'data_manager' in appstruct:
                    data_manager = Party()
                    data_manager.party_relationship = "manager"
                    data_manager.identifier = appstruct['data_manager']
                    new_parties.append(data_manager)

                if 'project_lead' in appstruct:
                    project_lead = Party()
                    project_lead.party_relationship = "owner"
                    project_lead.identifier = appstruct['data_manager']
                    new_parties.append(project_lead)

                if 'activity' in appstruct:
                    new_project.activity = appstruct['activity']
                    activity_results = MintLookup(None).get_from_identifier(appstruct['activity'])

                    if activity_results is not None:
                        new_project.brief_description = activity_results['dc:description']
                        new_project.project_title = activity_results['dc:title']

                        for contributor in activity_results['result-metadata']['all']['dc_contributor']:
                            if str(contributor).strip() != appstruct['data_manager'].split("/")[-1].strip():
                                new_party = Party()
                                new_party.identifier = "jcu.edu.au/parties/people/" + str(contributor).strip()
                                new_parties.append(new_party)

                        if activity_results['result-metadata']['all']['dc_date'][0]:
                            new_project.date_from = date(int(activity_results['result-metadata']['all']['dc_date'][0]), 1, 1)

                        if activity_results['result-metadata']['all']['dc_date_end'][0]:
                            new_project.date_to = date(int(activity_results['result-metadata']['all']['dc_date_end'][0]), 1, 1)

                new_project.parties = new_parties

                # TODO:  Add the current user (known because of login) as a creator for citations
                # TODO:  Add the current user (known because of login) as the creator of the project

                self.session.add(new_project)
                self.session.flush()

                self.request.session.flash('New project successfully created.')
                return HTTPFound(self.request.route_url('general', project_id=new_project.id))

            except ValidationFailure, e:
                appstruct = e.cstruct
                self.request.session.flash('Valid project setup data must be entered before progressing.')
                return {"page_title": self.find_page_title(self.request.matched_route.name), "form": e.render(), "form_only": False, 'messages': self.request.session.pop_flash() or ''}

        return {"page_title": self.find_page_title(self.request.matched_route.name), "form": form.render(appstruct), "form_only": False, 'messages': self.request.session.pop_flash() or ''}


    @view_config(route_name="general")
    def general_view(self):
        print self.request.POST
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise', ca_description=""), page='setup').bind(request=self.request)
        form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Save',), use_ajax=False, ajax_options=redirect_options)
        return self.handle_form(form, schema)


    @view_config(route_name="description")
    def description_view(self):
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise',
                ca_description="Fully describe your project to encourage other researchers to reuse your data:"\
                                       "<ul><li>The entered descriptions will be used for metadata record generation (ReDBox), provide detailed information that is relevant to the project as a whole.</li>"\
                                       "<li>Focus on what is being researched, why it is being researched and who is doing the research. The research locations and how the research is being conducted will be covered in the <i>Methods</i> and <i>Datasets</i> steps later on.</li></ul>"
        ), page="description").bind(
            request=self.request)

        form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Save',), use_ajax=False)
        return self.handle_form(form, schema)


    @view_config(route_name="information")
    def information_view(self):
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise', ca_description="<b>Please fill this section out completely</b> - it's purpose is to provide the majority of information for all generated metadata records so that you don't have to enter the same data more than once:"\
                                                                                                             "<ul><li>A metadata record (ReDBox) will be created for the entire project using the entered information directly.</li>"\
                                                                                                             "<li>A metadata record (ReDBox) will be created for each dataset using a combination of the below information and the information entered in the <i>Methods</i> and <i>Datasets</i> steps.</li>"\
                                                                                                             "<li>Once the project has been submitted and accepted the metadata records will be generated and exported, any further alterations will need to be entered for each record in ReDBox-Mint.</li>"\
                                                                                                             "<li>If specific datasets require additional metadata that cannot be entered through these forms, you can enter it directly in the ReDBox-Mint records once the project is submitted and accepted (Look under <i>[to be worked out]</i> for a link).</li>"\
                                                                                                             "</ul>"), page='metadata').bind(request=self.request)
        form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Save',), use_ajax=False)

        return self.handle_form(form, schema)

    def get_template_schemas(self):
        return self.session.query(MethodSchema).filter_by(template_schema=1).all()

    @view_config(route_name="methods")
    def methods_view(self):
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise', ca_description="Setup methods the project uses for collecting data (not individual datasets themselves as they will be setup in the next step)."), page="methods").bind(request=self.request)

        templates = self.session.query(MethodTemplate).order_by(MethodTemplate.category).all()
        categories = []
        for template in templates:
            if not template.category in categories:
                categories.append(template.category)

        schema.children[3].children[0].children[2].templates_data = templates
        schema.children[3].children[0].children[2].template_categories = categories

        # TODO: Better way of getting indexes
        schema.children[3].children[0].children[5].children[6].template_schemas = self.get_template_schemas()
#        assert False
        form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Save',), use_ajax=False)

        return self.handle_form(form, schema)

    @view_config(route_name="datasets")
    def datasets_view(self):
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise', ca_description="<p>Add individual datasets that your project will be collecting.  This is the when and where using the selected data collection method (what, why and how).</p><p><i>Such that an iButton sensor that is used to collect temperature at numerous sites would have been setup once within the Methods step and should be set-up in this step for each site it is used at.</i></p>"), page="datasets").bind(request=self.request)
        dataset_items = schema.children[3].children[0].children

#        if 'id' in self.request.GET:
#            id = int(self.request.GET['id'])
#            config = ConfigParser.SafeConfigParser()
#            config.read('../../development.ini')
#            db_engine = create_engine(config.get("app:main", "sqlalchemy.url"), echo=True)

            #scoped_session(sessionmaker(bind=db_engine))
        if self.project_id is not None:
            methods = self.session.query(Method).filter_by(project_id=self.project_id).all()
            method_schemas = []
            for method in methods:
                method_children = convert_schema(SQLAlchemyMapping(Dataset, unknown='raise')).children

                # TODO: Find programatical/more reliable way of finding the index
                DATA_CONFIG_INDEX = 11

                if method.data_source is not None:
                    for data_source in method_children[DATA_CONFIG_INDEX].children:
                        if fix_schema_field_name(data_source.name) == method.data_source:
                            method_children[DATA_CONFIG_INDEX].children = [data_source]
                            break
                else:
                    method_children[DATA_CONFIG_INDEX].children = []
                    method_children[DATA_CONFIG_INDEX].description = "No associated data source - please select a datasource on the Methods page."

                for child in method_children:
                    if fix_schema_field_name(child.name) == 'method_id':
                        child.missing = method.id
                        child.default = method.id
                        break

                method_schemas.append(colander.MappingSchema(*method_children, name=(method.method_name and method.method_name or 'Un-named')))

            method_select_schema = SelectMappingSchema(*method_schemas, title="Method", name="dataset")
        else:
            method_select_schema = SelectMappingSchema(title="Method", name="dataset")

        schema.children[3].children = [method_select_schema]

        form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Save',), use_ajax=False)

        return self.handle_form(form, schema)


    @view_config(route_name="submit")
    def submit_view(self):
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise',
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
                "<b>Disable:</b> Stop data ingestion, this would usually occur once the project has finished."), page="submit").bind(request=self.request)
        form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Save', 'Delete', 'Submit', 'Reopen', 'Approve', 'Disable'), use_ajax=False)


        if 'Approve' in self.request.POST and 'id' in self.request.POST:
            print self.request.POST
            project = self.session.query(Project).filter_by(id=self.project_id).first()

            auth = CredentialsAuthentication("casey", "password")
            ingester_api = IngesterAPIWrapper("http://localhost:8080/api", auth)

            ingester_api.post(project)
            ingester_api.close()

            print 'project approved - TODO: Success message'

        return self.handle_form(form, schema)