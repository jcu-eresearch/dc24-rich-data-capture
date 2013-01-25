import ConfigParser
import copy
from datetime import datetime, date
import json
import logging
import random
from string import split
import string
import urllib2
import sqlalchemy
from sqlalchemy.orm.properties import ColumnProperty, RelationProperty
from sqlalchemy.orm.util import object_mapper
import colander
import deform
from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.url import route_url
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import time
import transaction
from jcudc24ingesterapi.authentication import CredentialsAuthentication
from jcudc24ingesterapi.ingester_platform_api import IngesterPlatformAPI
from jcudc24provisioning.models.common_schemas import SelectMappingSchema
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPClientError
from pyramid.response import Response
from pyramid.view import view_config, view_defaults, render_view_to_response
from colanderalchemy.types import SQLAlchemyMapping
from jcudc24provisioning.views.views import Layouts
from pyramid.renderers import get_renderer
from jcudc24provisioning.models.project import DBSession, PullDataSource, ProjectTemplate,method_template, Project, CreatePage, Method, Base, Party, Dataset, MethodSchema, grant_validator, MethodTemplate
from jcudc24provisioning.views.ca_scripts import convert_schema, create_sqlalchemy_model, convert_sqlalchemy_model_to_data,fix_schema_field_name
from jcudc24provisioning.scripts.ingesterapi_wrapper import IngesterAPIWrapper
from jcudc24provisioning.views.mint_lookup import MintLookup


__author__ = 'Casey Bajema'

logger = logging.getLogger(__name__)

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
    def __init__(self, context, request):
        self.request = request
        self.context = context
        self.session = DBSession

        self.project_id = None
        if self.request.matchdict and 'project_id' in self.request.matchdict:
            self.project_id = self.request.matchdict['project_id']

    @reify
    def workflow_step(self):
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

    def find_workflow_title(self, href):
        for menu in WORKFLOW_STEPS:
            if menu['href'] == href:
                return menu['page_title']

        raise ValueError("There is no page title for this address: " + str(href))


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

         try:
             self.session.flush()
             self.project_id = model.id
             data['project:id'] = model.id
#             self.request.session.flash("Project saved successfully.", "success")
         except Exception as e:
             logger.exception("SQLAlchemy exception while flushing after save: %s" % e)
             self.request.session.flash("There was an error while saving the project, please try again.", "error")
             self.request.session.flash("Error: %s" % e, "error")
             self.session.rollback()

#         self.session.remove()

    def handle_form(self, form, schema, page_help=None, appstruct=None, display=None):
        # If the form is being saved (there would be 1 item in controls if it is a fresh page with a project id set)
        if len(self.request.POST) > 0:
            self.request.POST['id'] = self.project_id # Make sure the correct project is being saved (eg. user edits nav bar directly)
            controls = self.request.POST.items()

            # In either of the below cases get the data as a dict and get the rendered form
            if appstruct is None or display is None:
                try:
                    appstruct = form.validate(controls)
                    display = form.render(appstruct)
                except ValidationFailure, e:
                    appstruct = e.cstruct
                    display = e.render()

            # save the data even if it didn't validate - this allows the user to easily navigate and fill fields out as they get the info.
            self.save_form(appstruct)
            # TODO: Walk through schema saving to look at parent schemas (throws duplicate id error)
#            If there is a target workflow step set then change to that page.
            if self.request.POST['target']:
                target = self.request.POST['target']
            else:
                target = self.request.matched_route.name
            if form.use_ajax:
                messages = {
                    'error_messages': self.request.session.pop_flash("error"),
                    'success_messages': self.request.session.pop_flash("success"),
                    'warning_messages': self.request.session.pop_flash("warning")
                }
                return {"page_title": self.find_workflow_title(self.request.matched_route.name), "form": display, "form_only": form.use_ajax,  'messages' : messages or '', 'page_help': page_help}
            else:
                return HTTPFound(self.request.route_url(target, project_id=self.project_id))

