import ConfigParser
import cgi
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
from sqlalchemy.orm import scoped_session, sessionmaker, RelationshipProperty
import time
import transaction
from jcudc24ingesterapi.authentication import CredentialsAuthentication
from jcudc24ingesterapi.ingester_platform_api import IngesterPlatformAPI
from jcudc24provisioning.models.common_schemas import SelectMappingSchema
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPClientError
from pyramid.response import Response, FileResponse
from pyramid.view import view_config, view_defaults, render_view_to_response
from colanderalchemy.types import SQLAlchemyMapping
from jcudc24provisioning.views.views import Layouts
from pyramid.renderers import get_renderer
from jcudc24provisioning.models.project import DBSession, PullDataSource, Metadata, UntouchedPages, IngesterLogs, Location, \
    ProjectTemplate,method_template,DatasetDataSource, Project, project_validator, ProjectStates, CreatePage, Method, Base, Party, Dataset, MethodSchema, grant_validator, MethodTemplate
from jcudc24provisioning.views.ca_scripts import convert_schema, fix_schema_field_name
from jcudc24provisioning.models.ingesterapi_wrapper import IngesterAPIWrapper
from jcudc24provisioning.views.mint_lookup import MintLookup


__author__ = 'Casey Bajema'

logger = logging.getLogger(__name__)

# Workflow page href needs to be synchronised with UntouchedPages table in project.py
WORKFLOW_STEPS = [
        {'href': 'create', 'title': 'Create', 'page_title': 'Create a New Project', 'hidden': True},
        {'href': 'general', 'title': 'Details', 'page_title': 'General Details'},
        {'href': 'description', 'title': 'Description', 'page_title': 'Description'},
        {'href': 'information', 'title': 'Information', 'page_title': 'Associated Information'},
        {'href': 'methods', 'title': 'Methods', 'page_title': 'Data Collection Methods'},
        {'href': 'datasets', 'title': 'Datasets', 'page_title': 'Datasets (Collections of Data)'},
        {'href': 'view_record', 'title': 'Generated Dataset Record', 'page_title': 'Generated Dataset Record', 'hidden': True},
        {'href': 'edit_record', 'title': 'Generated Dataset Record', 'page_title': 'Generated Dataset Record', 'hidden': True},
        {'href': 'delete_record', 'title': 'Generated Dataset Record', 'page_title': 'Generated Dataset Record', 'hidden': True},
        {'href': 'submit', 'title': 'Submit', 'page_title': 'Submit & Approval'},
        {'href': 'template', 'title': 'Template', 'page_title': 'Template Details', 'hidden': True},
]

