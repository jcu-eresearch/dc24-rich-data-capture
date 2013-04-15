import ConfigParser
import cgi
import copy
from datetime import datetime, date
import json
import logging
from jcudc24provisioning.controllers.authentication import DefaultPermissions
from jcudc24provisioning.controllers.method_schema_scripts import get_method_schema_preview
import os
from lxml import etree
import random
from string import split
import string
import urllib2
from paste.deploy.converters import asint
import pyramid
from pyramid.security import authenticated_userid, NO_PERMISSION_REQUIRED, has_permission, view_execution_permitted
import requests
import sqlalchemy
from sqlalchemy.orm.properties import ColumnProperty, RelationProperty
from sqlalchemy.orm.util import object_mapper
import colander
from jcudc24provisioning.controllers.redbox_mint import ReDBoxWraper
from jcudc24provisioning.controllers.sftp_filesend import SFTPFileSend
import deform
from deform.exception import ValidationFailure
from deform.form import Form, Button
from pyramid.url import route_url
import inspect
from sqlalchemy import create_engine, distinct
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
from jcudc24provisioning.models import DBSession, Base
from jcudc24provisioning.models.project import PullDataSource, Metadata, UntouchedPages, IngesterLogs, Location, \
    ProjectTemplate,method_template,DatasetDataSource, Project, project_validator, ProjectStates, Sharing, CreatePage, MetadataNote, Method, Party, Dataset, MethodSchema, grant_validator, MethodTemplate, ManageData
from jcudc24provisioning.views.ca_scripts import convert_schema, fix_schema_field_name
from jcudc24provisioning.controllers.ingesterapi_wrapper import IngesterAPIWrapper
from jcudc24provisioning.views.mint_lookup import MintLookup
from pyramid.request import Request
from jcudc24provisioning.scripts.create_redbox_config import create_json_config
from jcudc24provisioning.models.website import User, ProjectPermissions, Permission


__author__ = 'Casey Bajema'

logger = logging.getLogger(__name__)

# Pyramid seems to have no way to dynamically find a views permission, so we need to manually re-add it here...
# Workflow page href needs to be synchronised with UntouchedPages table in project.py
WORKFLOW_STEPS = [
        {'href': 'create', 'title': 'Create', 'page_title': 'Create a New Project', 'hidden': True, 'tooltip': '', 'view_permission': DefaultPermissions.CREATE_PROJECT},
        {'href': 'general', 'title': 'Details', 'page_title': 'General Details', 'tooltip': 'Title, grants, people and collaborators', 'view_permission': DefaultPermissions.VIEW_PROJECT},
        {'href': 'description', 'title': 'Description', 'page_title': 'Description', 'tooltip': 'Project descriptions used for publishing records', 'view_permission': DefaultPermissions.VIEW_PROJECT},
        {'href': 'information', 'title': 'Information', 'page_title': 'Associated Information', 'tooltip': 'Collects metadata for publishing records', 'view_permission': DefaultPermissions.VIEW_PROJECT},
        {'href': 'methods', 'title': 'Methods', 'page_title': 'Data Collection Methods', 'tooltip': 'Ways of collecting data', 'view_permission': DefaultPermissions.VIEW_PROJECT},
        {'href': 'datasets', 'title': 'Datasets', 'page_title': 'Datasets (Collections of Data)', 'tooltip': 'Configure each individual data collection location'},
        {'href': 'view_record', 'title': 'Generated Dataset Record', 'page_title': 'Generated Dataset Record', 'hidden': True, 'tooltip': 'View datasets generated metadata record', 'view_permission': DefaultPermissions.VIEW_PROJECT},
        {'href': 'edit_record', 'title': 'Generated Dataset Record', 'page_title': 'Generated Dataset Record', 'hidden': True, 'tooltip': 'Edit datasets generated metadata record', 'view_permission': DefaultPermissions.EDIT_PROJECT},
        {'href': 'delete_record', 'title': 'Generated Dataset Record', 'page_title': 'Generated Dataset Record', 'hidden': True, 'tooltip': 'Delete datasets generated metadata record', 'view_permission': DefaultPermissions.EDIT_PROJECT},
        {'href': 'submit', 'title': 'Submit', 'page_title': 'Submit & Approval', 'tooltip': 'Overview, errors and project submission for administrator approval', 'view_permission': DefaultPermissions.VIEW_PROJECT},
        {'href': 'template', 'title': 'Template', 'page_title': 'Template Details', 'hidden': True, 'tooltip': 'Edit template specific details such as category', 'view_permission': DefaultPermissions.ADMINISTRATOR},
]