#            return {"page_title": self.find_workflow_title(self.request.matched_route.name), "form": display, "form_only": form.use_ajax, 'messages' : self.request.session.pop_flash() or ''}

        # If the page has just been opened but it is set to a specific project
        appstruct = {}

        if self.project_id is not None:
            model = self.session.query(Project).filter_by(id=self.project_id).first()
            appstruct = convert_sqlalchemy_model_to_data(model, schema)

        messages = {
            'error_messages': self.request.session.pop_flash("error"),
            'success_messages': self.request.session.pop_flash("success"),
            'warning_messages': self.request.session.pop_flash("warning")
        }
        print "Messages: " + str(messages)
        return {"page_title": self.find_workflow_title(self.request.matched_route.name), "form": form.render(appstruct), "form_only": False, 'messages': messages, 'page_help': page_help}


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
        page_help = "This project creation wizard helps pre-fill as many fields as possible to make the process as painless as possible!"

        schema = CreatePage(validator=grant_validator)
        templates = self.session.query(ProjectTemplate).order_by(ProjectTemplate.category).all()
        categories = []
        for template in templates:
            if not template.category in categories:
                categories.append(template.category)

        schema.children[0].templates_data = templates
        schema.children[0].template_categories = categories

#        print self.get_grants("a")

        form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id),
            buttons=('Create Project',), use_ajax=False, ajax_options=redirect_options)

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


                try:
                    self.session.add(new_project)
                    self.session.flush()
                    self.request.session.flash('New project successfully created.', 'success')
                except Exception as e:
                    logger.exception("SQLAlchemy exception while flushing after project creation: %s" % e)
                    self.request.session.flash("There was an error while creating the project, please try again.", "error")
                    self.request.session.flash("Error: %s" % e, "error")
                    self.session.rollback()

                return HTTPFound(self.request.route_url('general', project_id=new_project.id))

            except ValidationFailure, e:
                appstruct = e.cstruct
                self.request.session.flash('Valid project setup data must be entered before progressing.', 'error')
                messages = {
                    'error_messages': self.request.session.pop_flash("error"),
                    'success_messages': self.request.session.pop_flash("success"),
                    'warning_messages': self.request.session.pop_flash("warning")
                }
                return {"page_title": self.find_workflow_title(self.request.matched_route.name), "form": e.render(), "form_only": False, 'messages': messages}

        messages = {
            'error_messages': self.request.session.pop_flash("error"),
            'success_messages': self.request.session.pop_flash("success"),
            'warning_messages': self.request.session.pop_flash("warning")
        }
        return {"page_title": self.find_workflow_title(self.request.matched_route.name), "form": form.render(appstruct), "form_only": False, 'messages': messages, 'page_help': page_help}


    @view_config(route_name="general")
    def general_view(self):
        page_help = ""
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise', ca_description=""), page='setup').bind(request=self.request)
        form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Save',), use_ajax=False, ajax_options=redirect_options)
        return self.handle_form(form, schema, page_help)


    @view_config(route_name="description")
    def description_view(self):
        page_help = "Fully describe your project to encourage other researchers to reuse your data:"\
                    "<ul><li>The entered descriptions will be used for metadata record generation (ReDBox), " \
                    "provide detailed information that is relevant to the project as a whole.</li>"\
                    "<li>Focus on what is being researched, why it is being researched and who is doing the research. " \
                    "The research locations and how the research is being conducted will be covered in the <i>Methods</i>" \
                    " and <i>Datasets</i> steps later on.</li></ul>";
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise'), page="description").bind(
            request=self.request)

        form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Save',), use_ajax=False)
        return self.handle_form(form, schema, page_help)


    @view_config(route_name="information")
    def information_view(self):
        page_help ="<b>Please fill this section out completely</b> - it's purpose is to provide the majority of information " \
                   "for all generated metadata records so that you don't have to enter the same data more than once:"\
                                   "<ul><li>A metadata record (ReDBox) will be created for the entire project using the" \
                                   " entered information directly.</li>" \
                                   "<li>A metadata record (ReDBox) will be created for each dataset using a combination " \
                                   "of the below information and the information entered in the <i>Methods</i> and " \
                                   "<i>Datasets</i> steps.</li>"\
                                   "<li>Once the project has been submitted and accepted the metadata records will be " \
                                   "generated and exported, any further alterations will need to be entered for each " \
                                   "record in ReDBox-Mint.</li>"\
                                   "<li>If specific datasets require additional metadata that cannot be entered through " \
                                   "these forms, you can enter it directly in the ReDBox-Mint records once the project " \
                                   "is submitted and accepted (Look under <i>[to be worked out]</i> for a link).</li></ul>"
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise'), page='metadata').bind(request=self.request)
        form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Save',), use_ajax=False)

        return self.handle_form(form, schema, page_help)

    def get_template_schemas(self):
        return self.session.query(MethodSchema).filter_by(template_schema=1).all()

    @view_config(route_name="methods")
    def methods_view(self):
        page_help = "<p>Setup methods the project uses for collecting data (not individual datasets themselves as they will " \
                    "be setup in the next step).</p>" \
                    "<br /><p>This page sets up:</p>" \
                    "<ul><li>Ways of collecting data - data sources</li>" \
                    "<li>What the data actually is - its 'data schema' - what fields there are, field types and associated information.</li>" \
                    "<li>Any additional information about this data collection methods - websites or attachments</li></ul>"
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise'), page="methods").bind(request=self.request)

        templates = self.session.query(MethodTemplate).order_by(MethodTemplate.category).all()
        categories = []
        for template in templates:
            if not template.category in categories:
                categories.append(template.category)

        for i in range(len(schema.children)):
            if schema.children[i].name[-len(Project.methods.key):] == Project.methods.key:
                METHODS_INDEX = i

                for j in range(len(schema.children[i].children[0].children)):
                    if schema.children[i].children[0].children[j].name[-len(Method.method_template.key):] == Method.method_template.key:
                        METHOD_TEMPLATE_INDEX = j
                        break
                break

        schema.children[METHODS_INDEX].children[0].children[METHOD_TEMPLATE_INDEX].templates_data = templates
        schema.children[METHODS_INDEX].children[0].children[METHOD_TEMPLATE_INDEX].template_categories = categories
        schema.children[METHODS_INDEX].children[0].children[METHOD_TEMPLATE_INDEX].widget=deform.widget.HiddenWidget()

        template_data = method_template#type("dummy_object", (object,), {})
        template_data.oid = "MethodsTemplate"
        template_data.schema = type("dummy_object", (object,), {})
        template_data.schema.templates_data = templates
        template_data.schema.template_categories = categories

        schema.children[METHODS_INDEX].templates_data = template_data

        for i in range(len(schema.children[METHODS_INDEX].children[0].children)):
            if schema.children[METHODS_INDEX].children[0].children[i].name[-len(Method.data_type.key):] == Method.data_type.key:
                DATA_SCHEMA_INDEX = i
                for j in range(len(schema.children[METHODS_INDEX].children[0].children[i].children)):
                    if schema.children[METHODS_INDEX].children[0].children[i].children[j].name[-len(MethodSchema.parents.key):] == MethodSchema.parents.key:
                        METHOD_SCHEMA_PARENTS_INDEX = j
                        break
                break
        schema.children[METHODS_INDEX].children[0].children[DATA_SCHEMA_INDEX].children[METHOD_SCHEMA_PARENTS_INDEX].template_schemas = self.get_template_schemas()