WORKFLOW_ACTIONS = [
        {'href': 'general', 'title': 'Configuration', 'page_title': 'General Details'},
        {'href': 'logs', 'title': 'View Logs', 'page_title': 'Ingester Event Logs', 'hidden_states': [ProjectStates.OPEN, ProjectStates.SUBMITTED]},
        {'href': 'add_data', 'title': 'Add Data', 'page_title': 'Add Data', 'hidden_states': [ProjectStates.OPEN, ProjectStates.SUBMITTED]},
        {'href': 'manage_data', 'title': 'Manage Data', 'page_title': 'Manage Data', 'hidden_states': [ProjectStates.OPEN, ProjectStates.SUBMITTED]},
        {'href': 'permissions', 'title': 'Sharing', 'page_title': 'Sharing & Permissions'},
        {'href': 'duplicate', 'title': 'Duplicate Project', 'page_title': 'Duplicate Project'},
        {'href': 'create_template', 'title': 'Make into Template', 'page_title': 'Create Project Template'},
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

class ProjectStates(object):
    OPEN = 0
    SUBMITTED = 1
    ACTIVE = 2
    DISABLED = 3

@view_defaults(renderer="../templates/form.pt")
class Workflows(Layouts):
    def __init__(self, context, request):
        self.request = request
        self.context = context
        self.session = DBSession
        self.config = request.registry.settings

        self.project_id = None
        if self.request.matchdict and 'project_id' in self.request.matchdict:
            self.project_id = self.request.matchdict['project_id']

        # If the user submits a form
        if 'project:id' in self.request.POST and self.request.POST['project:id'] != self.project_id:
            self.request.POST['project:id'] = self.project_id

    @property
    def readonly(self):
        if '_readonly' not in locals():
            # TODO: Update this to take permissions into account for submitted state
            self._readonly = self.project is not None and not (self.project.state == ProjectStates.OPEN or self.project.state is None or self.project.state == ProjectStates.SUBMITTED)
        return self._readonly

    @property
    def title(self):
        if '_title' not in locals():
            self._title = self.find_menu()['title']
        return self._title

    @property
    def project(self):
        if '_project' not in locals():
            self._project = self.session.query(Project).filter_by(id=self.project_id).first()
        return self._project

    def find_errors(self, error, page=None):
        errors = []

        page = getattr(error.node, 'page', page)
        if error.msg is not None:
            errors.append((page, error.node.title, error.msg))
#        if error.message is not None and len(error.message) > 0:
#            test=1

        for child in error.children:
            errors.extend(self.find_errors(child, page))

        return errors


    @property
    def auth(self):
        if '_auth' not in locals():
            self._auth = CredentialsAuthentication(self.config["ingesterapi.username"], self.config["ingesterapi.password"])
            auth = self._auth
        return self._auth

    @property
    def ingester_api(self):
        if '_ingester_api' not in locals():
            self._ingester_api = IngesterAPIWrapper(self.config["ingesterapi.url"], self.auth)
            api = self._ingester_api
        return self._ingester_api


    @property
    def page(self):
        if '_page' not in locals():
            for menu in WORKFLOW_STEPS + WORKFLOW_ACTIONS:
                if self.request.url.endswith(menu['href']):
                    self._page = menu
        return self._page

    @property
    def next(self):
        if '_next' not in locals():
            self._next = None # Set as None if this is the last visible step or it isn't a workflow page.

            if self.page in WORKFLOW_STEPS:
                for i in range(len(WORKFLOW_STEPS))[WORKFLOW_STEPS.index(self.page) + 1:]:
                    if 'hidden' not in self._next or not self._next['hidden']:
                        self._next = WORKFLOW_STEPS[i]
                        break

        return self._next

    @property
    def previous(self):
        if '_previous' not in locals():
            self._previous = None # Set as None if this is the first visible step or it isn't a workflow page.

            if self.page in WORKFLOW_STEPS:
                for i in range(len(WORKFLOW_STEPS))[WORKFLOW_STEPS.index(self.page) - 1:].reverse():
                    if 'hidden' not in self._previous or not self._previous['hidden']:
                        self._previous = WORKFLOW_STEPS[i]
                        break

        return self._previous

    @property
    def appstruct(self):
        if '_appstruct' not in locals():
            controls = self.request.POST.items()

            if 'POST' != self.request.method or len(self.request.POST) == 0:
                self._appstruct = {}
            else:
                try:
                    self._appstruct = self.form.validate(controls)
                except ValidationFailure, e:
                    self._appstruct = e.cstruct
        return self._appstruct

# --------------------MENU TEMPLATE METHODS-------------------------------------------
    @reify
    def workflow_step(self):
        if self.page not in WORKFLOW_STEPS:
            return []

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
    def workflow_action(self):
        new_menu = WORKFLOW_ACTIONS[:]
        url = split(self.request.url, "?")[0]
        hidden = []
        for menu in new_menu:
            menu['current'] = url.endswith(menu['href']) or self.page in WORKFLOW_STEPS and menu['href'] == 'general'
            if ('hidden' in menu and menu['hidden'] is True) or ('hidden_states' in menu and self.project is not None and self.project.state in menu['hidden_states']):
                hidden.append(menu)

        for menu in hidden:
            new_menu.remove(menu)

        return new_menu

    @reify
    def is_hidden_workflow(self):
        url = split(self.request.url, "?")[0]

        for menu in WORKFLOW_STEPS + WORKFLOW_ACTIONS:
            if url.endswith(menu['href']) and 'hidden' in menu and menu['hidden'] is True:
                return True

        return False

    def find_menu(self, href=None):
        if href is None:
            href = self.request.matched_route.name

        for menu in WORKFLOW_STEPS + WORKFLOW_ACTIONS:
            if menu['href'] == href:
                return menu#['page_title']

        raise ValueError("There is no page for this address: " + str(href))



    @reify
    def workflow_template(self):
        renderer = get_renderer("../templates/workflow_template.pt")
        return renderer.implementation().macros['layout']

    @reify
    def isDelete(self):
        return 'Delete' in self.request.POST

    def get_address(self, href):
        return self.request.route_url(href, project_id=self.project_id)

# --------------------WORKFLOW STEP METHODS-------------------------------------------
    def _save_form(self, appstruct, model_id, model_type):
         # In either of the below cases get the data as a dict and get the rendered form
#        if 'POST' != self.request.method or len(self.request.POST) == 0 or self.readonly or \
#                'model_id' not in self.request.POST or 'model_type' not in self.request.POST:
#            return

#        model_id = self.request.POST['model_id']
#        model_type = globals()[self.request.POST['model_type']]

        model = self.session.query(model_type).filter_by(id=model_id).first()

        if model is None or not isinstance(model, model_type):
            if model_id is None or model_id == colander.null:
                model = model_type(appstruct=appstruct)
                if model is not None:
                    self.session.add(model)
                else:
                    return
            else:
                raise ValueError("No project found for the given project id(" + model_id + "), please do not directly edit the address bar.")

        else:
            # Update the model with all fields in the data
            if model.update(appstruct):
                self.session.merge(model)

        try:
            self.session.flush()
            return model.id
#            self.request.session.flash("Project saved successfully.", "success")
        except Exception as e:
            logger.exception("SQLAlchemy exception while flushing after save: %s" % e)
            self.request.session.flash("There was an error while saving the project, please try again.", "error")
            self.request.session.flash("Error: %s" % e, "error")
            self.session.rollback()
#       self.session.remove()

    def _get_messages(self):
        return {'error_messages': self.request.session.pop_flash("error"),
                'success_messages': self.request.session.pop_flash("success"),
                'warning_messages': self.request.session.pop_flash("warning")
            }

    def _redirect_to_target(self):
#       If there is a target workflow step set then change to that page.
        if self.request.POST['target']:
            target = self.request.POST['target']
        else:
            target = self.request.matched_route.name
#        if form.use_ajax:
#            return {"page_title": self.title, "form": display, "form_only": form.use_ajax,  'messages' : self._get_messages() or '', 'page_help': page_help, 'readonly': readonly}
#        else:
        return HTTPFound(self.request.route_url(target, project_id=self.project_id))


    def handle_form(self, form, schema, page_help=None, appstruct=None, display=None, readonly=False):
        # If the form is being saved (there would be 1 item in controls if it is a fresh page with a project id set)
        if len(self.request.POST) > 1 and not readonly:
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
            project_id = self._save_form(appstruct, self.project_id, Project)


            # Set the page as edited so future visits will show the page with validation
            if project_id is not None:
                self.project_id = project_id
                untouched_pages = self.session.query(UntouchedPages).filter_by(project_id=self.project_id).first()
                if untouched_pages is None:
                    untouched_pages = UntouchedPages()
                    untouched_pages.project_id = self.project_id
                    self.session.add(untouched_pages)

                # If this causes exceptions the UntouchedPages->column names (in project.py) need to by the same as href values in WORKFLOW_STEPS above.
                page = self.find_menu()['href']
                setattr(untouched_pages, page, True)

            return self._redirect_to_target()
#            return {"page_title": self.find_menu()['title'], "form": display, "form_only": form.use_ajax, 'messages' : self.request.session.pop_flash() or ''}

        # If the page has just been opened but it is set to a specific project
        appstruct = {}

        if self.project_id is not None:
            model = self.session.query(Project).filter_by(id=self.project_id).first()
            if model is not None:
                appstruct = model.dictify(schema)

        # If the page has been saved previously, show the validated form
        untouched_pages = self.session.query(UntouchedPages).filter_by(project_id=self.project_id).first()
        page = self.find_menu()['href']
        if untouched_pages is not None and hasattr(untouched_pages, page) and getattr(untouched_pages, page) == True:
            try:
                appstruct = form.validate_pstruct(appstruct)
                display = form.render(appstruct, readonly=readonly)
            except ValidationFailure, e:
                appstruct = e.cstruct
                display = e.render()

        else:
            display = form.render(appstruct, readonly=readonly)

        return {"page_title": self.find_menu()['title'], "form": display, "form_only": False, 'messages': self._get_messages(), 'page_help': page_help, 'readonly': readonly}


    def clone (self, source):
        """
        Clone a database model
        """
        if source is None:
            return None

        new_object = type(source)()
        for prop in object_mapper(source).iterate_properties:
            if (isinstance(prop, ColumnProperty) or isinstance(prop, RelationshipProperty) and prop.secondary is not None) and not prop.key == "id":
                setattr(new_object, prop.key, getattr(source, prop.key))
            elif isinstance(prop, RelationshipProperty):
                if isinstance(getattr(source, prop.key), list):
                    items = []
                    for item in getattr(source, prop.key):
                        items.append(self.clone(item))
                    setattr(new_object, prop.key, items)
                else:
                    setattr(new_object, prop.key, self.clone(getattr(source, prop.key)))


        return new_object



# --------------------WORKFLOW STEP VIEWS-------------------------------------------
    @view_config(route_name="create")
    def create_view(self):
        page_help = "This project creation wizard helps pre-fill as many fields as possible to make the process as painless as possible!"

        schema = CreatePage(validator=grant_validator)
        templates = self.session.query(ProjectTemplate).order_by(ProjectTemplate.category).all()
        categories = []
        for template in templates:
            if not template.category in categories:
                categories.append(template.category)

        schema.children[0].templates_data = templates
        schema.children[0].template_categories = categories

        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id),
            buttons=('Create Project',), use_ajax=False, ajax_options=redirect_options)

        controls = self.request.POST.items()
        appstruct = {}

        # If the form is being saved (there would be 1 item in controls if it is a fresh page with a project id set)
        if len(controls) > 0:
            # In either of the below cases get the data as a dict and get the rendered form
            try:
                appstruct = self.form.validate(controls)

                new_project = Project()

                if 'template' in appstruct:
                    template = self.session.query(Project).filter_by(id=appstruct['template']).first()
                    if template is not None:
                        new_project = self.clone(template)
                        new_project.id = None
                        new_project.template = False
                        new_project.state = ProjectStates.OPEN

                if not new_project.information:
                    new_info = Metadata()
                    new_project.information = new_info

                new_parties = []
                if 'data_manager' in appstruct:
                    data_manager = Party()
                    data_manager.party_relationship = "manager"
                    data_manager.identifier = appstruct['data_manager']
                    new_parties.append(data_manager)

                if 'project_lead' in appstruct:
                    project_lead = Party()
                    project_lead.party_relationship = "owner"
                    project_lead.identifier = appstruct['project_lead']
                    new_parties.append(project_lead)

                if 'activity' in appstruct:
                    new_project.information.activity = appstruct['activity']
                    activity_results = MintLookup(None).get_from_identifier(appstruct['activity'])

                    if activity_results is not None:
                        new_project.information.brief_description = activity_results['dc:description']
                        new_project.information.project_title = activity_results['dc:title']

                        for contributor in activity_results['result-metadata']['all']['dc_contributor']:
                            if str(contributor).strip() != appstruct['data_manager'].split("/")[-1].strip():
                                new_party = Party()
                                new_party.identifier = "jcu.edu.au/parties/people/" + str(contributor).strip()
                                new_parties.append(new_party)

                        if activity_results['result-metadata']['all']['dc_date'][0]:
                            new_project.information.date_from = date(int(activity_results['result-metadata']['all']['dc_date'][0]), 1, 1)

                        if activity_results['result-metadata']['all']['dc_date_end'][0]:
                            new_project.information.date_to = date(int(activity_results['result-metadata']['all']['dc_date_end'][0]), 1, 1)

                new_project.information.parties = new_parties

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
                return {"page_title": self.find_menu()['title'], "form": e.render(), "form_only": False, 'messages': self._get_messages()}

        return {"page_title": self.find_menu()['title'], "form": self.form.render(appstruct), "form_only": False, 'messages': self._get_messages(), 'page_help': page_help}


    @view_config(route_name="general")
    def general_view(self):
        page_help = ""
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise', ca_description=""), page='general').bind(request=self.request)
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Next', 'Save', ), use_ajax=False, ajax_options=redirect_options)

        if 'Next' in self.request.POST:
            self.request.POST['target'] = 'description'

        readonly = self.project is not None and not (self.project.state == ProjectStates.OPEN or self.project.state is None)
        return self.handle_form(self.form, schema, page_help, readonly=readonly)


    @view_config(route_name="description")
    def description_view(self):
        page_help = "Fully describe your project to encourage other researchers to reuse your data:"\
                    "<ul><li>The entered descriptions will be used for metadata record generation (ReDBox), " \
                    "provide detailed information that is relevant to the project as a whole.</li>"\
                    "<li>Focus on what is being researched, why it is being researched and who is doing the research. " \
                    "The research locations and how the research is being conducted will be covered in the <i>Methods</i>" \
                    " and <i>Datasets</i> steps later on.</li></ul>"
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise'), page="description").bind(
            request=self.request)


        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Next', 'Save', 'Previous'), use_ajax=False)

        if 'Next' in self.request.POST:
            self.request.POST['target'] = 'information'

        if 'Previous' in self.request.POST:
            self.request.POST['target'] = 'general'

        readonly = self.project is not None and not (self.project.state == ProjectStates.OPEN or self.project.state is None)
        return self.handle_form(self.form, schema, page_help, readonly=readonly)


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
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise'), page='information').bind(request=self.request, settings=self.config)
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Next', 'Save', 'Previous'), use_ajax=False)

        if 'Next' in self.request.POST:
            self.request.POST['target'] = 'methods'

        if 'Previous' in self.request.POST:
            self.request.POST['target'] = 'description'

        readonly = self.project is not None and not (self.project.state == ProjectStates.OPEN or self.project.state is None)
        return self.handle_form(self.form, schema, page_help, readonly=readonly)

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

        PREFIX_SEPARATOR = ":"
        METHODS_INDEX = string.join([schema.name, Project.methods.key], PREFIX_SEPARATOR)
        METHOD_TEMPLATE_INDEX = string.join([schema[METHODS_INDEX].children[0].name, Method.method_template_id.key], PREFIX_SEPARATOR)
        schema[METHODS_INDEX].children[0][METHOD_TEMPLATE_INDEX].templates_data = templates
        schema[METHODS_INDEX].children[0][METHOD_TEMPLATE_INDEX].template_categories = categories
        schema[METHODS_INDEX].children[0][METHOD_TEMPLATE_INDEX].widget=deform.widget.HiddenWidget()

        template_data = method_template#type("dummy_object", (object,), {})
        template_data.oid = "MethodsTemplate"
        template_data.schema = type("dummy_object", (object,), {})
        template_data.schema.templates_data = templates
        template_data.schema.template_categories = categories

        schema[METHODS_INDEX].templates_data = template_data

        DATA_SCHEMA_INDEX = string.join([schema[METHODS_INDEX].children[0].name, Method.data_type.key], PREFIX_SEPARATOR)
        METHOD_SCHEMA_PARENTS_INDEX = string.join([schema[METHODS_INDEX].children[0].name, Method.data_type.key, MethodSchema.parents.key], PREFIX_SEPARATOR)
        schema[METHODS_INDEX].children[0][DATA_SCHEMA_INDEX][METHOD_SCHEMA_PARENTS_INDEX].template_schemas = self.get_template_schemas()