WORKFLOW_ACTIONS = [
        {'href': 'general', 'title': 'Configuration', 'page_title': 'General Details', 'tooltip': 'Project settings used to create this project', 'view_permission': DefaultPermissions.VIEW_PROJECT},
        {'href': 'logs', 'title': 'View Logs', 'page_title': 'Ingester Event Logs', 'hidden_states': [ProjectStates.OPEN, ProjectStates.SUBMITTED], 'tooltip': 'Event logs received from the data ingester', 'view_permission': DefaultPermissions.VIEW_PROJECT},
#        {'href': 'add_data', 'title': 'Add Data', 'page_title': 'Add Data', 'hidden_states': [ProjectStates.OPEN, ProjectStates.SUBMITTED], 'tooltip': ''},
        {'href': 'manage_data', 'title': 'Manage Data', 'page_title': 'Manage Data', 'hidden_states': [ProjectStates.OPEN, ProjectStates.SUBMITTED], 'tooltip': 'Allows viewing, editing or adding of data and ingester configurations', 'view_permission': DefaultPermissions.VIEW_PROJECT},
        {'href': 'permissions', 'title': 'Sharing', 'page_title': 'Sharing & Permissions', 'tooltip': 'Change who can access and edit this project', 'view_permission': DefaultPermissions.EDIT_SHARE_PERMISSIONS},
        {'href': 'duplicate', 'title': 'Duplicate Project', 'page_title': 'Duplicate Project', 'tooltip': 'Create a new project using this project as a template', 'view_permission': DefaultPermissions.VIEW_PROJECT},
        {'href': 'create_template', 'title': 'Make into Template', 'page_title': 'Create Project Template', 'tooltip': 'Suggest to the administrators that this project should be a template', 'hidden': True, 'view_permission': DefaultPermissions.ADMINISTRATOR},
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

@view_defaults(renderer="../templates/workflow_form.pt", permission=DefaultPermissions.ADMINISTRATOR)
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
            self._readonly = has_permission(DefaultPermissions.EDIT_PROJECT, self.context, self.request) and self.project is not None and not (self.project.state == ProjectStates.OPEN or self.project.state is None or self.project.state == ProjectStates.SUBMITTED)
        return self._readonly

    @property
    def title(self):
        if '_title' not in locals():
            self._title = self.find_menu()['page_title']
        return self._title

    @property
    def project(self):
        if '_project' not in locals():
            self._project = self.session.query(Project).filter_by(id=self.project_id).first()
            if self._project is None:
                raise HTTPClientError("You are trying to access a project that doesn't exist.  Either you have edited the address bar directly or the project no longer exists.")
#                self.request.session.flash("The requested project doesn't exist.  Either you have edited the address bar directly or the project you are requesting no longer exists.")
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
    def redbox(self):
        if '_redbox' not in locals():
            # Get Redbox conconfigurations
            alert_url = self.config.get("redbox.url") + self.config.get("redbox.alert_url")
            host = self.config.get("redbox.ssh_host")
            port = self.config.get("redbox.ssh_port")
            private_key = self.config.get("redbox.rsa_private_key")
            username = self.config.get("redbox.ssh_username")
            password = self.config.get("redbox.ssh_password")
            harvest_dir = self.config.get("redbox.ssh_harvest_dir")
            tmp_dir = self.config.get("redbox.tmpdir")
            identifier_pattern = self.config.get("redbox.identifier_pattern")
            data_portal = self.request.route_url("record_data", metadata_id="")

            self._redbox = ReDBoxWraper(url=alert_url, data_portal=data_portal, identifier_pattern=identifier_pattern, ssh_host=host, ssh_port=port, tmp_dir=tmp_dir, harvest_dir=harvest_dir,
                ssh_username=username, rsa_private_key=private_key, ssh_password=password)

        return self._redbox

    @property
    def page(self):
        if '_page' not in locals():
            self._page = None
            for menu in WORKFLOW_STEPS + WORKFLOW_ACTIONS:
                if self.request.url.endswith(menu['href']):
                    self._page = menu
                    break
        return self._page

    @property
    def next(self):
        if '_next' not in locals():
            self._next = None # Set as None if this is the last visible step or it isn't a workflow page.

            if (self.page in WORKFLOW_STEPS):
                for i in range(len(WORKFLOW_STEPS))[WORKFLOW_STEPS.index(self.page) + 1:]:
                    if 'hidden' not in WORKFLOW_STEPS[i] or not WORKFLOW_STEPS[i]['hidden']:
                        self._next = WORKFLOW_STEPS[i]
                        break

        return self._next

    @property
    def previous(self):
        if '_previous' not in locals():
            self._previous = None # Set as None if this is the first visible step or it isn't a workflow page.

            if self.page in WORKFLOW_STEPS and WORKFLOW_STEPS.index(self.page) > 0:
                for i in reversed(range(len(WORKFLOW_STEPS))[:WORKFLOW_STEPS.index(self.page) - 1]):
                    if 'hidden' not in WORKFLOW_STEPS[i] or not WORKFLOW_STEPS[i]['hidden']:
                        self._previous = WORKFLOW_STEPS[i]
                        break

        return self._previous

    @property
    def schema(self):
        if self.form is None:
            return None
        return self.form.schema

    @property
    def model_type(self):
        if self.form is None or not hasattr(self.form.schema, '_reg'):
            return None

        return self.form.schema._reg.cls


    @property
    def model_id(self):
        if '_model_id' not in locals():
            if self.model_type is None:
                self._model_id = None
            elif self.model_type == Project:
                self._model_id = self.project_id
            elif self.model_type.__tablename__ + '_id' in self.request.matchdict:
                self._model_id = self.request.matchdict[self.model_type.__name__ + '_id']
            else:
                self._model_id = self.request.POST.get(self.model_type.__tablename__ + ":id", None)
        return self._model_id

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

            # Hide menu items that shouldn't be displayed (sub-pages)
            if 'hidden' in menu and menu['hidden'] is True:
                hidden.append(menu)

            # Hide manu items that the user doesn't have permission to see
            if 'view_permission' in menu and not has_permission(menu['view_permission'], self.context, self.request):
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

            # Hide menu items that shouldn't be displayed (sub-pages)
            if ('hidden' in menu and menu['hidden'] is True) or ('hidden_states' in menu and self.project is not None and self.project.state in menu['hidden_states']):
                hidden.append(menu)

            # Hide manu items that the user doesn't have permission to see
            if 'view_permission' in menu and not has_permission(menu['view_permission'], self.context, self.request):
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
        if href is None:
            return None
        return self.request.route_url(href, project_id=self.project_id)

# --------------------WORKFLOW STEP METHODS-------------------------------------------
    def _save_form(self, appstruct=None, model_id=None, model_type=None):
        if appstruct is None:
            appstruct = self._get_post_appstruct()
        if model_type is None:
            model_type = self.model_type
        if model_id is None:
            model_id = self.model_id
            model_id_field_name = "%s:id" % model_type.__tablename__
            if model_id is None and model_id_field_name in appstruct:
                model_id = appstruct[model_id_field_name]

         # In either of the below cases get the data as a dict and get the rendered form
#        if 'POST' != self.request.method or len(self.request.POST) == 0 or self.readonly or \
#                'model_id' not in self.request.POST or 'model_type' not in self.request.POST:
#            return

#        model_id = self.request.POST['model_id']
#        model_type = globals()[self.request.POST['model_type']]
        changed = False

        model = self.session.query(model_type).filter_by(id=model_id).first()

        if model is None or not isinstance(model, model_type):
            if model_id is None or model_id == colander.null:
                model = model_type(appstruct=appstruct)
                if model is not None:
                    self.session.add(model)
                    changed = True
                else:
                    return
            else:
                raise ValueError("No project found for the given project id(" + model_id + "), please do not directly edit the address bar.")

        else:
            # Update the model with all fields in the data
            if model.update(appstruct):
                self.session.merge(model)
                changed = True

        self._model = model

        try:
            self.session.flush()
            return changed
#            self.request.session.flash("Project saved successfully.", "success")
        except Exception as e:
            logger.exception("SQLAlchemy exception while flushing after save: %s" % e)
            self.request.session.flash("There was an error while saving the project, please try again.", "error")
            self.request.session.flash("Error: %s" % e, "error")
            self.session.rollback()
#       self.session.remove()

    def _touch_page(self):
        # Set the page as edited so future visits will show the page with validation
        if self.project_id is not None:
            untouched_pages = self.session.query(UntouchedPages).filter_by(project_id=self.project_id).first()
            if untouched_pages is None:
                untouched_pages = UntouchedPages()
                untouched_pages.project_id = self.project_id
                self.session.add(untouched_pages)

            # If this causes exceptions the UntouchedPages->column names (in project.py) need to by the same as href values in WORKFLOW_STEPS above.
            page = self.find_menu()['href']
            setattr(untouched_pages, page, True)

    def _is_page_touched(self):
        # If the page has been saved previously, show the validated form
        untouched_pages = self.session.query(UntouchedPages).filter_by(project_id=self.project_id).first()
        page = self.find_menu()['href']
        return untouched_pages is not None and hasattr(untouched_pages, page) and getattr(untouched_pages, page) == True

##       If there is a target workflow step set then change to that page.
#        if self.request.POST['target']:
#            target = self.request.POST['target']
#        else:
#            target = self.request.matched_route.name
##        if form.use_ajax:
##            return {"page_title": self.title, "form": display, "form_only": form.use_ajax,  'messages' : self._get_messages() or '', 'page_help': page_help, 'readonly': readonly}
##        else:
#        return HTTPFound(self.request.route_url(target, project_id=self.project_id))

    def _render_model(self):
        if self._get_model_appstruct() is not None:
            if self._is_page_touched() and not self._readonly:
                try:
                    appstruct = self.form.validate_pstruct(self._get_model_appstruct())
                    display = self.form.render(appstruct)
                except ValidationFailure, e:
                    appstruct = e.cstruct
                    display = e.render()

            else:
                try:
                    # Try to display the form without validating
                    appstruct = self._get_model_appstruct(dates_as_string=False)
                    display = self.form.render(appstruct, readonly=self._readonly)
                except Exception, e:
                    try:
                        # If it fails, try validating - there are issues with dates where it can't display the string as read from the DB untill it is validated.
                        appstruct = self.form.validate_pstruct(appstruct)
                        display = self.form.render(appstruct, readonly=self._readonly)
                    except ValidationFailure, e:
                        display = e.render()   # Validation failed, ignore that it isn't touched and display the error form

            return display

        return None

    def _render_post(self, **kw):
        if self._get_post_appstruct() is not None:
            if hasattr(self, '_validation_error'):
                return self._validation_error.render()
            else:
                return self.form.render(self._get_post_appstruct(), **kw)

        return None


    def _get_model(self):
        if not hasattr(self, '_model'):
            if self.model_type is None or self.model_id is None:
                self._model = None
            else:
                self._model = self.session.query(self.model_type).filter_by(id=self.model_id).first()
        return self._model

    def _get_model_appstruct(self, dates_as_string=True):
        if not hasattr(self, '_model_appstruct'):
            if self._get_model() is not None:
                self._model_appstruct = self._get_model().dictify(self.form.schema, dates_as_string=dates_as_string)
            else:
                return {}

        return self._model_appstruct

    def _handle_form(self):
        if self.request.method == 'POST' and len(self.request.POST) > 0:
            # If this is a sub-request called just to save.
            if self.request.referrer == self.request.path_url:
                if self._save_form():
                    self._touch_page()

                # If this view has been called for saving only, return without rendering.
                view_name = inspect.stack()[1][3][:-5]
                if self.request.matched_route.name != view_name:
                    return True
            else:
                self._redirect_to_target(self.request.referrer)

    def _clone_model(self, source):
        """
        Clone a database model
        """
        if source is None:
            return None

        new_object = type(source)()
        for prop in object_mapper(source).iterate_properties:
            if (isinstance(prop, ColumnProperty) or isinstance(prop, RelationshipProperty) and prop.secondary is not None) and not prop.key == "id":
                setattr(new_object, prop.key, getattr(source, prop.key))
            elif isinstance(prop, RelationshipProperty) and 'exclude' not in prop.ca_registry:
                if isinstance(getattr(source, prop.key), list):
                    items = []
                    for item in getattr(source, prop.key):
                        items.append(self._clone_model(item))
                    setattr(new_object, prop.key, items)
                else:
                    setattr(new_object, prop.key, self._clone_model(getattr(source, prop.key)))

        if hasattr(new_object, "id"):
            new_object.id = None

        return new_object

    def _get_post_appstruct(self):
        if not hasattr(self, '_appstruct'):
            controls = self.request.POST.items()

            if 'POST' != self.request.method or len(self.request.POST) == 0:
                self._appstruct = {}
            else:
                try:
                    self._appstruct = self.form.validate(controls)
                except ValidationFailure, e:
                    self._validation_error = e
                    self._appstruct = e.cstruct

        return self._appstruct


    def _create_response(self, **kwargs):
        response_dict = {
            "page_title": kwargs.pop("page_title", self.title),
            "form": kwargs.pop("form", None),
            "form_only": kwargs.pop("form_only", False),
            'readonly': kwargs.pop('readonly', None),
            'messages': kwargs.pop('messages', self._get_messages()),
            "next_page": kwargs.pop("next_page", self.next),
            "prev_page": kwargs.pop("prev_page", self.previous),
            "page_help": kwargs.pop("page_help", ""),
            "logged_in": authenticated_userid(self.request),
            "page_help_hidden": kwargs.pop("page_help_hidden", True),
        }

        # Don't use a default directly in pop as it initialises the default even if not needed, this causes self.project
        # to be called which breaks any pages that it is valid for the project to not be in the database yet (create page).
        if response_dict['readonly'] is None:
            response_dict['readonly'] = self.readonly
        else:
            self._readonly = response_dict['readonly']

        # Lazy default initialisation as this has high overheads.
        if response_dict['form'] is None:
            response_dict['form'] = self._render_model()
        response_dict.update(kwargs)
        return response_dict

    # --------------------WORKFLOW STEP VIEWS-------------------------------------------
    @view_config(route_name="create", permission=DefaultPermissions.CREATE_PROJECT)
    def create_view(self):
        page_help = "<p>There are unique challenges associated with creating metadata (information about your data - eg. where,  when or why) and organising persistent storage for large scale projects.\
                            Data is often output in a variety of ways and requires unique handling, this tool enables you to:\
                            <ul>\
                                <li>Store your data persistently (<b>your data is backed up!</b>).</li>\
                                <li>Your data can be automatically processed when added (<b>100% customisable</b>).</li>\
                                <li>Specific data that is indexed is searchable (<b>you tell us how your data should be searched</b>).</li>\
                                <li>Fine grained metadata records are generated with almost no more work than a single record (<b>Creates high quality advertisements/publications for your data so you gain recognition</b>).</li>\
                                <li>Flexible methods of inputting data, you may manually input data through a form, simply upload files into a folder or even stream the data directly from your sensors.</li>\
                            </ul></p> \
                            <p>This project creation wizard helps pre-fill as many fields as possible to make the process as fast as possible:\
                            <ul>\
                                <li><b>New users can pre-fill many fields related to the data by selecting an associated grant.</b></li>\
                                <li><b>If you (or your department) are already in the system, select a Project Template.  Templates have been constructed for a number of research groups and their large-scale sensor projects.</b></li>\
                            </ul></p>\
                            <p><i>Tip:  To be added to the system please send a request using the contact form.</i> <br />\
                            <i>Tip:  Find a wealth of help by looking for the '?' symbols next to each page's headings and field names.</i></p>"

        schema = CreatePage(validator=grant_validator)
        templates = self.session.query(ProjectTemplate).order_by(ProjectTemplate.category).all()
        categories = []
        for template in templates:
            if not template.category in categories:
                categories.append(template.category)

        schema.children[1].templates_data = templates
        schema.children[1].template_categories = categories

        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id),
            buttons=('Create Project',), use_ajax=False, ajax_options=redirect_options)

        appstruct = self._get_post_appstruct()

        # If the form is being saved (there would be 1 item in controls if it is a fresh page with a project id set)
        if len(appstruct) > 0 and not hasattr(self, '_validation_error'):
            # In either of the below cases get the data as a dict and get the rendered form
            new_project = Project()
            new_project.project_creator = self.request.user.id
            new_project.creation_date = datetime.datetime.now()

            if 'template' in appstruct:
                template = self.session.query(Project).filter_by(id=appstruct['template']).first()
                if template is not None:
                    new_project = self._clone_model(template)
                    new_project.id = None
                    new_project.template = False
                    new_project.state = ProjectStates.OPEN

            if not new_project.information:
                new_info = Metadata()
                new_project.information = new_info

            new_parties = []
            if 'data_manager' in appstruct:
                data_manager = Party()
                data_manager.party_relationship = "isManagedBy"
                data_manager.identifier = appstruct['data_manager']
                new_parties.append(data_manager)

            if 'project_lead' in appstruct:
                project_lead = Party()
                project_lead.party_relationship = "hasCollector"
                project_lead.identifier = appstruct['project_lead']
                new_parties.append(project_lead)

            if 'grant' in appstruct:
                new_project.information.grant = appstruct['grant']
                activity_results = MintLookup(None).get_from_identifier(appstruct['grant'])

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

        return self._create_response(page_help=page_help, page_help_hidden=False, form=self._render_post(readonly=False), readonly=False)

    @view_config(route_name="general", permission=DefaultPermissions.VIEW_PROJECT)
    def general_view(self):
        page_help = ""
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise', ca_description=""), page='general', restrict_admin=not has_permission(DefaultPermissions.ADVANCED_FIELDS, self.context, self.request)).bind(request=self.request)
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Next', 'Save', ), use_ajax=False, ajax_options=redirect_options)

        # If this page was only called for saving and a rendered response isn't needed, return now.
        if self._handle_form():
            return