#        assert False

        form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Save',), use_ajax=False)

        appstruct = None
        display = None
        controls = self.request.POST.items()
        if len(controls) > 0:
            try:
                appstruct = form.validate(controls)
                display = form.render(appstruct)
            except ValidationFailure, e:
                appstruct = e.cstruct
                display = e.render()

            print "Post variables: " + str(appstruct)

            old_models = self.session.query(Method).filter_by(project_id=self.project_id).all()
            for new_method_data in appstruct['project:methods']:
                if not new_method_data['method:id'] and 'method:method_template' in new_method_data and new_method_data['method:method_template']:
                    print "NEW:" + str(new_method_data)
                    template_method = self.session.query(Method).filter_by(id=new_method_data['method:method_template']).first()
                    if template is None: break

                    new_method_dict = convert_sqlalchemy_model_to_data(self.clone(template_method), schema.children[METHODS_INDEX])
                    new_method_dict = new_method_dict['method']
                    del new_method_dict['method:id']
                    new_method_dict['method:project_id'] = new_method_data['method:project_id']
                    new_method_dict['method:method_template'] = new_method_data['method:method_template']
                    new_method_data.update(new_method_dict)

        return self.handle_form(form, schema, page_help, appstruct=appstruct, display=display)

    @view_config(route_name="datasets")
    def datasets_view(self):
        def get_all_fields(data_entry_schema):
            fields = []

            for field in data_entry_schema.parents:
                fields.extend(get_all_fields(data_entry_schema))

            for field in data_entry_schema.custom_fields:
                fields.append(field)

            return fields

        page_help = "<p>Add individual datasets that your project will be collecting.  This is the when and where using " \
                    "the selected data collection method (what, why and how).</p><p><i>Such that an iButton sensor that " \
                    "is used to collect temperature at numerous sites would have been setup once within the Methods step" \
                    " and should be set-up in this step for each site it is used at.</i></p>"
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise'), page="datasets").bind(request=self.request)

        for i in range(len(schema.children)):
            if schema.children[i].name[-len(Project.datasets.key):] == Project.datasets.key:
                DATASETS_INDEX = i
                break

        dataset_items = schema.children[DATASETS_INDEX].children[0].children