#        assert False

        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Next', 'Save', 'Previous'), use_ajax=False)



        if 'Next' in self.request.POST:
            self.request.POST['target'] = 'datasets'

        if 'Previous' in self.request.POST:
            self.request.POST['target'] = 'information'

        appstruct = {}
        display = None
        controls = self.request.POST.items()
        if len(controls) > 0:
            try:
                appstruct = self.form.validate(controls)
                display = self.form.render(appstruct)
            except ValidationFailure, e:
                appstruct = e.cstruct
                display = e.render()

#            print "Post variables: " + str(appstruct)

#            old_models = self.session.query(Method).filter_by(project_id=self.project_id).all()
            for new_method_data in appstruct['project:methods']:
                if not new_method_data['method:id'] and 'method:method_template_id' in new_method_data and new_method_data['method:method_template_id']:
                    template_method = self.session.query(Method).filter_by(id=new_method_data['method:method_template_id']).first()
                    if template is None:
                        continue

                    new_method_dict = self.clone(template_method).dictify(schema[METHODS_INDEX].children[0])
#                    new_method_dict = new_method_dict['method']
                    del new_method_dict['method:id']
                    new_method_dict['method:project_id'] = new_method_data['method:project_id']
                    new_method_dict['method:method_template_id'] = new_method_data['method:method_template_id']
                    new_method_data.update(new_method_dict)

        readonly = self.project is not None and not (self.project.state == ProjectStates.OPEN or self.project.state is None)
        return self.handle_form(self.form, schema, page_help, appstruct=appstruct, display=display, readonly=readonly)


    @view_config(route_name="datasets")
    def datasets_view(self):
        # Helper method for recursively retrieving all fields in a schema
        def get_file_fields(data_entry_schema):
            if data_entry_schema is None:
                return []

            fields = []

            for field in data_entry_schema.parents:
                fields.extend(get_file_fields(field))

            for field in data_entry_schema.custom_fields:
                if field.type == 'file':
                    fields.append((field.id, field.name))

            return fields

        page_help = "<p>Add individual datasets that your project will be collecting.  This is the when and where using " \
                    "the selected data collection method (what, why and how).</p><p><i>Such that an iButton sensor that " \
                    "is used to collect temperature at numerous sites would have been setup once within the Methods step" \
                    " and should be set-up in this step for each site it is used at.</i></p>"

        datasets = self.session.query(Dataset).filter_by(project_id=self.project_id).all()
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise'), page="datasets").bind(request=self.request, datasets=datasets)

        # Get the index of datasets
        for i in range(len(schema.children)):
            if schema.children[i].name[-len(Project.datasets.key):] == Project.datasets.key:
                DATASETS_INDEX = i
                break
        # Find the DATASET_DATA_SOURCE_INDEX
        for i in range(len(schema.children[DATASETS_INDEX].children[0].children)):
            if schema.children[DATASETS_INDEX].children[0].children[i].name[-len(Dataset.dataset_data_source.key):] == Dataset.dataset_data_source.key:
                DATASET_DATA_SOURCE_INDEX = i
                break
        # Find teh DATASET_DATA_SOURCE_ID_INDEX
        for i in range(len(schema.children[DATASETS_INDEX].children[0].children[DATASET_DATA_SOURCE_INDEX].children)):
            if schema.children[DATASETS_INDEX].children[0].children[DATASET_DATA_SOURCE_INDEX].children[i].name[-len(DatasetDataSource.dataset_data_source_id.key):] == DatasetDataSource.dataset_data_source_id.key:
                DATASET_DATA_SOURCE_ID_INDEX = i
                break

        if self.project_id is not None:
            methods = self.session.query(Method).filter_by(project_id=self.project_id).all()

            if len(methods) <= 0:
                self.request.session.flash('You must configure at least one method before adding dataset\'s', 'warning')
                return HTTPFound(self.request.route_url('methods', project_id=self.project_id))