#        self.project.information.to_xml()
#        create_json_config()

        return self._create_response(page_help=page_help)


    @view_config(route_name="description", permission=DefaultPermissions.VIEW_PROJECT)
    def description_view(self):
        page_help = "Fully describe your project to encourage other researchers to reuse your data:"\
                    "<ul><li>The entered descriptions will be used for metadata record generation (ReDBox), " \
                    "provide detailed information that is relevant to the project as a whole.</li>"\
                    "<li>Focus on what is being researched, why it is being researched and who is doing the research. " \
                    "The research locations and how the research is being conducted will be covered in the <i>Methods</i>" \
                    " and <i>Datasets</i> steps later on.</li></ul>"
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise'), page="description", restrict_admin=not has_permission(DefaultPermissions.ADVANCED_FIELDS, self.context, self.request)).bind(
            request=self.request)
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Next', 'Save', 'Previous'), use_ajax=False)

        # If this page was only called for saving and a rendered response isn't needed, return now.
        if self._handle_form():
            return

        return self._create_response(page_help=page_help)


    @view_config(route_name="information", permission=DefaultPermissions.VIEW_PROJECT)
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
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise'), page='information', restrict_admin=not has_permission(DefaultPermissions.ADVANCED_FIELDS, self.context, self.request)).bind(request=self.request, settings=self.config)
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Next', 'Save', 'Previous'), use_ajax=False)

        # If this page was only called for saving and a rendered response isn't needed, return now.
        if self._handle_form():
            return

        return self._create_response(page_help=page_help)

    def get_template_schemas(self):
        return self.session.query(MethodSchema).filter_by(template_schema=1).all()

    @view_config(route_name="methods", permission=DefaultPermissions.VIEW_PROJECT)
    def methods_view(self):
        page_help = "<p>Setup methods the project uses for collecting data (not individual datasets themselves as they will " \
                    "be setup in the next step).</p>" \
                    "<p>Each method sets up:</p>"\
                    "<ul><li>Name and description of the collection method.</li>"\
                    "<li>Ways of collecting data (data sources), these may require additional configuration on each dataset (datasets page).</li>" \
                    "<li>Type of data being collected which tells the system how data should be stored, displayed and searched (what fields there are, field types and associated information).</li>" \
                    "<li>Any additional information about this data collection methods - websites or attachments</li></ul>"
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise'), page="methods", restrict_admin=not has_permission(DefaultPermissions.ADVANCED_FIELDS, self.context, self.request)).bind(request=self.request)

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
        schema[METHODS_INDEX].children[0][DATA_SCHEMA_INDEX][METHOD_SCHEMA_PARENTS_INDEX].children[0].get_form = get_method_schema_preview
        schema[METHODS_INDEX].children[0][DATA_SCHEMA_INDEX].get_form = get_method_schema_preview
        #        assert False

        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Next', 'Save', 'Previous'), use_ajax=False)

        # If a new method was just added update it with data from the chosen template.
        # Because the same appstruct
        appstruct = self._get_post_appstruct()

        if len(appstruct) > 0:
            for new_method_data in appstruct['project:methods']:
                if not new_method_data['method:id'] and 'method:method_template_id' in new_method_data and new_method_data['method:method_template_id']:
                    template = self.session.query(MethodTemplate).filter_by(id=new_method_data['method:method_template_id']).first()
                    if template is None:
                        continue
                    template_method = self.session.query(Method).filter_by(id=template.template_id).first()
                    if template_method is None:
                        continue

                    new_method_dict = self._clone_model(template_method).dictify(schema[METHODS_INDEX].children[0])