#        if 'id' in self.request.GET:
#            id = int(self.request.GET['id'])
#            config = ConfigParser.SafeConfigParser()
#            config.read('../../development.ini')
#            db_engine = create_engine(config.get("app:main", "sqlalchemy.url"), echo=True)

            #scoped_session(sessionmaker(bind=db_engine))
        if self.project_id is not None:
            methods = self.session.query(Method).filter_by(project_id=self.project_id).all()

            if len(methods) <= 0:
                self.request.session.flash('You must configure at least one method before adding dataset\'s', 'warning')
                return HTTPFound(self.request.route_url('methods', project_id=self.project_id))

            method_schemas = []
            for method in methods:
                dataset_children = convert_schema(SQLAlchemyMapping(Dataset, unknown='raise')).children

                DATA_SOURCE_CONFIGURATION_GROUP_NAME = "data_source_configuration"
                print dataset_children
                for i in range(len(dataset_children)):
                    if dataset_children[i].name[-len(DATA_SOURCE_CONFIGURATION_GROUP_NAME):] == DATA_SOURCE_CONFIGURATION_GROUP_NAME:
                        DATA_CONFIG_INDEX = i
                        break

                if method.data_source is not None and 'DATA_CONFIG_INDEX' in locals():
                    for data_source in dataset_children[DATA_CONFIG_INDEX].children:
                        if fix_schema_field_name(data_source.name) == method.data_source:
                            # Add dynamic data to pull data sources
                            if fix_schema_field_name(data_source.name) == PullDataSource.__tablename__:
                                for child in data_source.children:
                                    if fix_schema_field_name(child.name) == PullDataSource.file_field.key:
                                        fields = get_all_fields(method.data_type)
                                        field_values = []
                                        for i in range(len(fields)):
                                            if fields[i].type == "file":
                                                field_values.append((fields[i].id, fields[i].name))

                                        child.widget.values = tuple(field_values)

                            # Set the data source
                            dataset_children[DATA_CONFIG_INDEX].children = [data_source]
                            break
                elif 'DATA_CONFIG_INDEX' in locals():
                    dataset_children[DATA_CONFIG_INDEX].children = []
                    dataset_children[DATA_CONFIG_INDEX].description = "No associated data source - please select a datasource on the Methods page."

                # Get the dataset template if there is one
                if method.method_template:
                    template = self.session.query(Dataset).join(MethodTemplate).filter(Dataset.id == MethodTemplate.dataset_id).\
                    filter(MethodTemplate.id == method.method_template).first()

                for child in dataset_children:
#                    if fix_schema_field_name(child.name) == 'method_id':
##                        child.missing = method.id
#                        child.default = method.id
#                    else:
                        # If there is a template for datasets of this method, set all fields default values accordingly
                        if template:
                            name = fix_schema_field_name(child.name)
                            if name != "id" and hasattr(template, name):
                                child.default = getattr(template, name, colander.null)
                            elif name != "id":
                                logger.warn("Schema has field template doesn't: %s" % name)


                method_schemas.append(colander.MappingSchema(*dataset_children, name=(method.method_name and method.method_name or 'Un-named')))

            method_select_schema = SelectMappingSchema(*method_schemas, name="dataset", collapsed=False,
                select_title="Select dataset method type", select_description="<i>Changing will overwrite all fields.</i>")
        else:
            method_select_schema = SelectMappingSchema(select_title="Method", name="dataset" ,collapsed=False)


        schema.children[DATASETS_INDEX].children = [method_select_schema]

        form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Save',), use_ajax=False)

        return self.handle_form(form, schema, page_help)


    @view_config(route_name="submit")
    def submit_view(self):
        page_help="TODO: The submission and approval should both follow a process of:" \
                    "<ol><li>Automated validation</li>" \
                    "<li>User fixes validation errors</li>"  \
                    "<li>Reminders/action items for users to complete that can't be auto-validated</li>"  \
                    "<li>Final confirmation and approval</li>"  \
                    "<li>Recommendations and next steps</li></ol><br />" \
                    "<b>Save:</b> Save the project as is, it doesn't need to be fully complete or valid.<br/><br/>"\
                    "<b>Delete:</b> Delete the project, this can only be performed by administrators or before the project has been submitted.<br/><br/>"\
                    "<b>Submit:</b> Submit this project for admin approval. If there are no problems the project data will be used to create ReDBox-Mint records as well as configuring data ingestion into persistent storage<br/><br/>"\
                    "<b>Reopen:</b> Reopen the project for editing, this can only occur when the project has been submitted but not yet accepted (eg. the project may require updates before being approved)<br/><br/>"\
                    "<b>Approve:</b> Approve this project, generate metadata records and setup data ingestion<br/><br/>"\
                    "<b>Disable:</b> Stop data ingestion, this would usually occur once the project has finished."
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise',), page="submit").bind(request=self.request)
        form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Save', 'Delete', 'Submit', 'Reopen', 'Approve', 'Disable'), use_ajax=False)