#            # Add dataset template data to each method if it exists
#            for method in methods:
#                method.template = self.session.query(Dataset).join(MethodTemplate).filter(Dataset.id == MethodTemplate.dataset_id).\
#                    filter(MethodTemplate.id == method.method_template_id).first()

            # Add method data to the field for information to create new templates.
            schema.children[DATASETS_INDEX].children[0].methods = methods
            schema.children[DATASETS_INDEX].children[0].widget.get_file_fields = get_file_fields



#            method_schemas = []
#            for method in methods:
#                dataset_children = convert_schema(SQLAlchemyMapping(Dataset, unknown='raise')).children
#
#                DATA_SOURCE_CONFIGURATION_GROUP_NAME = "data_source_configuration"
#                # Find the DATA_CONFIG_INDEX
#                for i in range(len(dataset_children)):
#                    if dataset_children[i].name[-len(DATA_SOURCE_CONFIGURATION_GROUP_NAME):] == DATA_SOURCE_CONFIGURATION_GROUP_NAME:
#                        DATA_CONFIG_INDEX = i
#                        break
#
#                # Selectively show only the selected data source per method.
#                if method.data_source is not None and 'DATA_CONFIG_INDEX' in locals():
#                    for data_source in dataset_children[DATA_CONFIG_INDEX].children:
#                        if fix_schema_field_name(data_source.name) == method.data_source:
#                            # Add dynamic data to pull data sources
#                            if fix_schema_field_name(data_source.name) == PullDataSource.__tablename__:
#                                for child in data_source.children:
#                                    if fix_schema_field_name(child.name) == PullDataSource.file_field.key:
#                                        fields = get_all_fields(method.data_type)
#                                        field_values = []
#                                        for i in range(len(fields)):
#                                            if fields[i].type == "file":
#                                                field_values.append((fields[i].id, fields[i].name))
#
#                                        child.widget.values = tuple(field_values)
#
#                            # Set the data source
#                            dataset_children[DATA_CONFIG_INDEX].children = [data_source]
#                            break
#                elif 'DATA_CONFIG_INDEX' in locals():
#                    dataset_children[DATA_CONFIG_INDEX].children = []
#                    dataset_children[DATA_CONFIG_INDEX].description = "No associated data source - please select a datasource on the Methods page."
#
#                # Get the dataset template if there is one
#                if method.method_template_id:
#                    template = self.session.query(Dataset).join(MethodTemplate).filter(Dataset.id == MethodTemplate.dataset_id).\
#                        filter(MethodTemplate.id == method.method_template_id).first()
#
#                # Set all field defaults based on the template.
#                for child in dataset_children:
#                    if fix_schema_field_name(child.name) == 'method_id':
##                        child.missing = method.id
#                        child.default = method.id
##                    else:
#                        # If there is a template for datasets of this method, set all fields default values accordingly
#                    elif template:
#                        name = fix_schema_field_name(child.name)
#                        if name != "id" and hasattr(template, name):
#                            child.default = getattr(template, name, colander.null)
#                        elif name != "id":
#                            logger.warn("Schema has field template doesn't: %s" % name)
#
#
#                method_schemas.append(colander.MappingSchema(*dataset_children, name=(method.method_name and method.method_name or 'Un-named')))
#
#            method_select_schema = SelectMappingSchema(*method_schemas, name="dataset", collapsed=False,
#                select_title="Select dataset method type", select_description="<i>Changing will overwrite all fields.</i>")
#
#
#
#        else:
#            method_select_schema = SelectMappingSchema(select_title="Method", name="dataset" ,collapsed=False)
#
#        schema.children[DATASETS_INDEX].children = [method_select_schema]



        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Next', 'Save', 'Previous'), use_ajax=False)

        if 'Next' in self.request.POST:
            self.request.POST['target'] = 'submit'

        if 'Previous' in self.request.POST:
            self.request.POST['target'] = 'methods'

        # If a new dataset was added through the wizard - Update the appstruct with that datasets' template's data
        appstruct = None
        display = None
        controls = self.request.POST.items()
        if len(controls) > 0:
            try:
                appstruct = self.form.validate(controls)
                display = self.form.render()
            except ValidationFailure, e:
                appstruct = e.cstruct
                display = e.render()