#                    new_method_dict = new_method_dict['method']
                    del new_method_dict['method:id']
                    new_method_dict['method:project_id'] = new_method_data['method:project_id']
                    new_method_dict['method:method_template_id'] = new_method_data['method:method_template_id']
                    new_method_data.update(new_method_dict)

                # Else if this is a new method that wasn't actually added and is invalid (I believe the internals of deform automatically add min_len somehow)
                elif not new_method_data['method:project_id']:
                    appstruct['project:methods'].remove(new_method_data)
                    del new_method_data

        # If this page was only called for saving and a rendered response isn't needed, return now.
        if self._handle_form():
            return


        if self._get_model() is not None:
            for method in self._get_model().methods:
                if method.data_type is None:
                    method.data_type = MethodSchema()
                method.data_type.name = method.method_name

        return self._create_response(page_help=page_help)


    @view_config(route_name="datasets", permission=DefaultPermissions.VIEW_PROJECT)
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
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise'), page="datasets", restrict_admin=not has_permission(DefaultPermissions.ADVANCED_FIELDS, self.context, self.request)).bind(request=self.request, datasets=datasets)

        PREFIX_SEPARATOR = ":"
        DATASETS_INDEX = string.join([schema.name, Project.datasets.key], PREFIX_SEPARATOR)

        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Next', 'Save', 'Previous'), use_ajax=False)

        # If a new dataset was added through the wizard - Update the appstruct with that datasets' template's data
        appstruct = self._get_post_appstruct()
        if len(appstruct) > 0:
            for new_dataset_data in appstruct['project:datasets']:
                # If this is a newly created dataset
                if not new_dataset_data['dataset:id'] and 'dataset:method_id' in new_dataset_data and new_dataset_data['dataset:method_id']:
                    method = self.session.query(Method).filter_by(id=new_dataset_data['dataset:method_id']).first()
                    template_dataset = self.session.query(Dataset).join(MethodTemplate).filter(Dataset.id == MethodTemplate.dataset_id).\
                    filter(MethodTemplate.id == method.method_template_id).first()
                    if template_dataset is None:
                        continue

                    template_clone = self._clone_model(template_dataset)

                    # Pre-fill with first project point location
                    project_locations = self.session.query(Location).join(Metadata).filter(Metadata.id==Location.metadata_id).filter_by(project_id=self.project_id).all()
                    for location in project_locations:
                        if location.is_point():
                            location_clone = self._clone_model(location)
                            location_clone.metadata_id = None
                            template_clone.dataset_locations.append(location_clone)
                            break

                    # Copy all data from the template
                    new_dataset_dict = template_clone.dictify(schema[DATASETS_INDEX].children[0])

                    del new_dataset_dict['dataset:id']
                    new_dataset_dict['dataset:project_id'] = new_dataset_data['dataset:project_id']
                    new_dataset_dict['dataset:method_id'] = new_dataset_data['dataset:method_id']
                    new_dataset_data.update(new_dataset_dict)

                # Else if this is a new dataset that wasn't actually added and is invalid (I beleive the internals of deform automatically add min_len somehow)
                elif not new_dataset_data['dataset:id']:
                    appstruct['project:datasets'].remove(new_dataset_data)
                    del new_dataset_data


        # If this page was only called for saving and a rendered response isn't needed, return now.
        if self._handle_form():
            return

        if self.project_id is not None:
            methods = self.session.query(Method).filter_by(project_id=self.project_id).all()

            if len(methods) <= 0:
                self.request.session.flash('You must configure at least one method before adding dataset\'s', 'warning')
                return HTTPFound(self.request.route_url('methods', project_id=self.project_id))

            # Add method data to the field for information to create new templates.
            schema[DATASETS_INDEX].children[0].methods = methods
            schema[DATASETS_INDEX].children[0].widget.get_file_fields = get_file_fields

        # Pass the method names into the schema so it can be displayed
        appstruct = self._get_model_appstruct()
        method_names = {}
        if len(appstruct) > 0:
            for dataset_data in appstruct['project:datasets']:
                method_id = dataset_data["dataset:method_id"]

                # Dataset creation wizard automatically adds a dataset before the create button is pressed (something internal to deform when min_len > 0)
                if method_id is None or method_id == colander.null:
                    del dataset_data
                    break
                method_name = self.session.query(Method.method_name).filter_by(id=method_id).first()[0]
                method_names[method_id] = method_name
        schema[DATASETS_INDEX].children[0].method_names = method_names
        self.session.flush()

        return self._create_response(page_help=page_help)

    @view_config(route_name="submit", permission=DefaultPermissions.VIEW_PROJECT)
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
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise'), page="submit", restrict_admin=not has_permission(DefaultPermissions.ADVANCED_FIELDS, self.context, self.request)).bind(request=self.request)
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), use_ajax=False)

        # If this page was only called for saving and a rendered response isn't needed, return now.
        if self._handle_form():
            return

        # Get validation errors
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
                        sorted_errors.append((page, self.find_menu(page)['page_title'], []))

                    sorted_errors[-1][2].append((field, error))
                self.error = sorted_errors
        else:
            self.error = []

            # TODO: Validate the project and set it to self for all workflow steps to use.

        # Get all generated (and to-be-generated) metadata records
        # + Get a summary of all ingesters to be setup
        redbox_records = []
        ingesters = []
        datasets = []
        for dataset in self.project.datasets:
            portal_url = None
            if dataset.dam_id is not None:
                portal_url = "%s%s" % (self.config['ingesterapi.portal_url'], dataset.dam_id)