#        if 'Approve' in self.request.POST:

        response = self.handle_form(form, schema, page_help)

        if 'Approve' in self.request.POST and 'id' in self.request.POST:
            project = self.session.query(Project).filter_by(id=self.project_id).first()

            auth = CredentialsAuthentication("casey", "password")
            ingester_api = IngesterAPIWrapper("http://localhost:8080/api", auth)

            try:
                ingester_api.post(project)
                ingester_api.close()
                logger.info("Project has been added to ingesterplatform successfully: %s", project.id)
            except Exception as e:
                logger.exception("Project failed to add to ingesterplatform: %s", project.id)
                self.request.session.flash("<p>Sorry, the project failed to configure the data storage, please try agiain.", 'error')
                self.request.session.flash("Error: %s" % e, 'error')
                return response

            try:
                # TODO: ReDBox integration
                logger.info("Project has been added to ReDBox successfully: %s", project.id)
                raise NotImplementedError("ReDBox integration hasn't been implemented yet.")
                pass
            except Exception as e:
                logger.exception("Project failed to add to ReDBox: %s", project.id)
                self.request.session.flash("Sorry, the project failed to generate or add metadata records to ReDBox, please try agiain.", 'error')
                self.request.session.flash("Error: %s" % e, 'error')
                return response

            logger.info("Project has been approved successfully: %s", project.id)

        return response

    @view_config(context=Exception, route_name="workflow_exception")
    def exception_view(self):
        # TODO: Update standard exception screen to fit.
        logger.exception("An exception occurred in global exception view: %s", self.context)
        if hasattr(self, self.request.matched_route.name + "_view"):
            try:
                self.request.session.flash('Sorry, please try again - there was an exception: ' + str(self.context), 'error')
                self.request.POST.clear()
                response = getattr(self, str(self.request.matched_route.name) + "_view")()
                return response
            except Exception:
                logger.exception("Exception occurred while trying to display the view without variables: %s", Exception)
                return {"page_title": self.find_workflow_title(self.request.matched_route.name), "form": 'Sorry, we are currently experiencing difficulties.  Please contact the administrators: ' + str(self.context), "form_only": False}
        else:
            try:
                return {"page_title": self.find_workflow_title(self.request.matched_route.name), "form": 'This address is not valid, please don\'t directly edit the address bar: ' + str(self.context), "form_only": False}
            except:
                self.request.session.flash('There is no page at the requested address, please don\'t edit the address bar directly.', 'error')
                if self.request.matchdict and self.request.matchdict['route'] and (self.request.matchdict['route'].split("/")[0]).isnumeric():
                    project_id = int(self.request.matchdict['route'].split("/")[0])
                    print 'isnumeric: ' + str(project_id)
                    return HTTPFound(self.request.route_url('general', project_id=project_id))
                else:
                    return HTTPFound(self.request.route_url('setup'))


#            return {"page_title": self.context, "form": 'This address is not valid, please don\'t directly edit the address bar: ' + str(self.context), "form_only": False}

    #    @view_config(context=sqlalchemy.orm.exc.SQLAlchemyError, renderer="../templates/exception.pt")
    @view_config(context=sqlalchemy.exc.SQLAlchemyError, renderer="../templates/exception.pt")
    def sqlalchemy_exception_view(self):
        self.session.rollback()
        logger.exception("A database exception occurred in global exception view: %s", self.context)
        return {"exception": "%s" % self.context, "message": 'Sorry, we are currently experiencing difficulties.  Please contact the administrators: ' + str(self.context)}




#    @view_config(renderer="../templates/search_template.pt", route_name="add_method_from_template")
#    def add_method_from_template(self):
#        assert 'method_id' in self.request.matchdict, "Error: Trying to add method with invalid template id."
#        assert 'project_id' in self.request.matchdict, "Error: Trying to add method with invalid project id."
#        method_id = self.request.matchdict['method_id']
#        project_id = self.request.matchdict['project_id']
#
#        project = self.session.query(Project).filter_by(id=project_id).first()
#        model = self.session.query(Method).filter_by(id=method_id).first()
#
#        if project and model:
#            # Use the scripts to create the new models
#            data = convert_sqlalchemy_model_to_data(model, convert_schema(SQLAlchemyMapping(Method, unknown='raise')))
#            new_model = create_sqlalchemy_model(data, model_class=Method)
#            del new_model.id
#            #            new_model = Method()
#            self.session.add(new_model)
#            new_model.method_template = model.id
#            new_model.project_id = project.id
#            new_model.method_description="alsdjkh"
#            project.methods.append(new_model)
#            self.session.flush()
#            #            print new_model
#            #            print new_model.__dict__
#            #            self.session.flush()
#            #
#            #            self.session = DBSession
#            #
#            #            print "Method ID's: " + str(model.id) + " : " + str(new_model.id)
#            #
#            #            print new_model.id
#            #            id = new_model.id
#            #            transaction.commit()
#            #
#            #            self.session = APISession
#            #            test_model = self.session.query(Method).filter_by(id=id).all()
#            #            for test in test_model:
#            #                print "Test model: " + str(model.__dict__)
#            return {'values': json.dumps('Method successfully added')}
#        else:
#            print "Add method failed: " + str(project) + str(model)
#            return {'values': json.dumps('Failed to add method')}