#            print "Post variables: " + str(appstruct)

#            old_models = self.session.query(Method).filter_by(project_id=self.project_id).all()
            for new_dataset_data in appstruct['project:datasets']:
                # If this is a newly created dataset
                if not new_dataset_data['dataset:id'] and 'dataset:method_id' in new_dataset_data and new_dataset_data['dataset:method_id']:
                    method = self.session.query(Method).filter_by(id=new_dataset_data['dataset:method_id']).first()
                    template_dataset = self.session.query(Dataset).join(MethodTemplate).filter(Dataset.id == MethodTemplate.dataset_id).\
                                            filter(MethodTemplate.id == method.method_template_id).first()
                    if template_dataset is None:
                        continue

                    template_clone = self.clone(template_dataset)

                    # Pre-fill with first project point location
                    project_locations = self.session.query(Location).join(Metadata).filter(Metadata.id==Location.metadata_id).filter_by(project_id=self.project_id).all()
                    for location in project_locations:
                        if location.is_point():
                            location_clone = self.clone(location)
                            location_clone.metadata_id = None
                            template_clone.dataset_locations.append(location_clone)
                            break

                    # Copy all data from the template
                    new_dataset_dict = template_clone.dictify(schema.children[DATASETS_INDEX].children[0])


#                    new_method_dict = new_method_dict['method']
                    del new_dataset_dict['dataset:id']
                    new_dataset_dict['dataset:project_id'] = new_dataset_data['dataset:project_id']
                    new_dataset_dict['dataset:method_id'] = new_dataset_data['dataset:method_id']
                    new_dataset_data.update(new_dataset_dict)

        readonly = self.project is not None and not (self.project.state == ProjectStates.OPEN or self.project.state is None)
        return self.handle_form(self.form, schema, page_help, appstruct=appstruct, display=display, readonly=readonly)


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
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise'), page="submit").bind(request=self.request)

        if self.project is not None:
            # Create full self.project schema and form (without filtering to a single page as usual)
            val_schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise', ca_validator=project_validator, )).bind(request=self.request, settings=self.config)

            val_form = Form(val_schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Next', 'Save', 'Previous'), use_ajax=False)

            appstruct = self.project.dictify(val_schema)
            try:
                val_form.validate_pstruct(appstruct)
                self.error = []
            except ValidationFailure, e:
                errors = self.find_errors(e.error)
                sorted_errors = []
                last_page = None
                for (page, field, error) in errors:
                    if page != last_page:
                        last_page = page
                        sorted_errors.append((page, self.find_menu(page)['title'], []))

                    sorted_errors[-1][2].append((field, error))
                self.error = sorted_errors
        else:
            self.error = []

            # TODO: Validate the project and set it to self for all workflow steps to use.

        redbox_records = []
        ingesters = []
        for dataset in self.project.datasets:
            if dataset.publish_dataset:
                metadata_record = self.session.query(Metadata).filter_by(dataset_id=dataset.id).first()
                redbox_uri = None
                if metadata_record is not None:
                    redbox_uri = metadata_record.redbox_uri
                redbox_records.append((dataset.name, redbox_uri,
                                       self.request.route_url("view_record", project_id=self.project_id, dataset_id=dataset.id),
                                       self.request.route_url("delete_record", project_id=self.project_id, dataset_id=dataset.id)))

            dataset_method = self.session.query(Method).filter_by(id=dataset.method_id).first()
            ingesters.append((dataset.name, dataset_method.data_source, dataset_method.data_type.name))

        for i in range(len(schema.children)):
            if schema.children[i].name[-len('validation'):] == 'validation':
                schema.children[i].children[0].validation_errors = self.error
            if schema.children[i].name[-len('records'):] == 'records':
                schema.children[i].children[0].records = redbox_records
            if schema.children[i].name[-len('ingesters'):] == 'ingesters':
                schema.children[i].children[0].ingesters = ingesters

        SUBMIT_TEXT = "Submit"
        REOPEN_TEXT = "Reopen"
        DISABLE_TEXT = "Disable"
        APPROVE_TEXT = "Approve"
        DELETE_TEXT = "Delete"

        buttons=()
        if (self.project.state == ProjectStates.OPEN or self.project.state is None) and len(self.error) <= 0:
            buttons += (SUBMIT_TEXT,)
        elif self.project.state == ProjectStates.SUBMITTED:
            buttons += (REOPEN_TEXT, APPROVE_TEXT)
        elif self.project.state == ProjectStates.ACTIVE:
            buttons += (DISABLE_TEXT,)
        elif self.project.state == ProjectStates.DISABLED:
            buttons += (DELETE_TEXT,)

        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=buttons, use_ajax=False)

        response = self.handle_form(self.form, schema, page_help)

        if SUBMIT_TEXT in self.request.POST and 'id' in self.request.POST and (self.project.state == ProjectStates.OPEN or self.project.state is None) and len(self.error) <= 0:
            self.project.state = ProjectStates.SUBMITTED
            # TODO: fill citation data

            # Fill citation fields
            self.project.information.citation_title = self.project.information.project_title