#            dataset_method = self.session.query(Method).filter_by(id=dataset.method_id).first()

            if dataset.publish_dataset:
                dataset_name = "dataset for %s method" % dataset.method.method_name
                if dataset.record_metadata is not None:
                    dataset_name = dataset.record_metadata.project_title

                metadata_record = self.session.query(Metadata).filter_by(dataset_id=dataset.id).first()
                redbox_uri = None
                if metadata_record is not None:
                    redbox_uri = "%s%s%s" % (self.config['redbox.url'], self.config['redbox.search_url'], metadata_record.redbox_identifier)

                datasets.append((dataset_name, portal_url, redbox_uri,
                                 self.request.route_url("view_record", project_id=self.project_id, dataset_id=dataset.id),
                                 self.request.route_url("delete_record", project_id=self.project_id, dataset_id=dataset.id),
                                 self.session.query(Metadata).filter_by(dataset_id=dataset.id).count() > 0, len(self.error) == 0))


        for i in range(len(schema.children)):
            if schema.children[i].name[-len('validation'):] == 'validation':
                schema.children[i].children[0].validation_errors = self.error
            if schema.children[i].name[-len('overview'):] == 'overview':
                schema.children[i].children[0].datasets = datasets
#            if schema.children[i].name[-len('ingesters'):] == 'ingesters':
#                schema.children[i].children[0].ingesters = ingesters

       # Configure the available buttons based of the proect state.
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
        self.form.buttons = buttons

        # Handle button presses and actual functionality.
        if SUBMIT_TEXT in self.request.POST and (self.project.state == ProjectStates.OPEN or self.project.state is None) and len(self.error) <= 0:
            self.project.state = ProjectStates.SUBMITTED and has_permission(DefaultPermissions.SUBMIT, self.context)

            # Only update the citation if it is empty
            if self.project.information.custom_citation is not True:
                self.redbox.pre_fill_citation(self.project.information)


            for dataset in self.project.datasets:
                # Only update the citation if it is empty
                if dataset.record_metadata is not None and dataset.record_metadata.custom_citation is False:
                    self.redbox.pre_fill_citation(dataset.record_metadata)

        if REOPEN_TEXT in self.request.POST and self.project.state == ProjectStates.SUBMITTED:
            self.project.state = ProjectStates.OPEN

        if DISABLE_TEXT in self.request.POST and self.project.state == ProjectStates.ACTIVE:
            self.project.state = ProjectStates.DISABLED
            # TODO: Disable in CC-DAM

        if DELETE_TEXT in self.request.POST and self.project.state == ProjectStates.DISABLED:
            # TODO: Delete
            pass

        if APPROVE_TEXT in self.request.POST and self.project.state == ProjectStates.SUBMITTED:
            # Make sure all dataset record have been created
            for dataset in self.project.datasets:
                if (dataset.record_metadata is None):
                    dataset.record_metadata = self.generate_dataset_record(dataset.id)
            self.session.flush()