#            self.project.information.citation_creators = self.project.information.parties  TODO: Citation creators
            self.project.information.citation_edition = None
            self.project.information.citation_publisher = "James Cook University"
            self.project.information.citation_place_of_publication = "James Cook University"
            # Type of Data?
            self.project.information.citation_url = "" # TODO:  CC-DAM Data Link
            self.project.information.citation_context = self.project.information.project_title

        if REOPEN_TEXT in self.request.POST and 'id' in self.request.POST and self.project.state == ProjectStates.SUBMITTED:
            self.project.state = ProjectStates.OPEN

        if DISABLE_TEXT in self.request.POST and 'id' in self.request.POST and self.project.state == ProjectStates.ACTIVE:
            self.project.state = ProjectStates.DISABLED
            # TODO: Disable in CC-DAM

        if DELETE_TEXT in self.request.POST and 'id' in self.request.POST and self.project.state == ProjectStates.DISABLED:
            # TODO: Delete
            pass

        if APPROVE_TEXT in self.request.POST and 'id' in self.request.POST and self.project.state == ProjectStates.SUBMITTED:
            try:
                self.ingester_api.post(self.project)
                self.ingester_api.close()
                logger.info("Project has been added to ingesterplatform successfully: %s", self.project.id)
            except Exception as e:
                logger.exception("Project failed to add to ingesterplatform: %s", self.project.id)
                self.request.session.flash("Failed to configure data storage and ingestion.", 'error')
                self.request.session.flash("Error: %s" % e, 'error')
                return response

            try:
                dataset_services_csv = [self.dataset_to_mint_service_csv(dataset.id) for dataset in self.project.datasets]

                # TODO: Upload service csv files to Mint and get mint url and identifier

                project_csv = self.record_to_redbox_csv(self.project.information.id)
                dataset_records_csv = [self.record_to_redbox_csv(self.session.query(Metadata).filter(Metadata.dataset_id==dataset.id).first().id) for dataset in self.project.datasets]
                dataset_records_csv = [self.record_to_redbox_csv(id) for id in self.session.query(Metadata).join(Dataset).filter(Metadata.dataset_id==Dataset.id).filter(Dataset.project_id==self.project_id).all()]

                # TODO: Upload the csv files to ReDBox and get the links and identifiers

                logger.info("Project has been added to ReDBox successfully: %s", self.project.id)

            except Exception as e:
                logger.exception("Project failed to add to ReDBox: %s", self.project.id)
                self.request.session.flash("Sorry, the project failed to generate or add metadata records to ReDBox, please try agiain.", 'error')
                self.request.session.flash("Error: %s" % e, 'error')
                return response


            # Change the state to active
            self.project.state = ProjectStates.ACTIVE
            logger.info("Project has been approved successfully: %s", self.project.id)

        return response

    def dataset_to_mint_service_csv(self):
        service_csv = ""

        # TODO: Dataset to mint service csv mappings

        return service_csv

    def record_to_redbox_csv(self, metadata_id):
        redbox_csv = ""

        metadata = self.session.query(Metadata).filter_by(id==metadata_id).first()

        #TODO: Metadata to redbox csv mappings.

        return redbox_csv

    def generate_dataset_record(self, dataset_id):
        metadata_id = self.session.query(Metadata.id).filter_by(dataset_id=dataset_id).first()

        metadata_template = self.session.query(Metadata).join(Project).filter(Metadata.project_id==Project.id).join(Dataset).filter(Project.id==Dataset.project_id).filter(Dataset.id==dataset_id).first()

        template_clone = self.clone(metadata_template)
        template_clone.id = metadata_id
        template_clone.project_id = None
        template_clone.dataset_id = dataset_id
        # TODO:  Generate/add dataset specific metadata

        self.session.merge(template_clone)
        return template_clone


    @view_config(route_name="delete_record")
    def delete_record_view(self):
        dataset_id = self.request.matchdict['dataset_id']

        record = self.session.query(Metadata).filter_by(dataset_id=dataset_id).first()
        if record is not None:
            self.session.delete(record)

        self.request.session.flash('Dataset record successfully deleted (will be recreated when needed).', 'success')

        target = 'submit'
        return HTTPFound(self.request.route_url(target, project_id=self.project_id))