#            try:
#                self.ingester_api.post(self.project)
#                self.ingester_api.close()
#                logger.info("Project has been added to ingesterplatform successfully: %s", self.project.id)
#            except Exception as e:
#                logger.exception("Project failed to add to ingesterplatform: %s", self.project.id)
#                self.request.session.flash("Failed to configure data storage and ingestion.", 'error')
#                self.request.session.flash("Error: %s" % e, 'error')
#                return self._create_response(page_help=page_help)

            try:
                self.redbox.insert_project(self.project_id)

            except Exception as e:
                logger.exception("Project failed to add to ReDBox: %s", self.project.id)
                self.request.session.flash("Sorry, the project failed to generate or add metadata records to ReDBox, please try agiain.", 'error')
                self.request.session.flash("Error: %s" % e, 'error')
                return self._create_response(page_help=page_help)


            # Change the state to active
            self.project.state = ProjectStates.ACTIVE
            logger.info("Project has been approved successfully: %s", self.project.id)


        buttons=()
        if (self.project.state == ProjectStates.OPEN or self.project.state is None) and len(self.error) <= 0 and\
                has_permission(DefaultPermissions.SUBMIT, self.context, self.request):
            buttons += (Button(SUBMIT_TEXT),)
        elif self.project.state == ProjectStates.SUBMITTED:
            if has_permission(DefaultPermissions.REOPEN, self.context, self.request):
                buttons += (Button(REOPEN_TEXT),)
            if has_permission(DefaultPermissions.APPROVE, self.context, self.request):
                buttons += (Button(APPROVE_TEXT),)
        elif self.project.state == ProjectStates.ACTIVE and\
                has_permission(DefaultPermissions.DISABLE, self.context, self.request):
            buttons += (Button(DISABLE_TEXT),)
        elif self.project.state == ProjectStates.DISABLED and\
                has_permission(DefaultPermissions.DELETE, self.context, self.request):
            buttons += (Button(DELETE_TEXT),)
        self.form.buttons = buttons

        return self._create_response(page_help=page_help, readonly=False)



    @view_config(route_name="delete_record", permission=DefaultPermissions.DELETE)
    def delete_record_view(self):
        dataset_id = self.request.matchdict['dataset_id']

        record = self.session.query(Metadata).filter_by(dataset_id=dataset_id).first()
        if record is not None:
            self.session.delete(record)

        self.request.session.flash('Dataset record successfully deleted (will be recreated when needed).', 'success')

        target = 'submit'
        return HTTPFound(self.request.route_url(target, project_id=self.project_id))

#-----------------------Dataset Record View/Edit-----------------------------------
    @view_config(route_name="view_record", permission=DefaultPermissions.VIEW_PROJECT)
    @view_config(route_name="edit_record", permission=DefaultPermissions.EDIT_PROJECT)
    def edit_record_view(self):
        dataset_id = self.request.matchdict['dataset_id']

        page_help=""
        schema = convert_schema(SQLAlchemyMapping(Metadata, unknown='raise',), restrict_admin=not has_permission(DefaultPermissions.ADVANCED_FIELDS, self.context, self.request)).bind(request=self.request, settings=self.config)
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id, dataset_id=dataset_id), buttons=("Cancel", "Save & Close", "Save",), use_ajax=False)

        # If the form is being saved (there would be 1 item in controls if it is a fresh page with a project id set)
        if len(self.request.POST) > 1 and not 'Cancel' in self.request.POST:
            self.request.POST['metadata:dataset_id'] = dataset_id # Make sure the dataset id is correct.
        elif len(self.request.POST) == 0:
            model = self.session.query(Metadata).filter_by(dataset_id=dataset_id).first()
            if model is None:
                model = self.generate_dataset_record(dataset_id)
                self.session.add(model)
                self.session.flush() # Update the id field so it is stored in the form!

            self._model = model # Set the model to be rendered (this is needed to provide the default _render_form() with the created template data)

        if 'Cancel' not in self.request.POST:
            # Ignore the redirect result as this page is never called to save other form data (comes from a readonly page)
            self._handle_form()

        if 'Cancel' in self.request.POST or 'Save_&_Close' in self.request.POST:
            target = 'submit'
            return HTTPFound(self.request.route_url(target, project_id=self.project_id))

        return self._create_response(page_help=page_help)


    def generate_dataset_record(self, dataset_id):
        metadata_id = self.session.query(Metadata.id).filter_by(dataset_id=dataset_id).first()

        metadata_template = self.session.query(Metadata).join(Project).filter(Metadata.project_id == Project.id).join(Dataset).filter(Project.id==Dataset.project_id).filter(Dataset.id==dataset_id).first()

        template_clone = self._clone_model(metadata_template)
        template_clone.id = metadata_id     # It is valid for metadata_id to be None
        template_clone.project_id = None
        template_clone.dataset_id = dataset_id

        # TODO:  Finalise generation of dataset specific metadata

        dataset = self.session.query(Dataset).filter_by(id=dataset_id).first()
        height_text =  (", %sm above MSL") % dataset.dataset_locations[0].elevation if dataset.dataset_locations[0].elevation is not None else ""
        template_clone.project_title = "%s at %s (%s, %s%s) collected by %s" % \
                               (template_clone.project_title, dataset.dataset_locations[0].name, dataset.dataset_locations[0].get_latitude(),
                                dataset.dataset_locations[0].get_longitude(), height_text, dataset.method.method_name)

        method_note = MetadataNote()
        method_note.note_desc = dataset.method.method_description
        template_clone.notes.append(method_note)

        return template_clone


    # --------------------WORKFLOW ACTION/SIDEBAR VIEWS-------------------------------------------
    @view_config(route_name="dataset_logs", permission=DefaultPermissions.VIEW_PROJECT)
    def dataset_logs_view(self):
        dataset_id = int(self.request.matchdict['dataset_id'])
        logs = self.ingester_api.getIngesterLogs(dataset_id)

        content = ''.join(["%s - %s - %s - %s - %s - %s.\n" % (log['id'], log['dataset_id'], log['timestamp'], log['class'], log['level'], log['message'].strip()) for log in logs])
        res = Response(content_type="text")
        res.body = content
        return res

    @view_config(route_name="logs", permission=DefaultPermissions.VIEW_PROJECT)
    def logs_view(self):
#        print "POST VARS" + str(self.request.POST) + " " + str(self.project_id)
        page_help="View ingester event logs for project datasets."
        schema = IngesterLogs()
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Refresh',), use_ajax=False)

        datasets = self.session.query(Dataset).filter_by(project_id=self.project_id).order_by(Dataset.record_metadata.project_title).all()

        for dataset in datasets:
            if dataset.dam_id is None:
                dataset.logs_error = ["Ingester hasn't been activated yet: %s" % dataset.title]
            else:
                try:
                    dataset.logs = self.ingester_api.getIngesterLogs(dataset.dam_id)
#                    print dataset.logs
#                    print range(len(dataset.logs)).reverse()
                    for i in reversed(range(len(dataset.logs))):
#                        print "Level filter: " + str(dataset.logs[i]['level']) + " : " + str(self.request.POST['level'])
                        if 'level' in self.request.POST and str(self.request.POST['level']) != "ALL" and str(dataset.logs[i].level) != str(self.request.POST['level']):
                            del dataset.logs[i]
                            continue
#                        print "data: %s" % dataset.logs[i]['timestamp'].partition('T')[0]
                        try:
                            log_date = dataset.logs[i].timestamp.date()
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

        # If this page was only called for saving and a rendered response isn't needed, return now.
        if self._handle_form():
            return

        return self._create_response(page_help=page_help)