#-----------------------Dataset Record View/Edit-----------------------------------
    @view_config(route_name="view_record")
    @view_config(route_name="edit_record")
    def edit_record_view(self):
        dataset_id = self.request.matchdict['dataset_id']

        page_help=""
        schema = convert_schema(SQLAlchemyMapping(Metadata, unknown='raise',)).bind(request=self.request, settings=self.config)
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id, dataset_id=dataset_id), buttons=("Cancel", "Save & Close", "Save",), use_ajax=False)

        readonly = (self.project is not None and not (self.project.state == ProjectStates.OPEN or self.project.state is None)) or self.request.matched_route == "view_dataset_record"

        # If the form is being saved (there would be 1 item in controls if it is a fresh page with a project id set)
        if len(self.request.POST) > 1 and not 'Cancel' in self.request.POST:
            self.request.POST['metadata:dataset_id'] = dataset_id
            controls = self.request.POST.items()

            # In either of the below cases get the data as a dict and get the rendered form
            try:
                appstruct = self.form.validate(controls)
                display = self.form.render(appstruct)
            except ValidationFailure, e:
                appstruct = e.cstruct
                display = e.render()

            # save the data even if it didn't validate - this allows the user to easily navigate and fill fields out as they get the info.
            metadata_id = self._save_form(appstruct, appstruct['metadata:id'], Metadata)
        else:
            appstruct = {}

            model = self.session.query(Metadata).filter_by(dataset_id=dataset_id).first()
            if model is None:
                model = self.generate_dataset_record(dataset_id)

            appstruct = model.dictify(schema)


            try:
                appstruct = self.form.validate_pstruct(appstruct)
                display = self.form.render(appstruct, readonly=readonly)
            except ValidationFailure, e:
                appstruct = e.cstruct
                display = e.render()
                # If there is a target workflow step set then change to that page.


        if 'Cancel' in self.request.POST or 'Save_&_Close' in self.request.POST:
            target = 'submit'
            if self.form.use_ajax:
                pass
            else:
                return HTTPFound(self.request.route_url(target, project_id=self.project_id))

        return {"page_title": self.find_menu()['title'], "form": display, "form_only": False, 'messages': self._get_messages(), 'page_help': page_help, 'readonly': readonly}



    # --------------------WORKFLOW ACTION/SIDEBAR VIEWS-------------------------------------------
    @view_config(route_name="dataset_logs")
    def dataset_logs_view(self):
        dataset_id = int(self.request.matchdict['dataset_id'])
        logs = self.ingester_api.getIngesterEvents(dataset_id)

        content = ''.join(["%s - %s - %s - %s - %s - %s.\n" % (log['id'], log['dataset_id'], log['timestamp'], log['class'], log['level'], log['message'].strip()) for log in logs])
        res = Response(content_type="text")
        res.body = content
        return res

    @view_config(route_name="logs")
    def logs_view(self):
#        print "POST VARS" + str(self.request.POST) + " " + str(self.project_id)
        page_help="View ingester event logs for project datasets."
        schema = IngesterLogs()
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Refresh',), use_ajax=False)

        datasets = self.session.query(Dataset).filter_by(project_id=self.project_id).order_by(Dataset.name).all()

        for dataset in datasets:
            if dataset.dam_id is None:
                dataset.logs_error = ["Ingester hasn't been activated yet: %s" % dataset.title]
            else:
                try:
                    dataset.logs = self.ingester_api.getIngesterEvents(dataset.dam_id)
#                    print dataset.logs
#                    print range(len(dataset.logs)).reverse()
                    for i in reversed(range(len(dataset.logs))):