#        if 'target' in self.request.POST and self.request.POST['target']:
#            target = self.request.POST['target']
#            return HTTPFound(self.request.route_url(target, project_id=self.project_id))
#
#        appstruct = {}
#        if self.request.POST.items() > 0:
#            try:
#                appstruct = self.form.validate(self.request.POST.items())
#                display = self.form.render(appstruct)
#            except ValidationFailure, e:
#                appstruct = e.cstruct
#                display = e.render()
#
#
#        return {"page_title": self.find_menu()['page_title'], "form": display, "form_only": False, 'messages': self._get_messages(), 'page_help': page_help}

    @view_config(route_name="duplicate", permission=DefaultPermissions.VIEW_PROJECT)
    def duplicate_view(self):
        self._handle_form()

        duplicate = self._clone_model(self.project)
        self.session.add(duplicate)
        self.session.flush()

        self.request.session.flash("Project successfully duplicated.", "success")

        if self.request.referer is not None:
            return HTTPFound(self.request.route_url(self.request.referer.split("/")[-1], project_id=duplicate.id))
        return HTTPFound(self.request.route_url("general", project_id=duplicate.id))


    @view_config(route_name="add_data", permission=DefaultPermissions.EDIT_DATA)
    def add_data_view(self):
        raise NotImplementedError("This page hasn't been implemented yet.")

        page_help=""
        schema = IngesterLogs()
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Refresh',), use_ajax=False)


        return self.handle_form(self.form, schema, page_help)

    @view_config(route_name="manage_data", permission=NO_PERMISSION_REQUIRED)
    def manage_data_view(self):

        page_help=""
        schema = ManageData()
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Refresh',), use_ajax=False)


        # If this page was only called for saving and a rendered response isn't needed, return now.
        if self._handle_form():
            return

        return self._create_response(page_help=page_help)

    @view_config(route_name="permissions", permission=DefaultPermissions.EDIT_SHARE_PERMISSIONS)
    def permissions_view(self):
        page_help=""

        users = json.dumps([{"label": user.display_name, "identifier": user.id} for user in self.session.query(User).all()])
        schema = Sharing()
        schema['shared_with'].users=users
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Save',), use_ajax=False)

        appstruct = self._get_post_appstruct()
        if len(appstruct) > 0:
            users_to_delete = [user_id for user_id, in self.session.query(distinct(ProjectPermissions.user_id)).filter_by(project_id=self.project_id).all()]

            for share in appstruct['shared_with']:
                user = self.session.query(User).filter_by(id=share['user_id']).first()
                share.pop("user_id")

                if user is None:
                    self.request.session.flash("You selected an invalid user, please use the autocomplete input and don't enter text manually.", "error")
                    continue

                if user.id in users_to_delete:
                    users_to_delete.remove(user.id)

                has_permission = False
                for field_name, value in share.items():
                    permission = self.session.query(Permission).filter_by(name=field_name).first()

                    for i in range(len(user.project_permissions)):
                        if user.project_permissions[i].project_id == long(self.project_id) and user.project_permissions[i].permission_id == permission.id:  # If the user already has this permission
                            if value == 'false' or value is False:
                                del user.project_permissions[i]

                            has_permission = True
                            break

                    if not has_permission and value is True:
                        user.project_permissions.append(ProjectPermissions(self.project_id, permission.id, user.id))

            for user_id in users_to_delete:
                del_permissions = self.session.query(ProjectPermissions).filter_by(project_id=self.project_id).filter_by(user_id=user_id).all()
                self.session.query(ProjectPermissions).filter_by(project_id=self.project_id).filter_by(user_id=user_id).delete()

            self.session.flush()

        # Create the initial form data from the current state
        appstruct = {'shared_with': []}
        last_user_id = -1
        current_user = None
        project_permissions = self.session.query(ProjectPermissions).filter_by(project_id=self.project_id).order_by(ProjectPermissions.user_id).all()
        for project_permission in project_permissions:
            if project_permission.user_id != last_user_id:
                last_user_id = project_permission.user_id
                current_user = {}
                appstruct['shared_with'].append(current_user)
                current_user['user_id'] = project_permission.user_id

            current_user[project_permission.permission.name] = 'true'

        # Directly set the model appstruct by-passing the usual workflow appstruct generation (because this view isn't directly mapped to an ColanderAlchemy model)
        self._model_appstruct = appstruct

        # Create the response and display the form
        return self._create_response()

    # --------------------WORKFLOW EXCEPTION VIEWS-------------------------------------------
    @view_config(context=Exception, route_name="workflow_exception", permission=NO_PERMISSION_REQUIRED)
    def exception_view(self):
        logger.exception("An exception occurred in global exception view: %s", self.context)
        if hasattr(self, self.request.matched_route.name + "_view"):
#            try:
                self.request.session.flash('Sorry, please try again - there was an exception: ' + cgi.escape(str(self.context)), 'error')
#                self.request.POST.clear()
#                response = getattr(self, str(self.request.matched_route.name) + "_view")()
                return HTTPFound(self.request.route_url(self.request.matched_route.name))
#                return response
#            except Exception:
#                logger.exception("Exception occurred while trying to display the view without variables: %s", Exception)
#                messages = {
#                    'error_messages': ['Sorry, we are currently experiencing difficulties: ' % self.context],
#                    'success_messages': [],
#                    'warning_messages': []
#                }
#                return {"page_title": self.find_menu()['page_title'], "form": '', "messages": messages, "form_only": False}
        else:
            try:
                messages = {
                    'error_messages': ['Sorry, we are currently experiencing difficulties: ' % self.context],
                    'success_messages': [],
                    'warning_messages': []
                }
                return {"page_title": self.find_menu()['page_title'], "form": 'This address is not valid, please don\'t directly edit the address bar: ' + cgi.escape(str(self.context)), "form_only": False, "messages": messages}
            except:
                self.request.session.flash('There is no page at the requested address, please don\'t edit the address bar directly.', 'error')
                if self.request.matchdict and self.request.matchdict['route'] and (self.request.matchdict['route'].split("/")[0]).isnumeric():
                    project_id = int(self.request.matchdict['route'].split("/")[0])
#                    print 'isnumeric: ' + str(project_id)
                    return HTTPFound(self.request.route_url('general', project_id=project_id))
                else:
                    return HTTPFound(self.request.route_url('create'))


#            return {"page_title": self.context, "form": 'This address is not valid, please don\'t directly edit the address bar: ' + str(self.context), "form_only": False}

    #    @view_config(context=sqlalchemy.orm.exc.SQLAlchemyError, renderer="../templates/exception.pt")
    @view_config(context=sqlalchemy.exc.SQLAlchemyError, renderer="../templates/exception.pt", permission=NO_PERMISSION_REQUIRED)
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