#                        print "Level filter: " + str(dataset.logs[i]['level']) + " : " + str(self.request.POST['level'])
                        if 'level' in self.request.POST and str(self.request.POST['level']) != "ALL" and str(dataset.logs[i]['level']) != str(self.request.POST['level']):
                            del dataset.logs[i]
                            continue
#                        print "data: %s" % dataset.logs[i]['timestamp'].partition('T')[0]
                        try:
                            log_date = datetime.strptime(str(dataset.logs[i]['timestamp']).partition('T')[0], '%Y-%m-%d').date()
                        except Exception as e:
                            logger.exception("Log date wasn't parsable: %s" % e)
                            continue

                        if 'start_date' in self.request.POST and self.request.POST['start_date']:
                            start_date = datetime.strptime(self.request.POST['start_date'].partition('T')[0], '%Y-%m-%d').date()
                            if log_date < start_date:
                                del dataset.logs[i]
                                continue

                        if 'end_date' in self.request.POST and self.request.POST['end_date']:
                            end_date = datetime.strptime(self.request.POST['end_date'].partition('T')[0], '%Y-%m-%d').date()
                            if log_date > end_date:
                                del dataset.logs[i]
                                continue

                except Exception as e:
                    logger.exception("Exception getting logs: %s", e)
                    dataset.logs_error = "Error occurred: %s" % e

        schema.children[1].datasets = datasets

        if 'target' in self.request.POST and self.request.POST['target']:
            target = self.request.POST['target']
            return HTTPFound(self.request.route_url(target, project_id=self.project_id))

        appstruct = {}
        if self.request.POST.items() > 0:
            try:
                appstruct = self.form.validate(self.request.POST.items())
                display = self.form.render(appstruct)
            except ValidationFailure, e:
                appstruct = e.cstruct
                display = e.render()


        return {"page_title": self.find_menu()['title'], "form": display, "form_only": False, 'messages': self._get_messages(), 'page_help': page_help}

    @view_config(route_name="add_data")
    def add_data_view(self):
        raise NotImplementedError("This page hasn't been implemented yet.")

        page_help=""
        schema = IngesterLogs()
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Refresh',), use_ajax=False)


        return self.handle_form(self.form, schema, page_help)

    @view_config(route_name="manage_data")
    def manage_data_view(self):
        raise NotImplementedError("This page hasn't been implemented yet.")

        page_help=""
        schema = IngesterLogs()
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Refresh',), use_ajax=False)


        return self.handle_form(self.form, schema, page_help)

    @view_config(route_name="permissions")
    def permissions_view(self):
        raise NotImplementedError("This page hasn't been implemented yet.")

        page_help=""
        schema = IngesterLogs()
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Refresh',), use_ajax=False)


        return self.handle_form(self.form, schema, page_help)

    @view_config(route_name="duplicate")
    def duplicate_view(self):
        raise NotImplementedError("This page hasn't been implemented yet.")

        page_help=""
        schema = IngesterLogs()
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Refresh',), use_ajax=False)


        return self.handle_form(self.form, schema, page_help)

    # --------------------WORKFLOW EXCEPTION VIEWS-------------------------------------------
    @view_config(context=Exception, route_name="workflow_exception")
    def exception_view(self):
        logger.exception("An exception occurred in global exception view: %s", self.context)
        if hasattr(self, self.request.matched_route.name + "_view"):
            try:
                self.request.session.flash('Sorry, please try again - there was an exception: ' + cgi.escape(str(self.context)), 'error')
                self.request.POST.clear()
                response = getattr(self, str(self.request.matched_route.name) + "_view")()
                return response
            except Exception:
                logger.exception("Exception occurred while trying to display the view without variables: %s", Exception)
                messages = {
                    'error_messages': ['Sorry, we are currently experiencing difficulties: ' % self.context],
                    'success_messages': [],
                    'warning_messages': []
                }
                return {"page_title": self.find_menu()['title'], "form": '', "messages": messages, "form_only": False}
        else:
            try:
                messages = {
                    'error_messages': ['Sorry, we are currently experiencing difficulties: ' % self.context],
                    'success_messages': [],
                    'warning_messages': []
                }
                return {"page_title": self.find_menu()['title'], "form": 'This address is not valid, please don\'t directly edit the address bar: ' + cgi.escape(str(self.context)), "form_only": False, "messages": messages}
            except:
                self.request.session.flash('There is no page at the requested address, please don\'t edit the address bar directly.', 'error')
                if self.request.matchdict and self.request.matchdict['route'] and (self.request.matchdict['route'].split("/")[0]).isnumeric():
                    project_id = int(self.request.matchdict['route'].split("/")[0])
                    print 'isnumeric: ' + str(project_id)
                    return HTTPFound(self.request.route_url('general', project_id=project_id))
                else:
                    return HTTPFound(self.request.route_url('create'))


#            return {"page_title": self.context, "form": 'This address is not valid, please don\'t directly edit the address bar: ' + str(self.context), "form_only": False}

    #    @view_config(context=sqlalchemy.orm.exc.SQLAlchemyError, renderer="../templates/exception.pt")
    @view_config(context=sqlalchemy.exc.SQLAlchemyError, renderer="../templates/exception.pt")
    def sqlalchemy_exception_view(self):
        self.session.rollback()
        logger.exception("A database exception occurred in global exception view: %s", self.context)

        messages = {
            'error_messages': ['Sorry, we are currently experiencing difficulties.'],
            'success_messages': [],
            'warning_messages': []
        }
        if 'MySQL server has gone away' in self.context:
            try:
#                self.request.session.flash('Sorry, please try again - there was an exception: ' + cgi.escape(str(self.context)), 'error')
                self.request.POST.clear()
                response = getattr(self, str(self.request.matched_route.name) + "_view")()
                return response
            except Exception:
                pass

        return {"exception": "%s" % self.context, "messages": messages}




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
#            new_model.method_template_id = model.id
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
