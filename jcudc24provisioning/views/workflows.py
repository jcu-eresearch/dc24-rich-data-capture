"""
Provides all project related views, this includes project configuration as well as maintainence and searching models
(eg. anything to do with data ingestion and metadata).
"""

import cgi
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, date
from email.mime.text import MIMEText
import json
import logging
from mhlib import isnumeric
from operator import not_, itemgetter, or_, and_
import smtplib
from string import split
import string
import inspect
from sqlalchemy import distinct
import jcudc24ingesterapi
from jcudc24ingesterapi.search import DataEntrySearchCriteria, DataEntryMetadataSearchCriteria, DatasetMetadataSearchCriteria
from beaker.cache import cache_region
from jcudc24ingesterapi.schemas.metadata_schemas import DataEntryMetadataSchema, DatasetMetadataSchema
from jcudc24ingesterapi.models.metadata import MetadataEntry, DataEntryMetadataEntry, DatasetMetadataEntry
from jcudc24ingesterapi.ingester_platform_api import Marshaller
from jcudc24ingesterapi.models.data_entry import DataEntry, FileObject
from jcudc24provisioning.models.file_upload import ProvisioningFileUploadWidget
from jcudc24provisioning.resources import enmasse_forms, open_layers, open_layers_js
from js.jquery import jquery
from js.jqueryui import jqueryui
from js.jqueryui import ui_lightness
from js.jquery_form import jquery_form
import js.deform
from sqlalchemy import desc, asc
from pyramid.httpexceptions import HTTPForbidden
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

from jcudc24provisioning.controllers.authentication import DefaultPermissions
from jcudc24provisioning.controllers.method_schema_scripts import get_method_schema_preview, DataTypeSchema, DataTypeModel
from pyramid.security import authenticated_userid, NO_PERMISSION_REQUIRED, has_permission, ACLAllowed
import sqlalchemy
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.util import object_mapper
import colander
from jcudc24provisioning.controllers.redbox_mint import ReDBoxWrapper
import deform
from deform.exception import ValidationFailure
from deform.form import Form, Button
from sqlalchemy.orm import RelationshipProperty
from jcudc24ingesterapi.authentication import CredentialsAuthentication
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound, HTTPClientError
from pyramid.response import Response
from pyramid.view import view_config, view_defaults
from colanderalchemy.types import SQLAlchemyMapping
from jcudc24provisioning.views.views import Layouts
from pyramid.renderers import get_renderer
from jcudc24provisioning.models.project import Metadata, UntouchedPages, IngesterLogs, Location, \
    ProjectTemplate,method_template, Project, project_validator, ProjectStates, Sharing, CreatePage, MetadataNote, \
    Method, Party, Dataset, MethodSchema, create_project_validator, MethodTemplate, ManageData, ProjectNote, DataFiltering, DataFilteringWrapper, Keyword, TransitionNote, UserNotificationConfig, ProjectNotificationConfig, NotificationConfig, Notification, dataset_validator, metadata_validator, DatasetDataSource
from jcudc24provisioning.controllers.ca_schema_scripts import convert_schema, fix_schema_field_name
from jcudc24provisioning.controllers.ingesterapi_wrapper import IngesterAPIWrapper
from jcudc24provisioning.views.ajax_mint_lookup import MintLookup
from jcudc24provisioning.models.website import User, ProjectPermissions, Permission, PageLock


__author__ = 'Casey Bajema'

logger = logging.getLogger(__name__)

# Pyramid seems to have no way to dynamically find a views permission, so we need to manually re-add it here...
# Configures all menu items in the project workflow/configurations
WORKFLOW_STEPS = [
        {'href': 'create', 'title': 'Create', 'page_title': 'Create a New Project', 'hidden': True, 'tooltip': '', 'view_permission': DefaultPermissions.CREATE_PROJECT},
        {'href': 'general', 'title': 'Details', 'page_title': 'General Details', 'tooltip': 'Title, grants, people and collaborators', 'view_permission': DefaultPermissions.VIEW_PUBLIC, 'display_leave_confirmation': True},
        {'href': 'description', 'title': 'Description', 'page_title': 'Description', 'tooltip': 'Project descriptions used for publishing records', 'view_permission': DefaultPermissions.VIEW_PUBLIC, 'display_leave_confirmation': True},
        {'href': 'information', 'title': 'Information', 'page_title': 'Associated Information', 'tooltip': 'Collects metadata for publishing records', 'view_permission': DefaultPermissions.VIEW_PUBLIC, 'display_leave_confirmation': True},
        {'href': 'methods', 'title': 'Methods', 'page_title': 'Data Collection Methods', 'tooltip': 'Ways of collecting data', 'view_permission': DefaultPermissions.VIEW_PUBLIC, 'display_leave_confirmation': True},
        {'href': 'datasets', 'title': 'Datasets', 'page_title': 'Datasets (Collections of Data)', 'tooltip': 'Configure each individual data collection location', 'display_leave_confirmation': True},
        {'href': 'submit', 'title': 'Submit', 'page_title': 'Submit & Approval', 'tooltip': 'Overview, errors and project submission for administrator approval', 'view_permission': DefaultPermissions.VIEW_PROJECT},
        {'href': 'template', 'title': 'Template', 'page_title': 'Template Details', 'hidden': True, 'tooltip': 'Edit template specific details such as category', 'view_permission': DefaultPermissions.ADMINISTRATOR, 'display_leave_confirmation': True},
]

# Configures all contextual options in the project side menu.
WORKFLOW_ACTIONS = [
        {'href': 'general', 'title': 'Project Settings', 'page_title': 'General Details', 'tooltip': 'Project settings used to create this project', 'view_permission': DefaultPermissions.VIEW_PUBLIC, 'display_leave_confirmation': True},
        {'href': 'search', 'title': 'Browse Datasets', 'page_title': 'Browse Datasets', 'hidden_states': [ProjectStates.OPEN, ProjectStates.SUBMITTED], 'tooltip': 'Allows viewing, editing or adding of data and ingester configurations', 'view_permission': DefaultPermissions.VIEW_DATA, 'display_leave_confirmation': False},
        {'href': 'data_calibration', 'title': 'QA Data', 'page_title': 'Quality Assurance & Calibration', 'hidden_states': [ProjectStates.OPEN, ProjectStates.SUBMITTED], 'tooltip': 'Add/edit quality assurance & calibration data', 'visible_pages': ['data']},
        {'href': 'dataset', 'title': 'Add Dataset', 'page_title': 'Dataset Ingester', 'tooltip': 'Edit dataset ingester settings', 'hidden_states': [ProjectStates.OPEN, ProjectStates.SUBMITTED], 'view_permission': DefaultPermissions.EDIT_INGESTERS, 'display_leave_confirmation': True},
        {'href': 'search', 'title': 'Browse Data', 'page_title': 'Browse Data', 'hidden_states': [ProjectStates.OPEN, ProjectStates.SUBMITTED], 'tooltip': 'Data (Add, edit or view data)', 'visible_pages': ['dataset']},
        {'href': 'data', 'title': 'Add Data', 'page_title': 'Data (Add, edit or view data)', 'hidden_states': [ProjectStates.OPEN, ProjectStates.SUBMITTED], 'tooltip': 'Data (Add, edit or view data)', 'visible_pages': ['dataset']},
        {'href': 'dataset_calibration', 'title': 'Dataset Notes', 'page_title': 'Dataset Calibrations & Changes', 'hidden_states': [ProjectStates.OPEN, ProjectStates.SUBMITTED], 'tooltip': 'Record dataset changes and calibrations', 'visible_pages': ['dataset']},
        {'href': 'logs', 'title': 'View Logs', 'page_title': 'Ingester Event Logs', 'hidden_states': [ProjectStates.OPEN, ProjectStates.SUBMITTED], 'tooltip': 'Event logs received from the data ingester', 'view_permission': DefaultPermissions.VIEW_DATA, 'display_leave_confirmation': False},# 'visible_pages': ['general', 'description', 'information', 'methods', 'datasets', 'submit']},
        {'href': 'dataset_log', 'title': 'View Dataset Log', 'page_title': 'Ingester Event Log', 'hidden_states': [ProjectStates.OPEN, ProjectStates.SUBMITTED], 'tooltip': 'Event logs received from the data ingester', 'view_permission': DefaultPermissions.VIEW_DATA, 'display_leave_confirmation': False, 'visible_pages': ['dataset']},
        {'href': 'permissions', 'title': 'Sharing', 'page_title': 'Sharing & Permissions', 'tooltip': 'Change who can access and edit this project', 'view_permission': DefaultPermissions.EDIT_SHARE_PERMISSIONS}, # 'visible_pages': ['general', 'description', 'information', 'methods', 'datasets', 'submit']},
        {'href': 'notifications', 'title': 'Email Notifications', 'page_title': 'Email Notifications', 'tooltip': 'Configure what project changes you will get notified by email.', 'view_permission': DefaultPermissions.EDIT_SHARE_PERMISSIONS},# 'visible_pages': ['general', 'description', 'information', 'methods', 'datasets', 'submit']},
        {'href': 'duplicate', 'title': 'Duplicate Project', 'page_title': 'Duplicate Project', 'tooltip': 'Create a new project using this project as a template', 'view_permission': DefaultPermissions.CREATE_PROJECT}, # 'visible_pages': ['general', 'description', 'information', 'methods', 'datasets', 'submit']},
        {'href': 'create_template', 'title': 'Make into Template', 'page_title': 'Create Project Template', 'tooltip': 'Suggest to the administrators that this project should be a template', 'hidden': True, 'view_permission': DefaultPermissions.ADMINISTRATOR, 'display_leave_confirmation': True},
        {'href': 'dataset_record', 'title': 'Generated Dataset Record', 'page_title': 'Generated Dataset Record', 'hidden': True, 'tooltip': 'Edit datasets generated metadata record', 'view_permission': DefaultPermissions.EDIT_PROJECT, 'display_leave_confirmation': True},
        {'href': 'delete_record', 'title': 'Generated Dataset Record', 'page_title': 'Generated Dataset Record', 'hidden': True, 'tooltip': 'Delete datasets generated metadata record', 'view_permission': DefaultPermissions.EDIT_PROJECT},
    ]

# Not used currently - this is for if AJAX is enabled
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

@view_defaults(renderer="../templates/workflow_form.pt", permission=DefaultPermissions.ADMINISTRATOR)
class Workflows(Layouts):
    """
    This class provides all project related views and helper functions used by them.
    """
    def __init__(self, context, request):
#        self.request = request
#        self.context = context
        super(Workflows, self).__init__(context, request)
        enmasse_forms.need()

        self.project_id = None
        if self.request.matchdict and 'project_id' in self.request.matchdict:
            self.project_id = self.request.matchdict['project_id']

        # If the user submits a form
        if 'project:id' in self.request.POST and self.request.POST['project:id'] != self.project_id:
            self.request.POST['project:id'] = self.project_id


    @property
    def readonly(self):
        """
        Abstract functionality for determining if a form should be readonly so that it is reusable.

        Most forms are readonly if:
        - Project has been submitted and the user doen't have the ADMINISTRATOR permission.
        - Project has been submitted and approved.
        - User doesn't have edit permissions.
        """
        if '_readonly' not in locals():
            if self.project is None:
                return True

            is_closed = self.project.state == ProjectStates.DISABLED \
                    or self.project.state == ProjectStates.ACTIVE
            has_edit_permission = has_permission(DefaultPermissions.EDIT_PROJECT, self.context, self.request).boolval
            requires_admin = self.project.state == ProjectStates.SUBMITTED
            has_admin = has_permission(DefaultPermissions.ADMINISTRATOR, self.context, self.request).boolval
            can_edit = not is_closed and (has_admin or (not requires_admin and has_edit_permission))
            self._readonly = not can_edit
        return self._readonly

    @property
    def title(self):
        """
        All pages need to get their page title from the WORKFLOW_STEPS and WORKFLOW_ACTIONS arrays, this property
        abstracts that functionality to be reusable.
        """
        if '_title' not in locals():
            self._title = self.find_menu()['page_title']
        return self._title

    @property
    def project(self):
        """
        All project views are associated with a project - this attribute is a simple and efficient way of getting the
        current project when needed.
        """
        if '_project' not in locals():
            self._project = self.session.query(Project).filter_by(id=self.project_id).first()
            if self._project is None:
                raise HTTPClientError("You are trying to access a project that doesn't exist.  Either you have edited the address bar directly or the project no longer exists.")
#                self.request.session.flash("The requested project doesn't exist.  Either you have edited the address bar directly or the project you are requesting no longer exists.")
        return self._project

    def find_errors(self, error, page=None):
        """
        Get all Deform validation errors for the project as an array including the page, element title and error message.

        This is used by the project validation on the submit page.
        """
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
    def ingesterapi_auth(self):
        """
        Get an authentication object for opening communications with the ingesterapi.
        """
        if '_auth' not in locals():
            self._auth = CredentialsAuthentication(self.config["ingesterapi.username"], self.config["ingesterapi.password"])
            auth = self._auth
        return self._auth

    @property
    def ingester_api(self):
        """
        Open and return a connection with the ingester platform as an IngesterAPIWrapper instance.
        """
        if '_ingester_api' not in locals():
            self._ingester_api = IngesterAPIWrapper(self.config["ingesterapi.url"], self.ingesterapi_auth)
            api = self._ingester_api
        return self._ingester_api

    @property
    def redbox(self):
        """
        Initialise and return a ReDBox representation as a ReDBoxWrapper instance.

        All configurations are read from the development.ini/production.ini configuration file.
        """
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
            search_url = self.config['redbox.search_url']

            data_portal = "https://research.jcu.edu.au/enmasse/"

            self._redbox = ReDBoxWrapper(url=alert_url, search_url=search_url, data_portal=data_portal, identifier_pattern=identifier_pattern, ssh_host=host, ssh_port=port, tmp_dir=tmp_dir, harvest_dir=harvest_dir,
                ssh_username=username, rsa_private_key=private_key, ssh_password=password)

        return self._redbox

    @property
    def page(self):
        """
        Provide a function for the template to look up the dictionary from the WORKFLOW_STEPS/WORKFLOW_ACTIONS that
        represents the current workflow step/page/menu.
        """
        if '_page' not in locals():
            self._page = None
            for menu in WORKFLOW_STEPS + WORKFLOW_ACTIONS:
                if self.request.matched_route.name == menu['href']:
                    self._page = menu
                    break
        return self._page

    @property
    def next(self):
        """
        Provide a function for the template to look up the dictionary from the WORKFLOW_STEPS/WORKFLOW_ACTIONS that
        represents the next workflow step/page/menu.
        """
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
        """
        Provide a function for the template to look up the dictionary from the WORKFLOW_STEPS/WORKFLOW_ACTIONS that
        represents the previous workflow step/page/menu.
        """
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
        """
        Simple getter that reads the schema from the form set for this page.  This is used by the helper functions.
        """
        if self.form is None:
            return None
        return self.form.schema

    @property
    def model_type(self):
        """
        Read the model class from the set form.  This is a simple helper function that abstracts functionality that may
        potentially change to one location.
        """
        if hasattr(self, "_model_type"):
            return self._model_type

        if not hasattr(self, 'form') or not hasattr(self.form.schema, '_reg'):
            return None

        return self.form.schema._reg.cls


    @property
    def model_id(self):
        """
        Read the model id from the project property or the POST variables depending on the model type.
        """
        if '_model_id' not in locals() and not hasattr(self, '_model_id'):
            if self.model_type is None:
                self._model_id = None
            elif self.model_type == Project:
                self._model_id = self.project_id
            elif self.model_type.__tablename__.lower() + '_id' in self.request.matchdict:
                self._model_id = self.request.matchdict[self.model_type.__name__.lower() + '_id']
            else:
                self._model_id = self.request.POST.get(self.model_type.__tablename__ + ":id", None)
        return self._model_id

# --------------------MENU TEMPLATE METHODS-------------------------------------------
    @reify
    def workflow_step(self):
        """
        Find all workflow/project configuration steps/menus that should be displayed for the current page.
        """
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
            if 'view_permission' in menu and not has_permission(menu['view_permission'], self.context,
                    self.request).boolval:
                hidden.append(menu)

        for menu in hidden:
            if menu in new_menu:
                new_menu.remove(menu)

        return new_menu

    @reify
    def workflow_action(self):
        """
        Find all contextual options/menu items that should be displayed for the current page.
        """
        new_menu = WORKFLOW_ACTIONS[:]
        url = split(self.request.url, "?")[0]
        hidden = []
        for menu in new_menu:
            menu['current'] = url.endswith(menu['href']) or self.page in WORKFLOW_STEPS and menu['href'] == 'general'

            # Hide menu items that shouldn't be displayed (sub-pages)
            if ('hidden' in menu and menu['hidden'] is True) or ('hidden_states' in menu and self.project is not None and self.project.state in menu['hidden_states']):
                hidden.append(menu)

            # Hide menu items that are only to be displayed on set pages.
            if 'visible_pages' in menu and not self.request.matched_route.name in menu['visible_pages']:
                hidden.append(menu)

            # Hide manu items that the user doesn't have permission to see
            if 'view_permission' in menu and not has_permission(menu['view_permission'], self.context,
                    self.request).boolval:
                hidden.append(menu)

        for menu in hidden:
            if menu in new_menu:
                new_menu.remove(menu)

        return new_menu

    @reify
    def is_hidden_workflow(self):
        """
        Find if the current page is hidden and should hide the workflow/project configuration menu.
        """
        url = split(self.request.url, "?")[0]

        for menu in WORKFLOW_STEPS + WORKFLOW_ACTIONS:
            if url.endswith(menu['href']) and 'hidden' in menu and menu['hidden'] is True:
                return True

        return False

    def find_menu(self, href=None):
        """
        Find and return the dictionary from the WORKFLOW_STEPS/WORKFLOW_ACTIONS that represents the current page.
        """

        if href is None:
            href = self.request.matched_route.name

        for menu in WORKFLOW_STEPS + WORKFLOW_ACTIONS:
            if menu['href'] == href:
                return menu#['page_title']

        raise ValueError("There is no page for this address: " + str(href))

    @reify
    def workflow_template(self):
        """
        Provides getter for the workflows template.
        """
        renderer = get_renderer("../templates/workflow_template.pt")
        return renderer.implementation().macros['layout']
# --------------------WORKFLOW STEP METHODS-------------------------------------------
#
#
#    def _save_form(self, appstruct=None, model_id=None, model_type=None):
#        """
#        Abstracts functionality of saving form pages that is reusable for all project pages.
#        - If the model doesn't have an ID it inserts a new row in the database.
#        - If the model does have an ID it updates the current database row.
#        - If the data returned results in no change (or is empty), nothing is saved.
#        """
#
#        if appstruct is None:
#            appstruct = self._get_post_appstruct()
#        if model_type is None:
#            model_type = self.model_type
#
#            if model_type is None:
#                return False
#
#        if model_id is None:
#            model_id = self.model_id
#            model_id_field_name = "%s:id" % model_type.__tablename__
#            if model_id is None and model_id_field_name in appstruct:
#                model_id = appstruct[model_id_field_name]
#
#         # In either of the below cases get the data as a dict and get the rendered form
##        if 'POST' != self.request.method or len(self.request.POST) == 0 or self.readonly or \
##                'model_id' not in self.request.POST or 'model_type' not in self.request.POST:
##            return
#
##        model_id = self.request.POST['model_id']
##        model_type = globals()[self.request.POST['model_type']]
#        changed = False
#
#        model = self.session.query(model_type).filter_by(id=model_id).first()
#
#        if model is None or not isinstance(model, model_type):
#            if model_id is None or model_id == colander.null:
#                model = model_type(appstruct=appstruct)
#                if model is not None:
#                    self.session.add(model)
#                    changed = True
#                    model.date_created = datetime.now().date()
#                    model.create_by = self.request.user.id
#                else:
#                    return
#            else:
#                raise ValueError("No project found for the given project id(" + str(model_id) + "), please do not directly edit the address bar.")
#
#        else:
#            # Update the model with all fields in the data
#            if model.update(appstruct):
#                self.session.merge(model)
#                changed = True
#
#        self._model = model
#
#        if changed:
#            model.date_modified = datetime.now().date()
#            model.last_modified_by = self.request.user.id
#
#        try:
#            self.session.flush()
#            return changed
##            self.request.session.flash("Project saved successfully.", "success")
#        except Exception as e:
#            logger.exception("SQLAlchemy exception while flushing after save: %s" % e)
#            self.request.session.flash("There was an error while saving the project, please try again.", "error")
#            self.request.session.flash("Error: %s" % e, "error")
#            self.session.rollback()
##       self.session.remove()

    def _touch_page(self):
        """
        Indicate that this page has been saved by the user, this means that when the page is loaded in the future it
        will be validated and show any errors.
        """
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
        """
        Check if a page has been saved before, if the page hasn't been saved yet - don't validate (eg. it is
        non-intuitive to display validation errors before the user has entered and saved data).
        """
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

#    def _reset_form(self, node=None):
#        if node == None:
#            node = self.form
#
#        if hasattr(node, 'cstruct') and node.cstruct is not None:
#            del node.cstruct
#        if hasattr(node, 'error') and node.error is not None:
#            del node.error
#
#        for child in node.children:
#            self._reset_form(child)

    def _render_model(self):
        """
        Abstract the functionality behind rendering Deform schemas to HTML, including touched/untouched based validation
        wich is used by the _create_response() helper method.
        """

        # Remove errors that occurred during normal processing (this is usually stuff like invalid ID's for newly added
        # models.)
        if hasattr(self.form, "error") and self.form.error is not None:
            self.form = self.form.clone()
            self._reset_form()

        if not self._is_page_touched():
            # Try to display the form without validating
            appstruct = self._get_model_appstruct(dates_as_string=False)
            display = self._render_unvalidated_mode(appstruct)
            if display is not None:
                return display

        appstruct = self._get_model_appstruct(dates_as_string=True)
        display = self._render_validated_model(appstruct)

        return display


    def _get_model(self):
        """
        Get the SQLAlchemy model for the current page, this would typically be a Project but may be dynamically set
        to any ColanderAlchemy model.
        """
        if not hasattr(self, '_model'):
            if self.model_type is None or self.model_id is None:
                self._model = None
            else:
                self._model = self.session.query(self.model_type).filter_by(id=self.model_id).first()
        return self._model

    def _get_model_appstruct(self, dates_as_string=None):
        """
        Helper method for getting the current pages model and converting it into a Deform compatible appstruct.
        """
        if dates_as_string is None:
            dates_as_string = self._is_page_touched()

        if not hasattr(self, '_model_appstruct'):
            if self._get_model() is not None:
                self._model_appstruct = self._get_model().dictify(self.form.schema, dates_as_string=dates_as_string)
            else:
                return {}

        return self._model_appstruct

    def _create_response(self, **kwargs):
        """
        Abstract the repetitive task of rendering schemas and attributes into the output HTML.

        This also provides 1 location to place default rendering options such as that page help should be hidden.

        :param kwargs: Optional arguments to pass to the rendered form, most arguments will be standard and just
        override the defaults.

        :return: Rendered HTML form ready for display.
        """

        display_leave_confirmation =  kwargs.pop("display_leave_confirmation", "display_leave_confirmation" in self.page and self.page["display_leave_confirmation"])

        # If this is a form (something that the user edits) - Check to see if other users are viewing/editing the page.
        if display_leave_confirmation:
            users_viewing_page = self.session.query(PageLock.user_id).filter_by(url=self.request.path).filter(PageLock.expire_date >= datetime.now(), PageLock.id != self.lock_id).all()
            for user_id in users_viewing_page:
                display_name = self.session.query(User.display_name).filter_by(id=user_id[0]).first()
                self.request.session.flash("%s is already viewing this page, take care not to overwrite each others updates." % display_name, "warning")


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
            "display_leave_confirmation": display_leave_confirmation,
            "lock_id": self.lock_id,
        }

        # Don't use a default directly in pop as it initialises the default even if not needed, this causes self.project
        # to be called which breaks any pages that it is valid for the project to not be in the database yet
        # (eg. create page).
        if response_dict['readonly'] is None:
            response_dict['readonly'] = self.readonly
        else:
            self._readonly = response_dict['readonly']

        # Lazy default initialisation as this has high overheads.
        if response_dict['form'] is None:
            response_dict['form'] = self._render_model()
        response_dict.update(kwargs)
        return response_dict

    def _check_project_page_permissions(self):
        has_view_permission = has_permission(DefaultPermissions.VIEW_PROJECT, self.context, self.request).boolval
        project_activated = not (self.project.state == ProjectStates.OPEN or self.project.state == ProjectStates.SUBMITTED)

        if not project_activated and not has_view_permission:
            raise HTTPForbidden("You don't have permission to view this page.")

    def _send_email_notifications(self, type, project=None, **kw):
        """
        Send email notifications to all users that are configured to receive them for the current project and
        notification type.

        :param type: Name of the configuration type (eg. NotificationsConfig.new_projects.key)
        Lparam project: Optionally pass in the project that this notification is for (this will usually be for creating
                        new projects, as self.project isn't setup correctly yet).
        :return: Nothing.
        """
        if project is None:
            project = self.project

        config_ids = [id_tuple[0] for id_tuple in self.session.query(NotificationConfig.id).filter(getattr(NotificationConfig, type)==True).all()]
        users = []
        if len(config_ids) > 0:
            user_notification_config_ids = [id_tuple[0] for id_tuple in self.session.query(ProjectNotificationConfig.user_notification_config_id).filter_by(project_id=project.id).filter(ProjectNotificationConfig.notification_config_id.in_(config_ids)).all()]
            if len(user_notification_config_ids) > 0:
                user_ids = [tuple_id[0] for tuple_id in self.session.query(UserNotificationConfig.user_id).filter(UserNotificationConfig.id.in_(user_notification_config_ids)).all()]
                if len(user_ids) > 0:
                    users = self.session.query(User).filter(User.id.in_(user_ids)).all()
        email_to = [user.email for user in users]
        variables = {"name": self.request.user.display_name, "title": project.information.project_title,
                     "project_id": project.id, "url": self.request.route_url("general", project_id=project.id)}
        variables.update(kw)
        for key, value in variables.items():
            if isinstance(value, basestring):
                if isinstance(value, unicode):
                    variables[key] = value.encode("latin-1")
                else:
                    variables[key] = unicode(value, "latin-1")


        if type == NotificationConfig.state_changes.key:
            email_subject="[%(transition)s] EnMaSSe Project State Changed" % variables
            email_message = "Hi EnMaSSe User,<br /><p><a href='%(url)s'>project_%(project_id)s: %(title)s</a> has "\
                            "transitioned to the %(transition)s state by %(name)s:</p><p style='padding-left: 10px;'>"\
                            "%(message)s</p>"\
                            "<br />Regards,<br/>EnMaSSe System" % variables

            # Add a record of the notification to the database
            notification = Notification(datetime.now(), type, ','.join(email_to), email_subject, email_message,
                    variables['transition'],
                    ','.join("%s=%s" % (key, value) for key, value in variables.items()))
            self.session.add(notification)

        elif type == NotificationConfig.permission_changes.key:
            email_subject="EnMaSSe Project Share Permissions Changed" % variables
            email_message = "Hi EnMaSSe User,<br />"\
                            "<p><a href='%(url)s'>project_%(project_id)s: %(title)s</a> permissions were changed by %(name)s:</p>"\
                            "<p style='padding-left: 10px;'>%(modified)s</p>" \
                            "<br />Regards,<br/>EnMaSSe System"
            email_message = email_message % variables

            # Add a record of the notification to the database
            notification = Notification(datetime.now(), type, ','.join(email_to), email_subject, email_message,
                variables['modified'],
                ','.join("%s=%s" % (key, value) for key, value in variables.items()))
            self.session.add(notification)

        elif type == NotificationConfig.ingester_changes.key:
            variables["url"] = self.request.route_url("dataset", project_id=project.id, dataset_id=kw['dataset_id'])
            email_subject="EnMaSSe Dataset Ingester Changed" % variables
            email_message = "Hi EnMaSSe User,<br />"\
                            "<p><a href='%(url)s'>project_%(project_id)s: %(title)s</a> ingester configurations were changed by %(name)s.</p>"\
                            "<br />Regards,"\
                            "<br/>EnMaSSe System" % variables

            # Add a record of the notification to the database
            notification = Notification(datetime.now(), type, ','.join(email_to), email_subject, email_message,
                "[%s] %s" % (variables['dataset_id'], variables['title']),
                ','.join("%s=%s" % (key, value) for key, value in variables.items()))
            self.session.add(notification)

        elif type == NotificationConfig.log_errors.key:
            pass # Not implemented yet.
        elif type == NotificationConfig.log_warnings.key:
            pass # Not implemeneted yet
        elif type == NotificationConfig.new_projects.key:
            # New projects is a special case where the default configurations are used instead of per project configurations.
            email_to = [user.email for user in self.session.query(User).join(UserNotificationConfig, NotificationConfig).filter(NotificationConfig.new_projects==True).all()]

            email_subject="New EnMaSSe Project Created" % variables
            email_message = "Hi EnMaSSe User,<br />"\
                            "<p><a href='%(url)s'>project_%(project_id)s</a>: A new project has been created by %(name)s</p>"\
                            "<br />Regards,<br/>EnMaSSe System"
            email_message = email_message % variables

            # Add a record of the notification to the database
            notification = Notification(datetime.now(), type, ','.join(email_to), email_subject, email_message,
                variables['project_id'],
                ','.join("%s=%s" % (key, value) for key, value in variables.items()))
            self.session.add(notification)
        elif type == NotificationConfig.new_datasets.key:
            # New projects is a special case where the default configurations are used instead of per project configurations.
            email_to = [user.email for user in self.session.query(User).join(UserNotificationConfig, NotificationConfig).filter(NotificationConfig.new_datasets==True).all()]

            email_subject="New EnMaSSe Dataset Created" % variables
            email_message = "Hi EnMaSSe User,<br />"\
                            "<p><a href='%(url)s'>project_%(project_id)s: %(title)s</a>: A new dataset <a href='%(dataset_url)s'>(dataset_%(dataset_id)s)</a> has been added to the project by %(name)s</p>"\
                            "<p style='padding-left: 10px;'>%(message)s</p>" +\
                            "<br />Regards,<br/>EnMaSSe System"
            email_message = email_message % variables

            # Add a record of the notification to the database
            notification = Notification(datetime.now(), type, ','.join(email_to), email_subject, email_message,
                variables['project_id'],
                ','.join(["%s=%s" % (key, value) for key, value in variables.items()]))
            self.session.add(notification)
        elif type == NotificationConfig.errors.key:
            # New projects is a special case where the default configurations are used instead of per project configurations.
            email_to = [user.email for user in self.session.query(User).join(UserNotificationConfig, NotificationConfig).filter(NotificationConfig.errors==True).all()]

            email_subject="Error Occurred in EnMaSSe Project" % variables
            email_message = "Hi EnMaSSe User,<br />"\
                            "<p><a href='%(url)s'>project_%(project_id)s</a>: There was an error in updaates by %(name)s:</p>"\
                            "<p>%(message)s</p>" \
                            "<br />Regards,<br/>EnMaSSe System"
            email_message = email_message % variables

            # Add a record of the notification to the database
            notification = Notification(datetime.now(), type, ','.join(email_to), email_subject, email_message,
                variables['project_id'],
                ','.join("%s=%s" % (key, value) for key, value in variables.items()))
            self.session.add(notification)

        if len(email_to) > 0:
            mailer = get_mailer(self.request)
            message = Message(subject=email_subject, recipients=email_to, html=email_message)
            mailer.send(message)


# --------------------WORKFLOW STEP VIEWS-------------------------------------------
    @view_config(route_name="create", permission=DefaultPermissions.CREATE_PROJECT)
    def create_view(self):
        """
        The New Project creation wizard that collects the minimum required information to create and pre-fill new
        projects.

        The creation wizard also fills general data such as who create the project and when it was created.

        :return: HTML rendering of the create page form.
        """

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

        schema = CreatePage(validator=create_project_validator).bind(request=self.request)
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

            new_project.created_by = self.request.user.id
            new_project.date_created = datetime.now()

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

            try:
                self.session.add(new_project)
                self.session.flush()
                self.request.session.flash('New project successfully created.', 'success')

                self._add_default_notification_configs(self.request.user.id, self.project_id)

                # Send notification emails
                self._send_email_notifications(NotificationConfig.new_projects.key, new_project)

            except Exception as e:
                logger.exception("SQLAlchemy exception while flushing after project creation: %s" % e)
                self.request.session.flash("There was an error while creating the project, please try again.", "error")
                self.request.session.flash("Error: %s" % e, "error")
                self.session.rollback()

            return HTTPFound(self.request.route_url('general', project_id=new_project.id))

        return self._create_response(page_help=page_help, page_help_hidden=False, form=self._render_post(readonly=False), readonly=False)

    @view_config(route_name="general", permission=DefaultPermissions.VIEW_PUBLIC)
    def general_view(self):
        """
        Displays the general details page.  This is a basic page that simply collects and displays data.

        :return: HTML rendering of the create page form.
        """

        self._check_project_page_permissions()

        page_help = ""
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise', ca_description=""), page='general', restrict_admin=not has_permission(DefaultPermissions.ADVANCED_FIELDS, self.context, self.request).boolval).bind(request=self.request)
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Next', 'Save', ), use_ajax=False, ajax_options=redirect_options)

        # If this page was only called for saving and a rendered response isn't needed, return now.
        if self._handle_form():
            return

#        self.project.information.to_xml()
#        create_json_config()

        return self._create_response(page_help=page_help)


    @view_config(route_name="description", permission=DefaultPermissions.VIEW_PUBLIC)
    def description_view(self):
        """
        Displays the description page which is a basic page that simply collects and displays data.

        :return: HTML rendering of the create page form.
        """

        # Prevent the unauthorised users from seeing projects that aren't submitted and approved.
        self._check_project_page_permissions()

        page_help = "Fully describe your project to encourage other researchers to reuse your data:"\
                    "<ul><li>The entered descriptions will be used for metadata record generation (ReDBox), " \
                    "provide detailed information that is relevant to the project as a whole.</li>"\
                    "<li>Focus on what is being researched, why it is being researched and who is doing the research. " \
                    "The research locations and how the research is being conducted will be covered in the <i>Methods</i>" \
                    " and <i>Datasets</i> steps later on.</li></ul>"
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise'), page="description", restrict_admin=not has_permission(DefaultPermissions.ADVANCED_FIELDS, self.context, self.request).boolval).bind(
            request=self.request)
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Next', 'Save', 'Previous'), use_ajax=False)

        # If this page was only called for saving and a rendered response isn't needed, return now.
        if self._handle_form():
            return

        return self._create_response(page_help=page_help)


    @view_config(route_name="information", permission=DefaultPermissions.VIEW_PUBLIC)
    def information_view(self):
        """
        Displays the information page which is a basic page that simply collects and displays data.

        :return: HTML rendering of the create page form.
        """

        # Prevent the unauthorised users from seeing projects that aren't submitted and approved.
        self._check_project_page_permissions()

        open_layers.need()
        open_layers_js.need()

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
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise'), page='information', restrict_admin=not has_permission(DefaultPermissions.ADVANCED_FIELDS, self.context, self.request).boolval).bind(request=self.request, settings=self.config)
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Next', 'Save', 'Previous'), use_ajax=False)

        # If this page was only called for saving and a rendered response isn't needed, return now.
        if self._handle_form():
            return

        return self._create_response(page_help=page_help)

    def get_template_schemas(self):
        """
        Helper function that is given to the standardised fields/parent schema's schema to allow it to lookup and
        display standardised fields.

        :return: Array of standardised fields (MethodSchema's that have the template field set).
        """
        return self.session.query(MethodSchema).filter_by(template_schema=1).all()

    @view_config(route_name="methods", permission=DefaultPermissions.VIEW_PUBLIC)
    def methods_view(self):
        """
        Displays the methods page which provides a decent amount of dynamic functionality including:
        - Method creation wizard that allows selection of a template.
        - Data configuration wizard (simple, dynamic, ColanderAlchemy schema generator).
        - Pre-filling of methods based on the selected template.

        :return: HTML rendering of the create page form.
        """

        # Prevent the unauthorised users from seeing projects that aren't submitted and approved.
        self._check_project_page_permissions()

        page_help = "<p>Setup methods the project uses for collecting data (not individual datasets themselves as they will " \
                    "be setup in the next step).</p>" \
                    "<p>Each method sets up:</p>"\
                    "<ul><li>Name and description of the collection method.</li>"\
                    "<li>Ways of collecting data (data sources), these may require additional configuration on each dataset (datasets page).</li>" \
                    "<li>Type of data being collected which tells the system how data should be stored, displayed and searched (what fields there are, field types and associated information).</li>" \
                    "<li>Any additional information about this data collection methods - websites or attachments</li></ul>"
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise'), page="methods", restrict_admin=not has_permission(DefaultPermissions.ADVANCED_FIELDS, self.context, self.request).boolval).bind(request=self.request)

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

        adding_new = False
        if len(appstruct) > 0:
            for new_method_data in appstruct['project:methods']:
                if not new_method_data['method:id']:
                    adding_new = True

                # Pre-fill the new method from the template.
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
        if self._handle_form(dont_touch=adding_new):
            return

        # Getting the appstruct requires validation of the form - once the form is validated it can't be rendered without validation... So re-create the form.
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Next', 'Save', 'Previous'), use_ajax=False)

        if self._get_model() is not None:
            for method in self._get_model().methods:
                if method.data_type is None:
                    method.data_type = MethodSchema()
                method.data_type.name = method.method_name

        return self._create_response(page_help=page_help)

    def _get_file_fields(self, data_entry_schema):
        """
        Helper method for recursively retrieving all fields in a schema of type file.

        :param data_entry_schema: SQLAlchemy object to find all custom and parent fields from.
        :return: An array of all fields of file type within the provided schema.
        """
        if data_entry_schema is None:
            return []

        fields = []

        for field in data_entry_schema.parents:
            fields.extend(self._get_file_fields(field))

        for field in data_entry_schema.custom_fields:
            if field.type == 'file':
                fields.append((field.id, field.name))

        return fields

    @view_config(route_name="datasets", permission=DefaultPermissions.VIEW_PUBLIC)
    def datasets_view(self):
        """
        Displays the datasets page which provides a decent amount of dynamic functionality including:
        - Dataset creation wizard that allows adding of multiple datasets for each configured method.
        - Dynamic data and schema customisations for advanced data source configuration.
        - Pre-filling of datasets based on the selected template (the dataset template is set by the selected method
          template).

        :return: HTML rendering of the create page form.
        """

        # Prevent the unauthorised users from seeing projects that aren't submitted and approved.
        self._check_project_page_permissions()

        open_layers.need()
        open_layers_js.need()

        page_help = "<p>Add individual datasets that your project will be collecting.  This is the when and where using " \
                    "the selected data collection method (what, why and how).</p><p><i>Such that an iButton sensor that " \
                    "is used to collect temperature at numerous sites would have been setup once within the Methods step" \
                    " and should be set-up in this step for each site it is used at.</i></p>"

        datasets = self.session.query(Dataset).filter_by(project_id=self.project_id).all()
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise'), page="datasets", restrict_admin=not has_permission(DefaultPermissions.ADVANCED_FIELDS, self.context, self.request).boolval).bind(request=self.request, datasets=datasets)

        PREFIX_SEPARATOR = ":"
        DATASETS_INDEX = string.join([schema.name, Project.datasets.key], PREFIX_SEPARATOR)
        schema[DATASETS_INDEX].children[0].request = self.request

        # Fix any changes made in edit_dataset_view
        schema[DATASETS_INDEX].children[0]['dataset:publish_dataset'].widget.readonly = False
        schema[DATASETS_INDEX].children[0]['dataset:publish_date'].widget = deform.widget.DateInputWidget(readonly=False)
        schema[DATASETS_INDEX].children[0]['dataset:dataset_locations'].widget.readonly = False
        schema[DATASETS_INDEX].children[0]['dataset:location_offset'].widget.readonly = False

        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Next', 'Save', 'Previous'), use_ajax=False)

        # If a new dataset was added through the wizard - Update the appstruct with that datasets' template's data
        adding_new = False
        appstruct = self._get_post_appstruct()
        if len(appstruct) > 0:
            for new_dataset_data in appstruct['project:datasets']:
                # If this is a newly created dataset
                if not new_dataset_data['dataset:id'] and 'dataset:method_id' in new_dataset_data and new_dataset_data['dataset:method_id']:
                    adding_new = True
                    method = self.session.query(Method).filter_by(id=new_dataset_data['dataset:method_id']).first()
                    template_dataset = self.session.query(Dataset).join(MethodTemplate).filter(Dataset.id == MethodTemplate.dataset_id).\
                            filter(MethodTemplate.id == method.method_template_id).first()
                    if template_dataset is None:
                        continue

                    template_clone = self._clone_model(template_dataset)

                    # Pre-fill with first project point location
                    if len(template_clone.dataset_locations) == 0:
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

                    # Pre-fill the publish date to today if it isn't already set.
                    if not new_dataset_dict['dataset:publish_date']:
                        new_dataset_dict['dataset:publish_date'] = datetime.now().date()

                    new_dataset_data.update(new_dataset_dict)

                # Else if this is a new dataset that wasn't actually added and is invalid (I beleive the internals of deform automatically add min_len somehow)
                elif not new_dataset_data['dataset:id']:
                    appstruct['project:datasets'].remove(new_dataset_data)
                    del new_dataset_data


        # If this page was only called for saving and a rendered response isn't needed, return now.
        if self._handle_form(dont_touch=adding_new):
            return

        if self.project_id is not None:
            methods = self.session.query(Method).filter_by(project_id=self.project_id).all()

            if len(methods) <= 0:
                self.request.session.flash('You must configure at least one method before adding dataset\'s', 'warning')
                return HTTPFound(self.request.route_url('methods', project_id=self.project_id))

            # Add method data to the field for information to create new templates.
            schema[DATASETS_INDEX].children[0].methods = methods
            schema[DATASETS_INDEX].children[0].widget.get_file_fields = self._get_file_fields

        # Pass the method names into the schema so it can be displayed
        appstruct = self._get_model_appstruct(dates_as_string=self._is_page_touched())
        method_names = {}
        if len(appstruct) > 0:
            for dataset_data in appstruct['project:datasets']:
                method_id = dataset_data["dataset:method_id"]

                # Dataset creation wizard automatically adds a dataset before the create button is pressed (something internal to deform when min_len > 0)
                if method_id is None or method_id == colander.null:
                    del dataset_data
                    break
                method_name = self.session.query(Method.method_name).filter_by(id=method_id).first()[0]
                method_names[str(method_id)] = method_name
        schema[DATASETS_INDEX].children[0].method_names = method_names
        self.session.flush()

        # Getting the appstruct requires validation of the form - once the form is validated it can't be rendered without validation... So re-create the form.
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Next', 'Save', 'Previous'), use_ajax=False)

        return self._create_response(page_help=page_help)

    @cache_region('daily')
    def _get_cached_datasets_overview_data(self, cache_unique_id):
        """
        Get cached results for the datasets overview, this works by passing in a unique ID for the caching as the first
        parameter.

        The dataset overview results are a tuple of state and URL infomration ready to be displayed in the template.

        :param cache_unique_id: An integer read from self.project.datasets_ready, this integer is incremented every time
                methods or datasets are saved.
        :return: Cached results
        """
        datasets = []
        for dataset in self.project.datasets:
            dataset_name = "dataset for %s method" % dataset.method.method_name
            portal_url = None
            view_record_url = self.request.route_url("dataset_record", project_id=self.project_id, dataset_id=dataset.id)
            reset_record_url = None
            no_errors = len(self.error) == 0
            record_created = dataset.record_metadata is not None
            redbox_url = None

            if dataset.record_metadata is not None:
                dataset_name = dataset.record_metadata.project_title

            if dataset.publish_dataset and self.project.state in (ProjectStates.OPEN, ProjectStates.SUBMITTED, None):
                reset_record_url = self.request.route_url("delete_record", project_id=self.project_id, dataset_id=dataset.id)

            if dataset.publish_dataset and self.project.state not in (ProjectStates.OPEN, ProjectStates.SUBMITTED, None):
                id = dataset.record_metadata is not None and dataset.record_metadata.id or None
                portal_url = self.request.route_url("record_data", metadata_id=id)
                redbox_url = dataset.record_metadata is not None and dataset.record_metadata.redbox_uri or None

            datasets.append((dataset_name, portal_url, redbox_url, view_record_url, reset_record_url, record_created,
                             no_errors))
        return datasets

    @view_config(route_name="submit", permission=DefaultPermissions.VIEW_PROJECT)
    def submit_view(self):
        """
        Displays the submit page which provides a decent amount of dynamic functionality including:
        - Validation and error display of all workflow pages.
        - Setting the project note user.
        - Providing an overview of all data ingesters and metadata records.
        - changing project states
        - Integration with the ingesterapi and ReDBox on project approval.

        :return: HTML rendering of the create page form.
        """

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
        schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise'), page="submit", restrict_admin=not has_permission(DefaultPermissions.ADVANCED_FIELDS, self.context, self.request).boolval).bind(request=self.request)
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), use_ajax=False)

        # Configure the available buttons based off the proect state.
        SUBMIT_TEXT = "Submit"
        REOPEN_TEXT = "Reopen"
        DISABLE_TEXT = "Disable"
        APPROVE_TEXT = "Approve"
        DELETE_TEXT = "Delete"

        # Set the default user id to the current user so any notes that are added are set correctly.
        PROJECT_NOTE_KEY = "%s:%s" % (schema.name, Project.project_notes.key)
        TRANSITION_NOTE_KEY = "%s:%s" % (schema.name, Project.transition_notes.key)
        PROJECT_NOTE_USER_KEY = "%s:%s" % (schema[PROJECT_NOTE_KEY].children[0].name, ProjectNote.user_id.key)
        PROJECT_NOTE_USER_KEY = "%s:%s" % (schema[PROJECT_NOTE_KEY].children[0].name, ProjectNote.user_id.key)
        user_id = self.request.user is not None and self.request.user.id or None
        schema[PROJECT_NOTE_KEY].children[0][PROJECT_NOTE_USER_KEY].default = user_id
        schema[PROJECT_NOTE_KEY].children[0].user_id = user_id

        def get_user_name(user_id):
            if user_id is None or user_id is colander.null:
                return None
            user_name = self.session.query(User.display_name).filter_by(id=user_id).first()
            return user_name is not None and user_name[0] or None
        schema[TRANSITION_NOTE_KEY].children[0].get_user_name = get_user_name
        schema[PROJECT_NOTE_KEY].children[0].get_user_name = get_user_name
        schema[TRANSITION_NOTE_KEY].can_edit = has_permission(DefaultPermissions.EDIT_PROJECT, self.context, self.request).boolval

        post = self.request.POST
        pressed_button = SUBMIT_TEXT in post and SUBMIT_TEXT or\
                         REOPEN_TEXT in post and REOPEN_TEXT or\
                         DISABLE_TEXT in post and DISABLE_TEXT or\
                         APPROVE_TEXT in post and APPROVE_TEXT or\
                         DELETE_TEXT in post and DELETE_TEXT or\
                         None

        if pressed_button is not None:
            transition_comment = post[pressed_button]

            appstruct = self._get_post_appstruct()

            for transition_note in appstruct[TRANSITION_NOTE_KEY]:
                if transition_note['%s:id' % TransitionNote.__tablename__] is colander.null:
                    # Save the transition note.
                    transition_note["%s:user_id" % TransitionNote.__tablename__] = user_id
                    transition_note["%s:transition" % TransitionNote.__tablename__] = pressed_button
                    transition_note["%s:comment" % TransitionNote.__tablename__] = transition_comment
                    transition_note["%s:date_create" % TransitionNote.__tablename__] = datetime.now().date()
                    transition_note["%s:project_id" % TransitionNote.__tablename__] = self.project_id

            # Send notification emails
            self._send_email_notifications(NotificationConfig.state_changes.key, message=transition_comment, transition=pressed_button)

        # If this page was only called for saving and a rendered response isn't needed, return now.
        if self._handle_form():
            return

        # Get validation errors
        if self.project is not None and (self.project.state == ProjectStates.OPEN or self.project.state == ProjectStates.SUBMITTED) and not self.project.validated:
            # Create full self.project schema and form (without filtering to a single page as usual)
            val_schema = convert_schema(SQLAlchemyMapping(Project, unknown='raise', ca_validator=project_validator, )).bind(request=self.request, settings=self.config)

            val_form = Form(val_schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Next', 'Save', 'Previous'), use_ajax=False)

            appstruct = self.project.dictify(val_schema)
            try:
                val_form.validate_pstruct(appstruct)
                self.error = []
                self.project.validated = True
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

        # Get all generated (and to-be-generated) metadata records
        # + Get a summary of all ingesters to be setup
        datasets = self._get_cached_datasets_overview_data("%s:%s" % (self.project_id, self.project.datasets_ready))


        for i in range(len(schema.children)):
            if schema.children[i].name[-len('validation'):] == 'validation':
                schema.children[i].children[0].validation_errors = self.error
            if schema.children[i].name[-len('overview'):] == 'overview':
                schema.children[i].children[0].datasets = datasets
#            if schema.children[i].name[-len('ingesters'):] == 'ingesters':
#                schema.children[i].children[0].ingesters = ingesters


        buttons=()
        if (self.project.state == ProjectStates.OPEN or self.project.state is None) and len(self.error) <= 0:
            buttons += (SUBMIT_TEXT,)
        elif self.project.state == ProjectStates.SUBMITTED:
            buttons += (REOPEN_TEXT, APPROVE_TEXT)
        elif self.project.state == ProjectStates.ACTIVE:
            buttons += (DISABLE_TEXT,)
        elif self.project.state == ProjectStates.DISABLED:
            buttons += (DELETE_TEXT,)
        buttons += (Button("Save Notes"),)
        self.form.buttons = buttons

        # Handle button presses and actual functionality.
        if SUBMIT_TEXT in self.request.POST and (self.project.state == ProjectStates.OPEN or self.project.state is None) and len(self.error) <= 0:
            self.project.state = ProjectStates.SUBMITTED and has_permission(DefaultPermissions.SUBMIT, self.context, self.request).boolval

            # Only update the citation if it is empty
            if self.project.information.custom_citation is not True:
                self.redbox.pre_fill_citation(self.project.information)


            for dataset in self.project.datasets:
                # Only update the citation if it is empty
                if dataset.record_metadata is not None and dataset.record_metadata.custom_citation is False:
                    self.redbox.pre_fill_citation(dataset.record_metadata)

        if REOPEN_TEXT in self.request.POST and self.project.state == ProjectStates.SUBMITTED\
                and has_permission(DefaultPermissions.REOPEN, self.context, self.request).boolval:
            self.project.state = ProjectStates.OPEN

            for dataset in self.project.datasets:
                if dataset.dam_id is not None:
                    self.ingester_api.enableDataset(dataset.dam_id)

        if DISABLE_TEXT in self.request.POST and self.project.state == ProjectStates.ACTIVE\
                and has_permission(DefaultPermissions.DISABLE, self.context, self.request).boolval:
            self.project.state = ProjectStates.DISABLED
            for dataset in self.project.datasets:
                if dataset.dam_id is not None:
                    self.ingester_api.disableDataset(dataset.dam_id)

        if DELETE_TEXT in self.request.POST and self.project.state == ProjectStates.DISABLED \
                and has_permission(DefaultPermissions.DELETE, self.context, self.request).boolval:
            schemas = []
            for dataset in self.project.datasets:
                if dataset.dam_id is not None:
                    schema = dataset.method.data_type
                    if schema not in schemas:
                        schemas.append(schema)

                    self.ingester_api.delete(dataset.dataset_locations[0])
                    self.ingester_api.delete(dataset)

                for schema in schemas:
                    self.ingester_api.delete(schema)

            self.session.delete(self.project)

        if APPROVE_TEXT in self.request.POST and self.project.state == ProjectStates.SUBMITTED\
                and has_permission(DefaultPermissions.APPROVE, self.context, self.request).boolval and len(self.error) <= 0:
            # Make sure all dataset record have been created
            for dataset in self.project.datasets:
                if (dataset.record_metadata is None):
                    dataset.record_metadata = self.generate_dataset_record(dataset.id)
            self.session.flush()

            try:
                self.ingester_api.post(self.project)
                self.ingester_api.close()
                logger.info("Project has been added to ingesterplatform successfully: %s", self.project.id)
            except Exception as e:
                logger.exception("Project failed to add to ingesterplatform - Project ID: %s", self.project.id)
                self.request.session.flash("Failed to configure data storage and ingestion.", 'error')
                self.request.session.flash("Error: %s" % e, 'error')
                self._send_email_notifications(NotificationConfig.errors.key, dataset.project,
                    message="Error creating data ingesters for <a href='%s'>project %s</a>: %s" % (
                        self.request.route_url("general", project_id=dataset.project_id),
                        self.project_id ,e))
                return self._create_response(page_help=page_help)

#            try:
#                self.redbox.insert_project(self.project_id)
#
#            except Exception as e:
#                logger.exception("Project failed to add to ReDBox: %s", self.project.id)
#                self.request.session.flash("Sorry, the project failed to generate or add metadata records to ReDBox, please try agiain.", 'error')
#                self.request.session.flash("Error: %s" % e, 'error')
#                self._send_email_notifications(NotificationConfig.errors.key,
#                    message="Error creating ReDBox records for project <a href='%s'>%s</a>: %s" % (
#                        self.request.route_url("general", project_id=self.project_id),
#                        self.project_id ,e))
#                return self._create_response(page_help=page_help)

            # Change the state to active
            self.project.state = ProjectStates.ACTIVE
            logger.info("Project has been approved successfully: %s", self.project.id)


        buttons=()
        if (self.project.state == ProjectStates.OPEN or self.project.state is None) and len(self.error) <= 0 and\
                has_permission(DefaultPermissions.SUBMIT, self.context, self.request).boolval:
            buttons += (Button(SUBMIT_TEXT),)
        elif self.project.state == ProjectStates.SUBMITTED:
            if has_permission(DefaultPermissions.REOPEN, self.context, self.request).boolval:
                buttons += (Button(REOPEN_TEXT),)
            if has_permission(DefaultPermissions.APPROVE, self.context, self.request).boolval:
                buttons += (Button(APPROVE_TEXT),)
        elif self.project.state == ProjectStates.ACTIVE and\
                has_permission(DefaultPermissions.DISABLE, self.context, self.request).boolval:
            buttons += (Button(DISABLE_TEXT),)
        elif self.project.state == ProjectStates.DISABLED and\
                has_permission(DefaultPermissions.DELETE, self.context, self.request).boolval:
            buttons += (Button(DELETE_TEXT),)
        buttons += (Button("Save Notes"),)
        self.form.buttons = buttons

        return self._create_response(page_help=page_help, readonly=False)



    @view_config(route_name="delete_record", permission=DefaultPermissions.DELETE)
    def delete_record_view(self):
        """
        Deletes the metadata record associated with the selected dataset.  This basically resets any changes so that
        the next view will re-create the default metadata record.

        :return: Redirect to the submit page
        """
        dataset_id = self.request.matchdict['dataset_id']

        record = self.session.query(Metadata).filter_by(dataset_id=dataset_id).first()
        if record is not None:
            self.session.delete(record)
            self.project.datasets_ready += 1

        self.request.session.flash('Dataset record successfully deleted (A new record will be created when needed).', 'success')

        target = 'submit'
        return HTTPFound(self.request.route_url(target, project_id=self.project_id))

#-----------------------Dataset Record View/Edit-----------------------------------
    @view_config(route_name="dataset_record", permission=DefaultPermissions.EDIT_PROJECT)
    def dataset_record_view(self):
        """
        Displays the generated metadata record for the selected dataset, this is basically the genral details,
        description and information models all on one form.

        :return: HTML rendering of the create page form.
        """

        open_layers.need()
        open_layers_js.need()

        dataset_id = self.request.matchdict['dataset_id']

        page_help=""
        schema = convert_schema(SQLAlchemyMapping(Metadata, unknown='raise', widget=deform.widget.MappingWidget(validator=metadata_validator)), restrict_admin=not has_permission(DefaultPermissions.ADVANCED_FIELDS, self.context, self.request).boolval).bind(request=self.request, settings=self.config)
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
        """
        Generate a dataset metadata record based of the project metadata, methods and datasets pages.

        :return: A ColanderAlchemy Metadata model of the newly created dataset metadata.
        """
        metadata_id = self.session.query(Metadata.id).filter_by(dataset_id=dataset_id).first()

        metadata_template = self.session.query(Metadata).join(Project).filter(Metadata.project_id == Project.id).join(Dataset).filter(Project.id==Dataset.project_id).filter(Dataset.id==dataset_id).first()

        template_clone = self._clone_model(metadata_template)
        template_clone.id = metadata_id     # It is valid for metadata_id to be None
        template_clone.project_id = None
        template_clone.dataset_id = dataset_id

        dataset = self.session.query(Dataset).filter_by(id=dataset_id).first()
        height_text =  (", %sm above MSL") % dataset.dataset_locations[0].elevation if dataset.dataset_locations[0].elevation is not None else ""
        template_clone.project_title = "%s at %s (%s, %s%s) collected by %s" % \
                               (template_clone.project_title, dataset.dataset_locations[0].name, dataset.dataset_locations[0].get_longitude(),
                                 dataset.dataset_locations[0].get_latitude(),height_text, dataset.method.method_name)

        method_note = MetadataNote()
        method_note.note_desc = dataset.method.method_description
        template_clone.notes.append(method_note)

        return template_clone


    # --------------------WORKFLOW ACTION/SIDEBAR VIEWS-------------------------------------------
    @view_config(route_name="dataset_log", permission=DefaultPermissions.VIEW_PROJECT)
    def dataset_log_view(self):
        """
        Retrieves all ingester platform events/logs for the selected dataset from the ingesterapi and displays them.

        :return: HTML rendering of the create page form.
        """

        dataset_id = self.request.matchdict['dataset_id']

        logs = self.ingester_api.getIngesterLogs(dataset_id)

        content = ''.join(["%s - %s - %s - %s - %s - %s.\n" % (log['id'], log['dataset_id'], log['timestamp'], log['class'], log['level'], log['message'].strip()) for log in logs])
        res = Response(content_type="text")
        res.body = content
        return res

    @view_config(route_name="logs", permission=DefaultPermissions.VIEW_PROJECT)
    def logs_view(self):
        """
        Retrieves all ingester platform events/logs for all dataset associated with the project from the ingesterapi
        and displays them with optional filtering.

        :return: HTML rendering of the create page form.
        """
#        print "POST VARS" + str(self.request.POST) + " " + str(self.project_id)
        page_help="View ingester event logs for project datasets."
        schema = IngesterLogs()
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Refresh',), use_ajax=False)

        datasets = self.session.query(Dataset).filter_by(project_id=self.project_id).all()

        # Create
        for dataset in datasets:
            if dataset.dam_id is None:
                dataset.logs_error = ["Ingester hasn't been activated yet"] #: %s" % dataset.id]
#            else:
#                for dataset in datasets:
#                    dataset.logs = [{"level": "info" ,
#                                     "message": "Logs are still loading, please wait.  Provide more specific filtering "
#                                     "or click on the individual dataset log link (right of the dataset name) for "
#                                     "quicker results.",
#                                     "timestamp": None}]

        schema.children[1].datasets = datasets
        schema.children[1].request = self.request

        level = "ALL"
        start_date = None
        end_date = None
        if 'level' in self.request.POST and str(self.request.POST['level']):
            level = self.request.POST['level']
        if 'start_date' in self.request.POST and self.request.POST['start_date']:
            start_date = self.request.POST['start_date']
        if 'end_date' in self.request.POST and self.request.POST['end_date']:
            end_date = self.request.POST['end_date']

        schema.children[1].filtering = (level, start_date, end_date)

#            try:
#                    dataset.logs = self.ingester_api.getIngesterLogs(dataset.dam_id)
##                    print dataset.logs
##                    print range(len(dataset.logs)).reverse()
#                    for i in reversed(range(len(dataset.logs))):
##                        print "Level filter: " + str(dataset.logs[i]['level']) + " : " + str(self.request.POST['level'])
#                        if 'level' in self.request.POST and str(self.request.POST['level']) != "ALL" and str(dataset.logs[i].level) != str(self.request.POST['level']):
#                            del dataset.logs[i]
#                            continue
##                        print "data: %s" % dataset.logs[i]['timestamp'].partition('T')[0]
#                        try:
#                            log_date = dataset.logs[i].timestamp.date()
#                        except Exception as e:
#                            logger.exception("Log date wasn't parsable: %s" % e)
#                            continue
#
#                        if 'start_date' in self.request.POST and self.request.POST['start_date']:
#                            start_date = datetime.strptime(self.request.POST['start_date'].partition('T')[0], '%Y-%m-%d').date()
#                            if log_date < start_date:
#                                del dataset.logs[i]
#                                continue
#
#                        if 'end_date' in self.request.POST and self.request.POST['end_date']:
#                            end_date = datetime.strptime(self.request.POST['end_date'].partition('T')[0], '%Y-%m-%d').date()
#                            if log_date > end_date:
#                                del dataset.logs[i]
#                                continue
#
#                except Exception as e:
#                    logger.exception("Exception getting logs: %s", e)
#                    dataset.logs_error = "Error occurred: %s" % e
#
#        schema.children[1].datasets = datasets


        # If this page was only called for saving and a rendered response isn't needed, return now.
        if self._handle_form():
            return

        return self._create_response(page_help=page_help, readonly=False)

    @view_config(route_name="duplicate", permission=DefaultPermissions.VIEW_PROJECT)
    def duplicate_view(self):
        """
        Contextual option that allows users to duplicate an existing project.

        :return: Redirect to the general page of the newly created/duplicated project.
        """
        self._handle_form()

        duplicate = self._clone_model(self.project)
        duplicate.state = ProjectStates.OPEN
        duplicate.date_created = datetime.now().date()
        duplicate.date_modified = datetime.now().date()
        duplicate.created_by = self.request.user.id
        duplicate.last_modified_by = None
        duplicate.template_only = False
        duplicate.transition_notes = []
        duplicate.notification_configs = []
        self.session.add(duplicate)
        self.session.flush()

        self.request.session.flash("Project successfully duplicated.", "success")

        if self.request.referer is not None:
            return HTTPFound(self.request.route_url(self.request.referer.split("/")[-1], project_id=duplicate.id))
        return HTTPFound(self.request.route_url("general", project_id=duplicate.id))

    def _get_ingester_dataset_changes(self, dataset):
        """
        Finds differences between the current dataset configuration in the ingester platform compared to the settings
        in the provisioning interface.

        The only valid changes are enabled and data_source so everything else is ignored.

        :param dataset: Provisioning interface dataset to find changes for.
        :return: Array of dict's that describe the changes.
        """
        if dataset.dam_id is None:
            return []

        changes = []
        ingester_dataset = self.ingester_api.getDataset(dataset.dam_id)
        marshaller = Marshaller()

        if ingester_dataset.enabled == dataset.disabled:
            changes.append({"field": Dataset.disabled.key, "ingester": not ingester_dataset.enabled, "provisioning": dataset.disabled})

        new_data_source = self.ingester_api._create_data_source(dataset)
        provisioning_datasource_dict = marshaller.obj_to_dict(marshaller.obj_to_dict(new_data_source))
        ingester_datasource_dict = marshaller.obj_to_dict(marshaller.obj_to_dict(ingester_dataset.data_source))
        if type(new_data_source) != type(ingester_dataset.data_source):
            changes.append({"field": "Datasource type changed", "ingester": ingester_datasource_dict,
                    "provisioning": provisioning_datasource_dict})
        else:
            for field in ingester_datasource_dict:
                if ingester_datasource_dict[field] != provisioning_datasource_dict[field]:
                    changes.append({"field": field, "ingester": ingester_datasource_dict[field], "provisioning": provisioning_datasource_dict[field]})

        return changes


    @view_config(route_name="dataset", permission=DefaultPermissions.VIEW_PROJECT)
    def dataset_view(self):
        """
        Hidden view for editing dataset ingester settings, this accessible through search.
        """
        readonly = False
        if self.project.state == ProjectStates.OPEN or self.project.state == ProjectStates.SUBMITTED:
            self.request.session.flash("Please use the datasets page in project configuration to update projects that haven't been submitted and approved.", "warning")
            readonly = True

        if not has_permission(DefaultPermissions.EDIT_INGESTERS, self.context, self.request).boolval:
            readonly = True

        open_layers.need()
        open_layers_js.need()

        dataset_id = self.request.matchdict['dataset_id']
        if len(dataset_id) == 0 or dataset_id[0] == 'None':
            dataset_id = None
        else:
            dataset_id = int(dataset_id[0])

        self._model_id = dataset_id
        self._model_type = Dataset
        dataset = self._get_model()

        is_approved = dataset is not None and dataset.dam_id is not None

        page_help=""

        schema = convert_schema(SQLAlchemyMapping(Dataset, unknown='raise'), page="datasets", restrict_admin=not has_permission(DefaultPermissions.ADVANCED_FIELDS, self.context, self.request).boolval).bind(request=self.request, datasets=self.project.datasets)

        schema['dataset:publish_dataset'].widget.readonly = readonly or is_approved
        schema['dataset:publish_date'].widget = deform.widget.DateInputWidget(readonly=readonly or is_approved)
        schema['dataset:dataset_locations'].widget.readonly = readonly or readonly or is_approved
        schema['dataset:location_offset'].widget.readonly = readonly or readonly or is_approved

        schema.methods = self.project.methods
        schema.validator = dataset_validator

        # Add calibration data for display.
        if dataset is not None and dataset.dam_id is not None:
            calibrations_data = []
            calibrations = self.ingester_api.search(DatasetMetadataSearchCriteria(dataset.dam_id), 0, 1000)
            if calibrations.count > 0:
                for calibration in calibrations.results:
                    calibrations_data.append({
                        "date": calibration["date"],
                        "changes": json.loads(calibration["changes"]),
                        })
            self.schema.calibrations = calibrations_data

        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id, dataset_id=dataset_id),
            buttons=("Save",), use_ajax=False)
        self.form.widget.template="edit_dataset_form"
        self.form.widget.readonly_template="readonly/edit_dataset_form"
        self.form.widget.get_file_fields = self._get_file_fields

        # If a new dataset was just added, set it's project before it gets added.
        appstruct = self._get_post_appstruct()
        if dataset is None and len(appstruct) > 0:
            appstruct["dataset:project_id"] = self.project_id
            appstruct["dataset:disabled"] = True

        # If this page was only called for saving and a rendered response isn't needed, return now.
        if self._handle_form():
            return

        # Get the updated model with the newly saved data.
        dataset = self._get_model()

        # If this is a new dataset that needs to be submitted/activated, show the submit/approve buttons.
        if dataset is not None and not is_approved:
            if has_permission(DefaultPermissions.ADMINISTRATOR, self.context, self.request) and dataset.submitted:
                self.form.buttons.append(Button("Approve"))
            elif not dataset.submitted:
                self.form.buttons.append(Button("Submit for Approval"))

        if hasattr(self, '_form_changed') and self._form_changed:
            # If a new dataset was just added, redirect to its edit page.
            if dataset_id is None:
                dataset_id = self._model.id
                new_url = self.request.route_url(self.request.matched_route.name, project_id=self.project_id,
                        dataset_id=dataset_id)
                return HTTPFound(new_url)
#            elif is_approved:
#                self._send_email_notifications(NotificationConfig.ingester_changes.key, dataset_id=dataset_id)

        # Otherwise, update/insert the ingester and metadata record + send notification emails that the dataset has changed.
        if 'Approve' in self.request.POST:
            try:
                # Check that the model validates (will throw an exception if it is invalid).
                self.form.validate_pstruct(self._get_model_appstruct(dates_as_string=True))

                # Activate the project (Export ReDBox record and setup the data ingester).
                # Make sure all dataset record have been created
                if (dataset.record_metadata is None):
                    dataset.record_metadata = self.generate_dataset_record(dataset.id)
                self.session.flush()

                success = True
                dataset_exported = False
                record_exported = False

                changes = self._get_ingester_dataset_changes(dataset)

                # Setup data ingestion to the ingester platform.
                if success:
                    try:
                        self.ingester_api.post(dataset)
                        self.ingester_api.close()
                        dataset_exported = True
                        logger.info("Dataset has been added to ingesterplatform successfully: %s", dataset.id)
                    except Exception as e:
                        success = False
                        logger.exception("Dataset failed to add to ingesterplatform - Dataset ID: %s", dataset.id)
                        self.request.session.flash("Failed to configure data storage and ingestion.", 'error')
                        self.request.session.flash("Error: %s" % e, 'error')
                        self._send_email_notifications(NotificationConfig.errors.key, dataset.project,
                            message="Error %s dataset <a href='%s'>%s</a>: %s" % (
                                dataset.dam_id is None and "inserting" or "updating",
                                self.request.route_url("dataset", project_id=dataset.project_id, dataset_id=dataset.id),
                                dataset.id ,e))

                # Export dataset metadata record to ReDBox only if this is a new dataset.
                if success and dataset.publish_dataset and dataset.record_metadata.date_added_to_redbox is None:
                    try:
                        self.redbox.insert_dataset(dataset.id)
                        record_exported = True
                    except Exception as e:
                        success = False
                        logger.exception("Dataset failed to add to ReDBox: %s", dataset.id)
                        self.request.session.flash("Dataset failed to generate or add metadata records to ReDBox.", 'error')
                        self.request.session.flash("Error: %s" % e, 'error')
                        self._send_email_notifications(NotificationConfig.errors.key, dataset.project,
                            message="Error creating ReDBox record for dataset <a href='%s'>%s</a>: %s" % (
                                self.request.route_url("dataset", project_id=dataset.project_id, dataset_id=dataset.id),
                                dataset.id ,e))

                if success:
                    self.request.session.flash("Dataset successfully approved.", "success")
                    if dataset_exported and record_exported:
                        self._send_email_notifications(NotificationConfig.new_datasets.key, dataset_id=dataset_id
                            , dataset_url=self.request.route_url(self.request.matched_route.name, project_id=self.project_id,
                                dataset_id=dataset_id), message="The dataset has been approved and is now active.")
                    else:
                        if len(changes) > 0:
                            # TODO: This only supports 1 type of dataset calibration.
                            calibration_schema = self.session.query(MethodSchema).filter_by(schema_type=DatasetMetadataSchema.__xmlrpc_class__).first()
                            calibration = DatasetMetadataEntry(dataset.dam_id, metadata_schema_id=int(calibration_schema.dam_id))
                            calibration["date"] = datetime.now()
                            calibration["changes"] = json.dumps(changes)
                            try:
                                self.ingester_api.post(calibration)
                            except Exception as e:
                                message = "Failed to add dataset calibration after saving changes."
                                logger.exception(message)
                                self.request.session.flash(message, "error")
                                self._send_email_notifications(NotificationConfig.errors.key, dataset.project,
                                    message=message)
                        self._send_email_notifications(NotificationConfig.ingester_changes.key, dataset_id=dataset_id,
                                changes=changes)


            except ValidationFailure as e:
                self.request.session.flash("You cannot approve the dataset while it has validation errors.", "error")

        elif 'Submit_for_Approval' in self.request.POST:
            try:
                # Check that the model validates (will throw an exception if it is invalid).
                self.form.validate_pstruct(self._get_model_appstruct(dates_as_string=True))

                dataset.submitted = True
                self._send_email_notifications(NotificationConfig.new_datasets.key, dataset_id=dataset_id
                    , dataset_url=self.request.route_url(self.request.matched_route.name, project_id=self.project_id,
                        dataset_id=dataset_id), message="The dataset requires administrator approval.")
            except ValidationFailure as e:
                self.request.session.flash("You cannot submit the dataset for approval while it has validation errors.", "error")

        if dataset is not None and dataset.dam_id is not None:
            changes = self._get_ingester_dataset_changes(dataset)
            if len(changes) > 0:
                self.request.session.flash("This dataset has un-exported changes, data is currently being ingested with "
                       "<a href='%s'>these settings</a>" % self.request.route_url(
                            "ingester_dataset", project_id=self.project_id, dataset_id=dataset.id), "warning")

        # Remove the appstruct created during submit/approval so the form renders correctly.
        if hasattr(self, '_model_appstruct'):
            delattr(self, '_model_appstruct')

#        self.model_type = Dataset
        return self._create_response(page_help=page_help, readonly= readonly or not
            has_permission(DefaultPermissions.EDIT_INGESTERS, self.context, self.request).boolval)

    @view_config(route_name="ingester_dataset", permission=DefaultPermissions.VIEW_PROJECT)
    def ingester_dataset_view(self):
        page_help=""

        dataset_id = self.request.matchdict['dataset_id']
        self.request.session.flash("This is the exported dataset settings, update and submit new settings <a href='%s'>here</a>." %
            self.request.route_url("dataset", project_id=self.project_id, dataset_id=dataset_id), "warning")

        schema = convert_schema(SQLAlchemyMapping(Dataset, unknown='raise'), page="datasets", restrict_admin=True).bind(request=self.request, datasets=self.project.datasets)

        schema['dataset:publish_dataset'].widget.readonly = True
        schema['dataset:publish_date'].widget = deform.widget.DateInputWidget(readonly=True)
        schema['dataset:dataset_locations'].widget.readonly = True
        schema['dataset:location_offset'].widget.readonly = True

        schema.methods = self.project.methods

        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id, dataset_id=dataset_id),
            buttons=(), use_ajax=False)
        self.form.widget.template="edit_dataset_form"
        self.form.widget.readonly_template="readonly/edit_dataset_form"
        self.form.widget.get_file_fields = self._get_file_fields

        dataset = self.session.query(Dataset).filter_by(id=dataset_id).first()
        ingester_dataset = self.ingester_api.getDataset(dataset.dam_id)

        appstruct = {}

        # TODO

        return self._create_response(page_help=page_help, readonly=True)

    @view_config(renderer="../templates/form.pt", route_name="search", permission=NO_PERMISSION_REQUIRED)
    def search_view(self):
        """
        Search/browse page to allow users to navigate projects and their associated data.

        :return: Rendered HTML form ready for display.
        """
        schema = DataFilteringWrapper()
        search_info = 'search_info' in self.request.matchdict and self.request.matchdict['search_info'] or ()

        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, search_info=('',)), method="POST", buttons=('Search',), use_ajax=False)

        # Initialise empty display data
        schema['data_filtering'].results = []
        schema['data_filtering'].filter_data = {}
        schema['data_filtering'].selection_actions = []

        appstruct = {}
        # Add the non-deform data directly to the schema (keep filtering data)
        if self.request.method == "POST":
            try:
                appstruct = self.form.validate(self.request.POST.items())
            except ValidationFailure as e:
                appstruct = e.cstruct
                val_error = e

        # Add the filtering data directly to the schema (kind of hackish way of mixing template and deform data together).
        filter_data = {"order_by": self.request.POST.get('order_by', "creation"),
                       "order_direction": self.request.POST.get('order_direction', 'descending'),
                       "limit": self.request.POST.get('limit', "20"),
                       "page": self.request.POST.get('page', 0),
                       "num_pages": 0}
        schema['data_filtering'].filter_data = filter_data

        # Get data from both the address URL and POST data which allows searching URL address and/or form data.
        search_info = self.request.matchdict['search_info']

        # Display an error if the search data in the matchdict (address url) is invalid.
        if len(search_info) > 0 and search_info[0] != "data" and search_info[0] != "dataset" and search_info[0] != "project" and 'id_list=' not in search_info[0]:
            self.request.session.flash("Trying to search on invalid data (in the address bar), data has been ignored.", "Error")
            search_info = ()

        # Get all search data from both the address URL and the posted form values.
        search_data = self._get_search_data(search_info, 'data_filtering' in appstruct and appstruct['data_filtering'] or {})

        # Get a list of the id's of all items selected.
        selected_ids = []
        if self.request.method == "POST":
            for key, value in self.request.POST.items():
                if key[:len("selected_")] == "selected_":
                    selected_ids.append(value)

        results = []
        pagination_data = {}
        actions = []

        # If this is a list of unique identifiers, display the results (of possibly different types)
        if len(search_data) == 1 and "id_list" in search_data:
            results = self._get_id_list_results(search_data, pagination_data)

        # Find results when searching projects
        elif search_data['type'] == "project":
            results = self._get_project_results(search_data, pagination_data, selected_ids, actions)

        # Find results when searching datasets.
        elif search_data['type'] == "dataset":
            results = self._get_dataset_results(search_data, pagination_data, selected_ids, actions)

        # Find results when searching data.
        elif search_data['type'] == "data":
            results = self._get_data_results(search_data, pagination_data, selected_ids, actions)

        if isinstance(results, HTTPFound):
            return results

        # Add the found results and pagination data to the schema to be displayed.
        schema['data_filtering'].results = results

        schema['data_filtering'].selection_actions = actions

        schema['data_filtering'].filter_data['num_pages'] = pagination_data.get('num_pages', 1)
        schema['data_filtering'].filter_data['num_results'] = pagination_data.get('num_results', 0)
        schema['data_filtering'].filter_data['start_num'] = pagination_data.get('start_num', 0)
        end_num = pagination_data.get("end_num", 0) < pagination_data.get('num_results', 0) and \
                  pagination_data.get("end_num", 0) or pagination_data.get('num_results', 0)
        schema['data_filtering'].filter_data['end_num'] = end_num

        if 'val_error' in locals():
            display = val_error.render()
        else:
            display = self.form.render(appstruct)

        return self._create_response(readonly=False, form='display' in locals() and display or None)

    def _get_search_data(self, search_info, appstruct):
        is_search_info = len(search_info) > 0
        # If an ID list is provided directly, just display those objects without other search info.
        if is_search_info and 'id_list' in search_info[0]:
            return {"id_list": [int(id.strip()) for id in search_info[0][len("id_list="):].split(",")]}

        post_data = self.request.POST
        search_data = {}
        if is_search_info:
            search_data['type'] = search_info[0]

        for item in search_info[1:]:
            name, value = item.split("=")
            if "," in value or name == "id_list":
                value = value.split(",")
            search_data[name] = value

        if len(self.request.POST) > 0:
            items = self.request.POST.items()
            in_deform = False
            for key, value in items:
                if key == "__start__" and value == "data_filtering:mapping":
                    in_deform = True
                elif in_deform and key == "__end__" and value == "data_filtering:mapping":
                    in_deform = False

                if not in_deform and key[0] != "_":
                    if isinstance(value, basestring) and "," in value:
                        value = value.split(",")
                    search_data[key] = value

        for key, value in appstruct.items():
            if key[0] != "_" and value is not None and value is not colander.null:
                if isinstance(value, basestring) and "," in value:
                    value = value.split(",")
                search_data[key] = value

        # Add defaults
        if len(search_data) == 0:
            search_data = {
                "type": "project",
                "order_by": "modified",
                "order_direction": "descending",
                "limit": "20",
                "page": "0",
          }
        elif 'type' not in search_data:
            search_data['type'] = "project"

        return search_data

    def _get_id_list_results(self, search_data, pagination_data):
        id_list = search_data['id_list']
        id_lists = {"dataset": [], "project": [], "data": []}
        for id in id_list:
            if id[:len("dataset_")] == "dataset_" and isnumeric(id[len("dataset_"):]):
                id_lists['dataset'].append(id[len("dataset_"):])
            elif id[:len("project_")] == "project_" and isnumeric(id[len("project_"):]):
                id_lists['project'].append(id[len("project_"):])
            elif id[:len("data_")] == "data_" and isnumeric(id[len("data_"):]):
                id_lists['data'].append(id[len("data_"):])

        results = self._search_ids(id_lists['project'], id_lists['dataset'], id_lists['data'])

        sorted(results, key=itemgetter(search_data['order_by']), reverse=search_data['order_dir'] == "descending")

        limit = int(search_data.get("limit", 20))
        page = int(search_data.get("page", 0))

        num_pages = len(results) / int(limit)
        pagination_data['num_pages'] = num_pages
        pagination_data['num_results'] = len(results)
        pagination_data['start_num'] = search_data.get('page', 0) * limit
        pagination_data['end_num'] = pagination_data['start_num'] + limit

        results = results[page * limit: page * limit + limit]

        return results

    def _search_ids(self, project_ids=None, dataset_ids=None, data_ids=None):
        results = []
        if data_ids is not None and len(dataset_ids) > 0:
            datasets = self.session.query(Dataset).filter(Dataset.id.in_(dataset_ids)).all()
            for dataset in datasets:
                results.append(self._dataset_to_search_result(dataset))
        if project_ids is not None and len(project_ids) > 0:
            projects = self.session.query(Project).filter(Project.id.in_(project_ids)).all()
            for project in projects:
                results.append(self._project_to_search_result(project))
        if data_ids is not None:
#            data = ""
#            return self._dataset_to_search_result(dataset)
            pass
        return results

    def _get_project_results(self, search_data, pagination_data, selected_ids, actions):
        # Retreive all needed data and set defauts if needed.
        start_date = search_data.get('start_date', None)
        end_date = search_data.get('end_date', None)
        order_by = search_data.get('order_by', None)
        order_dir = search_data.get('order_direction', None)
        search_string = search_data.get('search_string', None)
        limit = int(search_data.get('limit', 20))
        id_list = search_data.get('id_list', None)
        if not isinstance(id_list, tuple) and not id_list is None:
            id_list = tuple(id_list)
        page = int(search_data.get('page', 0))
        data_type = search_data.get("type", "project")

        actions.append("Disable")
        actions.append("Enable")
        actions.append("View Datasets")

        # Handle any actions on selected items (eg. disable/enable the selected projects).
        actions_result = self._process_project_actions(search_data, selected_ids)
        if isinstance(actions_result, HTTPFound):
            return actions_result

        # Query the project table joined with the metadata table, we need the metadata table for sorting.
        query = self.session.query(Project).outerjoin(Metadata).filter(Project.template_only==False)

        # Filter based on project states.
        if 'state' in search_data:
            int_states = []
            if isinstance(search_data['state'], (list, tuple, dict, set)):
                for state in search_data['state']:
                    int_states.append(int(state))
            else:
                int_states.append(int(search_data['state']))

            if len(int_states) > 0:
                query = query.filter(Project.state.in_(int_states))

        # Filter based on start date
        if isinstance(start_date, date):
            query = query.filter(Project.date_created > start_date)

        # Filter based on end date
        if isinstance(end_date, date):
            query = query.filter(Project.date_created < end_date)

        # Order based on the type and direction
        if order_by == "id":
            if order_dir == "ascending":
                query = query.order_by(Project.id)
            else:
                query = query.order_by(Project.id.desc())
        if order_by == "created":
            if order_dir == "ascending":
                query = query.order_by(Project.date_created)
            else:
                query = query.order_by(Project.date_created.desc())
        elif order_by == "modified":
            if order_dir == "ascending":
                query = query.order_by(Project.date_modified)
            else:
                query = query.order_by(Project.date_modified.desc())
        elif order_by == "title":
            if order_dir == "ascending":
                query = query.order_by(Metadata.project_title)
            else:
                query = query.order_by(Metadata.project_title.desc())


        # Filter based on the entered search string
        if search_string:
            keywords = search_string.split(" ")
            regex_string = ".*(^| )%s($| ).*"

            for keyword in keywords:
                query = query.filter(
                    or_(or_(or_(Metadata.project_title.op('regexp')(regex_string % keyword),
                        Metadata.brief_desc.op('regexp')(regex_string % keyword)),
                        or_(Metadata.id.in_(self.session.query(Keyword.metadata_id).filter(
                            Keyword.keyword.op('regexp')(regex_string % keyword))),
                            Metadata.full_desc.op('regexp')(regex_string % keyword))),
                        Metadata.id.in_(self.session.query(MetadataNote.metadata_id).filter(
                            MetadataNote.note_desc.op('regexp')(regex_string % keyword)))))

        if id_list:
            num_id_list = []
            for id in id_list:
                if data_type in id:
                    num = id.strip()[len(data_type) + 1:]

                    if isnumeric(num):
                        num_id_list.append(int(num))
                    else:
                        self.request.session.flash("Entered ID's must be in the form <type>_<number>, "
                                                   "eg. project_1.  The bad id is: %s" % id, "warning")
                else:
                    self.request.session.flash("Entered ID's must be in the form <type>_<number>, eg. project_1."
                                               "  Also check that the correct type is selected.  The bad id is: %s" % id, "warning")

            if len(num_id_list) > 0:
                query = query.filter(Project.id.in_(num_id_list))

        num_results = query.count()
        num_pages = num_results / limit
        pagination_data['num_pages'] = num_pages
        pagination_data['num_results'] = num_results
        pagination_data['start_num'] = page * limit
        pagination_data['end_num'] = pagination_data['start_num'] + limit

        # Add the results limit (-1 is given for all/no limit)
        if int(limit) > 0:
            query = query.limit(limit)

            if page * limit < num_results:
                query = query.offset(page * limit)

        # Get all results ready to process and send to the template
        query_results = query.all()


        results = []
        for result in query_results:
            result = self._project_to_search_result(result)
            if result is not None:
                results.append(result)

        return results

    def _process_project_actions(self, search_data, selected_ids):
        if 'Disable' in search_data:
            for id in selected_ids:
                num = id[len("project_"):]
                if isnumeric(num):
                    # Check the user has permission to disable the project
                    self.request.matchdict["project_id"] = num
                    if has_permission(DefaultPermissions.DISABLE, self.context, self.request).boolval:
                        project = self.session.query(Project).filter_by(id=num).first()
                        if project is not None and project.state == ProjectStates.ACTIVE:
                            project.state = ProjectStates.DISABLED
                            for dataset in project.datasets:
                                dataset.disabled = True
                                self.ingester_api.disableDataset(dataset.dam_id)
                        else:
                            self.request.session.flash("You can't disable a project unless it is in the active state: %s" % num, "warning")
                    else:
                        self.request.session.flash("You don't have permission to disable this project: %s" % num, "warning")
                else:
                    self.request.session.flash("Trying to use an invalid id for actions: %s" % id, "warning")

        if 'Enable' in search_data:
            for id in selected_ids:
                num = id[len("project_"):]
                if isnumeric(num):
                    # Check the user has permission to disable the project
                    self.request.matchdict["project_id"] = num
                    if has_permission(DefaultPermissions.ENABLE, self.context, self.request).boolval:
                        project = self.session.query(Project).filter_by(id=num).first()
                        if project is not None and project.state == ProjectStates.DISABLED:
                            project.state = ProjectStates.ACTIVE
                            for dataset in project.datasets:
                                dataset.disabled = False
                                self.ingester_api.enableDataset(dataset.dam_id)
                        else:
                            self.request.session.flash("You can't enable a project unless it is in the disabled state: %s" % num, "warning")
                    else:
                        self.request.session.flash("You don't have permission to disable this project: %s" % num, "warning")
                else:
                    self.request.session.flash("Trying to use an invalid id for actions: %s" % id, "warning")

        if 'View Datasets' in search_data:
#            id_list = []
#            for id in selected_ids:
#                num = id[len("project_"):]
#                if isnumeric(num):
#                    project = self.session.query(Project).filter_by(id=num).first()
#                    if project is not None:
#                        id_list.extend([str(dataset.id) for dataset in project.datasets])

            return HTTPFound(self.request.route_url("search", search_info='/dataset/id_list=' + ",".join(selected_ids)))

    def _project_to_search_result(self, project):
        dataset_id_list = ["dataset_" + str(dataset.id) for dataset in project.datasets]

        self.request.matchdict['project_id'] = project.id # Needed for theauthentication to find permissions correctly

        can_edit = has_permission(DefaultPermissions.EDIT_PROJECT, self.context, self.request).boolval
        can_view = has_permission(DefaultPermissions.VIEW_PROJECT, self.context, self.request).boolval or can_edit
        can_edit_data = has_permission(DefaultPermissions.EDIT_DATA, self.context, self.request).boolval
        can_view_data = self.session.query(Metadata.access_rights).filter_by(project_id=project.id).one()[0] == "Open Access" or\
                        has_permission(DefaultPermissions.VIEW_DATA, self.context, self.request).boolval or can_edit_data
        can_edit_dataset = has_permission(DefaultPermissions.EDIT_INGESTERS, self.context, self.request).boolval

        if not (can_view or can_view_data or can_edit_dataset):
            return None

        urls = OrderedDict()
        if can_edit:
            urls["Edit Project"] = self.request.route_url("general", project_id=project.id)
        elif can_view:
            urls["View Project"] = self.request.route_url("general", project_id=project.id)

        if can_edit_dataset:
            urls["Add Dataset"] = self.request.route_url("dataset", project_id=project.id, dataset_id='')

        if can_view_data:
            urls["Datasets (click here for data)"] = self.request.route_url("search", search_info="/dataset/id_list=project_%s" % project.id)

        return {
            "id": project.id,
            "type": "project",
            "state": project.state,
            "created": project.date_created,
            "modified": project.date_modified,
            "description": project.information is not None and project.information.project_title or "",
            "urls": urls,
        }
    def _get_dataset_results(self, search_data, pagination_data, selected_ids, actions):
        # Retreive all needed data and set defauts if needed.
        start_date = search_data.get('start_date', None)
        end_date = search_data.get('end_date', None)
        order_by = search_data.get('order_by', None)
        order_dir = search_data.get('order_direction', None)
        search_string = search_data.get('search_string', None)
        limit = int(search_data.get('limit', 20))
        id_list = search_data.get('id_list', None)
        page = int(search_data.get('page', 0))
        data_type = search_data.get('type', "dataset")

        actions.append("Disable")
        actions.append("Enable")

        self._process_dataset_actions(search_data, selected_ids)

        # Query the project table joined with the metadata table, we need the metadata table for sorting.
        query = self.session.query(Dataset).outerjoin(Method, Metadata)

        # Filter based on project states.
        if 'state' in search_data:
            states = []
            if isinstance(search_data['state'], (list, tuple, dict, set)):
                for state in search_data['state']:
                    if int(state) == ProjectStates.ACTIVE:
                        states.append(0)
                    elif int(state) == ProjectStates.DISABLED:
                        states.append(1)
            else:
                states.append(int(search_data['state']) == ProjectStates.ACTIVE and 0 or 1)

            if len(states) > 0:
                query = query.filter(Dataset.disabled.in_(states))

        # Filter based on start date
        if isinstance(start_date, date):
            query = query.filter(Dataset.date_created > start_date)

        # Filter based on end date
        if isinstance(end_date, date):
            query = query.filter(Dataset.date_created < end_date)

        # Order based on the type and direction
        if order_by == "id":
            if order_dir == "ascending":
                query = query.order_by(Dataset.id)
            else:
                query = query.order_by(Dataset.id.desc())
        if order_by == "created":
            if order_dir == "ascending":
                query = query.order_by(Dataset.date_created)
            else:
                query = query.order_by(Dataset.date_created.desc())
        elif order_by == "modified":
            if order_dir == "ascending":
                query = query.order_by(Dataset.date_modified)
            else:
                query = query.order_by(Dataset.data_modified.desc())
        elif order_by == "title":
            if order_dir == "ascending":
                query = query.order_by(Metadata.project_title)
            else:
                query = query.order_by(Metadata.project_title.desc())


        # Filter based on the entered search string
        if search_string:
            keywords = search_string.split(" ")
            regex_string = ".*(^| )%s($| ).*"

            for keyword in keywords:
                query = query.filter(
                    or_(or_(or_(or_(Metadata.project_title.op('regexp')(regex_string % keyword),
                        Metadata.brief_desc.op('regexp')(regex_string % keyword)),
                        or_(Metadata.id.in_(self.session.query(Keyword.metadata_id).filter(
                            Keyword.keyword.op('regexp')(regex_string % keyword))),
                            Metadata.full_desc.op('regexp')(regex_string % keyword))),
                        Metadata.id.in_(self.session.query(MetadataNote.metadata_id).filter(
                            MetadataNote.note_desc.op('regexp')(regex_string % keyword)))),
                        or_(Method.method_description.op('regexp')(regex_string % keyword),
                            Dataset.id.in_(self.session.query(Location.dataset_id).filter(Location.name.op('regexp')(regex_string % keyword))))))

        if id_list:
            if id_list:
                normalised_id_list = []
                if isinstance(id_list, basestring):
                    id_list = (id_list,)

                for id in id_list:
                    if isnumeric(id):
                        normalised_id_list.append(int(id))
                    elif data_type in id:
                        num = id.strip()[len(data_type) + 1:]

                        if isnumeric(num):
                            normalised_id_list.append(int(num))
                        else:
                            self.request.session.flash("Entered ID's must be in the form <type>_<number>, "
                                                       "eg. project_1.  The bad id is: %s" % id, "warning")
                    elif 'project' in id:
                        num = id.strip()[len("project") + 1:]

                        if isnumeric(num):
                            project = self.session.query(Project).filter_by(id=num).first()
                            if project:
                                normalised_id_list.extend([dataset.id for dataset in project.datasets])
                    else:
                        self.request.session.flash("Entered ID's must be in the form <type>_<number>, eg. project_1."
                                                   "  Also check that the correct type is selected.  The bad id is: %s" % id, "warning")

            if len(normalised_id_list) > 0:
                query = query.filter(Dataset.id.in_(normalised_id_list))

        num_results = query.count()
        num_pages = num_results / int(limit)
        pagination_data['num_pages'] = num_pages
        pagination_data['num_results'] = num_results
        pagination_data['start_num'] = page * limit
        pagination_data['end_num'] = pagination_data['start_num'] + limit

        # Add the results limit (-1 is given for all/no limit)
        if int(limit) > 0:
            query = query.limit(limit)

            if page * limit < num_results:
                query = query.offset(page * limit)

        # Get all results ready to process and send to the template
        query_results = query.all()

        results = []
        for result in query_results:
            result = self._dataset_to_search_result(result)
            if result is not None:
                results.append(result)

        return results

    def _process_dataset_actions(self, search_data, selected_ids):
        if 'Disable' in search_data or "Enable" in search_data:
            for id in selected_ids:
                num = id[len("dataset_"):]
                if isnumeric(num):
                    dataset = self.session.query(Dataset).filter_by(id=num).first()
                    if dataset is not None:
                        search_data["project_id"] = dataset.project_id
                        # Check the user has permission to disable the project
                        if has_permission(DefaultPermissions.DISABLE, self.context, self.request).boolval:
                            if 'Disable' in search_data:
                                dataset.disabled = 1
                                self.ingester_api.disableDataset(dataset.dam_id)
                            else:
                                dataset.disabled = 0
                                self.ingester_api.enableDataset(dataset.dam_id)
                        else:
                            self.request.session.flash("You don't have permission to enable/disable this project: %s" % num, "warning")
                    else:
                        self.request.session.flash("Could not enable/disable a dataset that doesn't exist: %s" % num, "warning")
                else:
                    self.request.session.flash("Trying to use an invalid id for actions: %s" % id, "warning")

    def _dataset_to_search_result(self, dataset):
        self.request.matchdict['project_id'] = dataset.project_id # Needed for theauthentication to find permissions correctly

        can_edit = has_permission(DefaultPermissions.EDIT_INGESTERS, self.context, self.request).boolval
        can_edit_data = has_permission(DefaultPermissions.EDIT_DATA, self.context, self.request).boolval
        can_view_data = self.session.query(Metadata.access_rights).filter_by(project_id=dataset.project_id).one()[0] == "Open Access" or\
                        has_permission(DefaultPermissions.VIEW_DATA, self.context, self.request).boolval or can_edit_data

        if not (can_view_data or can_edit):
            return None

        urls = OrderedDict()
        if can_edit:
            urls["Edit Dataset"] = self.request.route_url("dataset", project_id=dataset.project_id, dataset_id=dataset.id)
        elif can_view_data:
            urls["View Dataset"] = self.request.route_url("dataset", project_id=dataset.project_id, dataset_id=dataset.id)

        urls["Project"] = self.request.route_url("search", search_info="/project/id_list=project_%s" % dataset.project_id)

        if can_edit_data:
            urls["Add Data"] = self.request.route_url("data", project_id=dataset.project_id, dataset_id=dataset.id, data_id=None)
        if can_view_data:
            urls["Access Data"] = self.request.route_url("search", search_info="/data/id_list=dataset_%s" % dataset.id)

        result = {
            "id": dataset.id,
            "type": "dataset",
            "state": dataset.disabled is True and ProjectStates.DISABLED or ProjectStates.ACTIVE,
            "created": dataset.date_created,
            "modified": dataset.date_modified,
            "description": dataset.record_metadata and dataset.record_metadata.project_title or dataset.method and dataset.method.method_name or '',
            "urls": urls
            }
        return result



    @cache_region('default_term')
    def _search_data(self, search_info):
        """
        Implements cached bulk data searching - this functionality could easily go inline except for caching.

        :param search_info: Filtering information such as dataset_id,
        :return: Bulk results for the data found with the given filtering.
        """
        dataset_dam_id, start_date, end_date, page, limit = search_info

        results = self.ingester_api.search(DataEntrySearchCriteria(int(dataset_dam_id), start_time=start_date, end_time=end_date),
            page * limit, limit)

        return results

    def _get_data_results(self, search_data, pagination_data, selected_ids, actions):
        # Retreive all needed data and set defauts if needed.
        start_date = search_data.get('start_date', None)
        end_date = search_data.get('end_date', None)
        order_by = search_data.get('order_by', "created")
        order_dir = search_data.get('order_direction', "descending")
        search_string = search_data.get('search_string', None)
        limit = int(search_data.get('limit', 20))
        id_list = search_data.get('id_list', None)
        if not isinstance(id_list, (list, tuple)):
            id_list = [id_list]
        page = int(search_data.get('page', 0))
        data_type = search_data.get('type', "dataset")

#        actions.append("Add Data")
        actions.append("Add QA")

        self._process_data_actions(search_data, selected_ids)

        results = []
        if id_list:
            normalised_id_list = []
            dataset_list = []
            for id in id_list:
                if "%s_" % data_type in id:
                    id_nums = id.strip()[len(data_type) + 1:].split("_")

                    if len(id_nums) == 2 and isnumeric(id_nums[0]) and isnumeric(id_nums[1]):
                        dataset_id, data_id = id_nums

                        # Check permissions
                        self.request.matchdict["project_id"] = self.session.query(Dataset.project_id).filter_by(id=dataset_id).first()[0]
                        if has_permission(DefaultPermissions.VIEW_DATA, self.context, self.request) or has_permission(DefaultPermissions.EDIT_DATA, self.context, self.request):
                            normalised_id_list.append((int(dataset_id), int(data_id)))
                        else:
                            self.request.session.flash("You don't have permission to view data for dataset_%s" % dataset_id, "error")
                    else:
                        self.request.session.flash("Entered ID's must be in the form project_<num>, dataset_<num> or data_<num>_<num>."
                                                   "  The bad id is: %s" % id, "warning")
                elif 'dataset' in id:
                    num = id.strip()[len("dataset") + 1:]

                    if isnumeric(num):
                        # Check permissions
                        self.request.matchdict["project_id"] = self.session.query(Dataset.project_id).filter_by(id=num).first()[0]
                        if has_permission(DefaultPermissions.VIEW_DATA, self.context, self.request) or has_permission(DefaultPermissions.EDIT_DATA, self.context, self.request):
                            dataset_list.append(num)
                        else:
                            self.request.session.flash("You don't have permission to view data for dataset_%s" % num, "error")
                elif 'project' in id:
                    num = id.strip()[len("project") + 1:]

                    if isnumeric(num):
                        project = self.session.query(Project).filter_by(id=num).first()

                        if project:
                            # Check permissions
                            self.request.matchdict["project_id"] = project.id
                            if has_permission(DefaultPermissions.VIEW_DATA, self.context, self.request) or has_permission(DefaultPermissions.EDIT_DATA, self.context, self.request):
                                dataset_list.extend([dataset.id for dataset in project.datasets])
                            else:
                                self.request.session.flash("You don't have permission to view data for project_%s" % num, "error")
                else:
                    self.request.session.flash("Entered ID's must be in the form project_<num>, dataset_<num> or data_<num>_<num>."
                                               "  The bad id is: %s" % id, "warning")

            data_entries = []
            num_results = 0
            if len(dataset_list) > 0:
                for dataset_id in dataset_list:
                    dam_id = self.session.query(Dataset.dam_id).filter_by(id=dataset_id).first()
                    if len(dam_id) > 0 and dam_id[0] is not None:
                        search_results = self._search_data((dam_id[0], start_date, end_date, page, limit))
                        num_results += search_results.count
                        data_entries.extend(search_results.results)

            # There is no way to paginate over multiple searches, so just limit the results
            if len(dataset_list) > 1:
                self.request.session.flash("Results pagination is disabled while you are searching across multiple "
                                           "datasets, either select to display more results from the dropdown at the "
                                           "top-right or search on only 1 dataset.")
                num_results = limit

            if len(normalised_id_list) > 0:
                for dataset_id, data_id in id_list:
                    num_results += 1
                    data_entries.append(self.ingester_api.getDataEntry(dataset_id, data_id))

            for data_entry in data_entries:
                results.append(self._data_to_search_result(data_entry))

        else:
            self.request.session.flash("Data must be searched using the ID List, other fields filter those results."
                                       "  It is recommended that you view data associated with a dataset rather "
                                       "than trying to search data directly.", "warning")

#        sorted(results, key=itemgetter(order_by), reverse=order_dir == "descending")

        limit = limit
        page = page

        num_pages = num_results / int(limit)
        pagination_data['num_pages'] = num_pages
        pagination_data['num_results'] = num_results
        pagination_data['start_num'] = int(search_data.get('page', 0)) * limit
        pagination_data['end_num'] = int(pagination_data['start_num']) + limit

#        results = results[page * limit: page * limit + limit]

        return results


    def _process_data_actions(self, search_data, selected_ids):
        if 'Add QA' in search_data:
            data_ids = [id for id in selected_ids]


    def _data_to_search_result(self, data):
        dataset_data = self.session.query(Dataset.project_id, Dataset.id).filter_by(dam_id=data.dataset).first()
        if not dataset_data:
            logger.error("Ingester dataset doesn't exist within the Provisioning Interface.  dam_id: %s" % data.dam_id)
            project_id = None
            dataset_id = None
        else:
            project_id, dataset_id = dataset_data

        self.request.matchdict["project_id"] = project_id

        can_view = has_permission(DefaultPermissions.VIEW_DATA, self.context, self.request).boolval
        can_edit = has_permission(DefaultPermissions.EDIT_DATA, self.context, self.request).boolval

        urls = OrderedDict()
        if can_edit:
            urls["Edit Data"] = self.request.route_url("data", project_id=project_id, dataset_id=dataset_id, data_id=data.id)
        elif can_view:
            urls["View Data"] = self.request.route_url("data", project_id=project_id, dataset_id=dataset_id, data_id=data.id)

        urls["Project"] = self.request.route_url("search", search_info="/project/id_list=project_%s" % project_id)
        urls["Dataset"] = self.request.route_url("search", search_info="/dataset/id_list=dataset_%s" % dataset_id)

        return {
            "id": "%s_%s" % (data.dataset, data.id),
            "type": "data",
            "state": None,
            "created": data.timestamp,
            "modified": data.timestamp,
            "description": str(data),
            "urls": urls
            }

    @view_config(route_name="data_calibration", permission=DefaultPermissions.VIEW_DATA)
    def data_calibration_view(self):
        """

        :return:
        """
        dataset_id = int(self.request.matchdict['dataset_id'])
        dataset_dam_id = int(self.session.query(Dataset.dam_id).filter_by(id=dataset_id).first()[0])
        id_list = self.request.matchdict['id_list'].split(",")
        data_ids = []
        for id in id_list:
            if id is not None and len(id) > 0 and isnumeric(id):
                data_ids.append(int(id))

        calibration_id = self.request.matchdict.get('calibration_id', None)
        if isinstance(calibration_id, tuple) and len(calibration_id) > 0 and calibration_id[0] != 'None':
            calibration_id = calibration_id[0]
        else:
            calibration_id = None

        page_help="Sets the quality assurance information for all selected data to the entered values, this will" \
                  "over-write any previous quality assurance."

        schema_object = self.session.query(MethodSchema).filter_by(schema_type=DataEntryMetadataSchema.__xmlrpc_class__).first()
        schema = DataTypeSchema(schema_object).bind(request=self.request)
        self.form = Form(schema,
            action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id,
                dataset_id=dataset_id, id_list=self.request.matchdict['id_list'], calibration_id=calibration_id),
            buttons=calibration_id is not None and len(calibration_id) > 0 and ('Save',) or ('Add',), use_ajax=False)

                #todo
        appstruct = {}
        calibration = None
        # If we are currently looking at a single DataEntry, get the calibration information (if looking at multiple
        # DataEntries the calibrations may be different - so don't load any data).
        if len(data_ids) == 1:
            calibrations = self.ingester_api.search(DataEntryMetadataSearchCriteria(int(dataset_dam_id), int(data_ids[0])), offset=0, limit=1000)

            # A DataEntry can have 1 calibration for each schema, so make sure we are looking at the correct one.
            for result in calibrations.results:
                if result.metadata_schema == schema_object.dam_id:
                    # When we have the correct calibration - set the appstruct as its data.
                    appstruct = deepcopy(result.data)
                    calibration = result

                    to_delete = []
                    for key in appstruct:
                        if isinstance(appstruct[key], jcudc24ingesterapi.models.data_entry.FileObject):
                            # TODO: Customised schemas for data calibrations aren't implmeneted yet, but when they are, we will need a getDataEntryCalibrationStream or similar.
                            file_stream = self.ingester_api.getDataEntryStream(int(dataset_dam_id), int(data_ids[0]), key)
                            file_stream.fp.close()
                            appstruct[key] = {
                                "is_external": True,
                                "filepath": file_stream.url,
                                "filename": file_stream.url.split("/")[-1]
                            }
                    break

        # If this page was navigated to from another form, save that form.
        if self.request.referrer != self.request.path_url:
            self._handle_form()
        elif len(self.request.POST) > 0:
            # Load the form data
            appstruct = self._get_post_appstruct()
            # Convert the data and schema to a CAModel which provides correct data types etc.
            model = DataTypeModel(schema, appstruct=appstruct)
            files = []
            to_delete = []
            empty = True

            if calibration is None:
                if schema_object.dam_id is None:
                    self.ingester_api.post(schema_object)
                calibration = DataEntryMetadataEntry(metadata_schema_id=int(schema_object.dam_id), dataset_id=dataset_dam_id)

            for field in model._schema.children:
                key = field.name
                calibration_value = calibration.data.get(key, None)

                if isinstance(field.widget, ProvisioningFileUploadWidget):
                    if isinstance(appstruct.get(key, colander.null), basestring):
                        file_val = appstruct[key]
                        # If the current data file hasn't been changed
                        if file_val.startswith("{") and file_val.endswith("}"):
                            to_delete.append(key) # Remove the field so that it isn't changed.

                        # Else if a new file was uploaded
                        else:
                            tmp_filename = file_val.split("\\")[-1]
                            f_name = tmp_filename.split(".", 1)[1]
                            file = FileObject(f_path=file_val, file_name=f_name)
                            calibration[key] = file
                            empty = False
                    else:
                        to_delete.append(key)
                    files.append(key)
                else:
                    calibration[key] = getattr(model, key)
                    if calibration[key] is not None:
                        empty = False

            for key in to_delete:
                if key in calibration.data:
                    del calibration.data[key]

            if not empty:
                old_appstruct = appstruct
                unit = self.ingester_api.createUnitOfWork()
                # Save the calibration to all DataEntry(s)
                for id in data_ids:
                    data_calibration = deepcopy(calibration)
                    data_calibration.object_id = id
                    saved_calibration = self.ingester_api.post(data_calibration)
                unit.commit()

                # This ensures the shown data is what is actually saved.
                appstruct = saved_calibration.data

                # Fix file fields as they aren't returned from the provisioning interface.
                for file in files:
                    appstruct[file] = old_appstruct[file]

#                if calibration_id is None:
#                    if 'Add' in self.request.POST:
#                    # If we just added a new DataEntry redirect to editing the newly added DataEntry.
#                        return HTTPFound(self.request.route_url(self.request.matched_route.name, project_id=self.project_id,
#                            dataset_id=dataset_id, data_id=calibration.id))
#                    else:
#                        # Add the data and goto a blank form for adding another.
#                        appstruct = {}

        self._model_appstruct = appstruct

        # Create the response and display the form
        return self._create_response(
            readonly=not has_permission(DefaultPermissions.EDIT_DATA, self.context, self.request).boolval)


    @view_config(route_name="data", permission=DefaultPermissions.VIEW_DATA)
    def data_view(self):
        """

        :return:
        """
        dataset_id = self.request.matchdict['dataset_id']
        if dataset_id is None or dataset_id == "None" or not isnumeric(dataset_id):
            return HTTPFound(self.request.route_url("search", search_info="/data/id_list=project_%s" % self.project_id))

        dam_id = int(self.session.query(Dataset.dam_id).filter_by(id=dataset_id).first()[0])

        data_id = self.request.matchdict['data_id']
        if isinstance(data_id, tuple) and len(data_id) > 0 and data_id[0] != 'None':
            data_id = data_id[0]
        else:
            data_id = None

        page_help=""

        method_id = self.session.query(Dataset.method_id).filter_by(id=dataset_id).first()[0]
        schema_id = self.session.query(Method.method_schema_id).filter_by(id=method_id).first()[0]
        schema = DataTypeSchema(self.session.query(MethodSchema).filter_by(id=schema_id).first())
        schema = schema.bind(request=self.request)
        self.form = Form(schema,
            action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id,
                dataset_id=dataset_id, data_id=data_id),
            buttons=data_id is not None and len(data_id) > 0 and ('Save',) or ('Add & Create New', 'Add'), use_ajax=False)

        appstruct = {}
        data_entry = None
        if data_id is not None and isnumeric(data_id):
            data_entry = self.ingester_api.getDataEntry(int(dam_id), int(data_id))
            appstruct = deepcopy(data_entry.data)

            to_delete = []
            for key in appstruct:
                if isinstance(appstruct[key], jcudc24ingesterapi.models.data_entry.FileObject):
                    file_stream = self.ingester_api.getDataEntryStream(int(dam_id), int(data_id), key)
                    file_stream.fp.close()
                    appstruct[key] = {
                        "is_external": True,
                        "filepath": file_stream.url,
                        "filename": file_stream.url.split("/")[-1]
                    }

        # If this page was only called for saving and a rendered response isn't needed, return now.
        if self.request.referrer != self.request.path_url:
            self._handle_form()

        elif len(self.request.POST) > 0:
            appstruct = self._get_post_appstruct()
            model = DataTypeModel(schema, appstruct=appstruct)
            files = []
            to_delete = []

            if data_entry is None:
                data_entry = DataEntry(dataset=dam_id, timestamp=datetime.now())

            empty = True
            for field in model._schema.children:
                key = field.name
                data_value = data_entry.data.get(key, None)

                if isinstance(field.widget, ProvisioningFileUploadWidget):
                    # If the file was set/left as it was.
                    if isinstance(appstruct.get(key, colander.null), basestring):
                        file_val = appstruct[key]
                        # If the current data file hasn't been changed
                        if file_val.startswith("{") and file_val.endswith("}"):
                            to_delete.append(key) # Remove the field so that it isn't changed.

                        # Else if a new file was uploaded
                        else:
                            tmp_filename = file_val.split("\\")[-1]
                            f_name = tmp_filename.split(".", 1)[1]
                            file = FileObject(f_path=file_val, file_name=f_name)
                            data_entry[key] = file
                            empty = False

                    # Else if the data file was deleted.
                    else:
                        to_delete.append(key) # Remove the field so that it isn't changed.
                    files.append(key)
                else:
                    data_entry[key] = getattr(model, key)
                    if data_entry[key] is not None:
                        empty = False

            for key in to_delete:
                if key in data_entry.data:
                    del data_entry.data[key]

            if not empty:
                old_appstruct = appstruct
                unit = self.ingester_api.createUnitOfWork()
                saved_data_entry = unit.post(data_entry)
                unit.commit()

                # This ensures the shown data is what is actually saved.
                appstruct = data_entry.data

                # Fix file fields as they aren't returned from the provisioning interface.
                for file in files:
                    appstruct[file] = old_appstruct[file]

                if data_id is None:
                    if 'Add' in self.request.POST:
                    # If we just added a new DataEntry redirect to editing the newly added DataEntry.
                        return HTTPFound(self.request.route_url(self.request.matched_route.name, project_id=self.project_id,
                            dataset_id=dataset_id, data_id=data_entry.id))
                    else:
                        # Add the data and goto a blank form for adding another.
                        appstruct = {}

        self._model_appstruct = appstruct

        # Create the response and display the form
        return self._create_response(
            readonly=not has_permission(DefaultPermissions.EDIT_DATA, self.context, self.request).boolval)


    @view_config(route_name="permissions", permission=DefaultPermissions.EDIT_SHARE_PERMISSIONS)
    def permissions_view(self):
        """
        Contextual option that allows project creators/administrators to give other users permissions or the
        current project.

        :return: HTML rendering of the create page form.
        """
        page_help=""

        all_users = self.session.query(User).all()
        json_users = json.dumps([{"label": user.display_name, "identifier": user.id} for user in all_users])
        user_mapping = {str(user.id): user.display_name for user in all_users}
        schema = Sharing()
        schema['shared_with'].users=json_users
        schema['shared_with'].children[0].user_mapping=user_mapping
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id), buttons=('Save',), use_ajax=False)

        # Update the user permissions
        modified = []
        appstruct = self._get_post_appstruct()
        if len(appstruct) > 0:
            users_to_delete = [user_id for user_id, in self.session.query(distinct(ProjectPermissions.user_id)).filter_by(project_id=self.project_id).all()]

            for share in appstruct['shared_with']:
                user = self.session.query(User).filter_by(id=share['user_id']).first()

                if user is None:
                    self.request.session.flash("You selected an invalid user, please use the autocomplete input and don't enter text manually.", "error")
                    continue

                if user.id in users_to_delete:
                    users_to_delete.remove(user.id)

                has_this_permission = False
                for field_name, value in share.items():
                    if field_name == 'user_id':
                        continue

                    permission_name = field_name[:-len("_permission")]

                    permission = self.session.query(Permission).filter_by(name=permission_name).first()

                    has_this_permission = False
                    for i in range(len(user.project_permissions)):
                        if user.project_permissions[i].project_id == long(self.project_id) and user.project_permissions[i].permission_id == permission.id:  # If the user already has this permission
                            if value == 'false' or value is False:
                                user_permission = user.project_permissions[i]
                                modified.append(("Remove", user_permission.permission.name, user_permission.user_id,))
                                self.session.delete(user_permission)

                            has_this_permission = True
                            break

                    if not has_this_permission and value is True:
                        user.project_permissions.append(ProjectPermissions(self.project_id, permission.id, user.id))
                        modified.append(("Add", permission.name, user.display_name))

                        self._add_default_notification_configs(user.id, self.project_id)

            for user_id in users_to_delete:
#                del_permissions = self.session.query(ProjectPermissions).filter_by(project_id=self.project_id).filter_by(user_id=user_id).all()
                self.session.query(ProjectPermissions).filter_by(project_id=self.project_id).filter_by(user_id=user_id).delete()
                modified.append(("Remove", "All", user_id))

            self.session.flush()

        # Update how the modified permissions will be displayed in the sent emails.
        for changed_permissions in modified:
            if isinstance(changed_permissions[1], (int, long)):
                user = self.session.query(User).filter_by(id=changed_permissions[1]).first()
                if user is not None:
                    changed_permissions[1] = user.display_name
            if isinstance(changed_permissions[2], (int, long)):
                permission = self.session.query(Permission).filter_by(id=changed_permissions[2]).first()
                if permission is not None:
                    modified.append((changed_permissions[0], changed_permissions[1], permission.name))
                    modified.remove(changed_permissions)

        # Send notification emails
        if len(modified) > 0:
            modified_text = "<br />".join(["%s %s for %s" % changed_permission for changed_permission in modified])
            self._send_email_notifications(NotificationConfig.permission_changes.key, modified=modified_text)

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

            current_user[project_permission.permission.name + "_permission"] = 'true'

        # Directly set the model appstruct by-passing the usual workflow appstruct generation (because this view isn't directly mapped to an ColanderAlchemy model)
        self._model_appstruct = appstruct
        self.form.cstruct = {'shared_with': colander.null}
        if hasattr(self.form.children[0], 'sequence_fields'):
            delattr(self.form.children[0], 'sequence_fields')

        # Create the response and display the form
        return self._create_response(
            readonly=not has_permission(DefaultPermissions.EDIT_SHARE_PERMISSIONS, self.context, self.request).boolval)

    def _add_default_notification_configs(self, user_id, project_id):
        # Add email notification configurations for the user.
        user_notification_configs = self.session.query(UserNotificationConfig).filter_by(user_id=user_id).first()
        if user_notification_configs is None:
            user_notification_configs = UserNotificationConfig()
            user_notification_configs.default_notification_config = NotificationConfig()
            user_notification_configs.user_id = user_id

        if self.session.query(ProjectNotificationConfig).filter_by(user_notification_config_id=user_notification_configs.id, project_id=project_id).count() == 0:
            new_config = ProjectNotificationConfig()
            new_config.project_id = project_id
            new_config.user_notification_config_id = user_notification_configs.id
            new_config.notification_config = NotificationConfig()
            for config in new_config.notification_config.schema.children:
                name = fix_schema_field_name(config.name)
                setattr(new_config.notification_config, name, getattr(user_notification_configs.default_notification_config,name))
            user_notification_configs.notification_configs.append(new_config)


    @view_config(route_name="notifications", permission=DefaultPermissions.VIEW_DATA)
    def notifications_view(self):
        """
        Contextual option that allows users to edit their own notifications and if they have the EDIT_NOTIFIACTIONS
        permission they can edit others notifications.

        :return: HTML rendering of the create page form.
        """
        page_help = ""
        self._check_project_page_permissions()

        self._model_type = UserNotificationConfig

        configs = self.session.query(UserNotificationConfig.id).filter_by(user_id=self.request.user.id).first()
        if configs is None:
            self._model = UserNotificationConfig()
            self._model.user_id = self.request.user.id
            self._model.default_notification_config = NotificationConfig()
            self.session.add(self._model)
            self.session.flush()
            self._model_id = self._model.id
        else:
            self._model_id = configs[0]

        page_help = ""
        schema = convert_schema(SQLAlchemyMapping(UserNotificationConfig, unknown='raise', ca_description="")).bind(
            request=self.request)


        DEFAULT_CONFIGS_INDEX = 'usernotificationconfig:default_notification_config'
        DEFAULT_NEW_PROJECT_INDEX = DEFAULT_CONFIGS_INDEX + ":new_projects"
        DEFAULT_NEW_DATASET_INDEX = DEFAULT_CONFIGS_INDEX + ":new_datasets"
        PROJECT_CONFIGS_INDEX = 'usernotificationconfig:notification_configs'
        PROJECT_NOTIFICATION_CONFIG_INDEX = "projectnotificationconfig:notification_config"
        PROJECT_NOTIFICATION_NEW_PROJECT_INDEX = "projectnotificationconfig:notification_config:new_projects"

        has_admin_permission = has_permission(DefaultPermissions.ADMINISTRATOR, self.context, self.request).boolval
        schema[DEFAULT_CONFIGS_INDEX][DEFAULT_NEW_PROJECT_INDEX].widget.hidden=not has_admin_permission
        schema[DEFAULT_CONFIGS_INDEX][DEFAULT_NEW_DATASET_INDEX].widget.hidden=not has_admin_permission
#        schema[PROJECT_CONFIGS_INDEX].children[0][PROJECT_NOTIFICATION_CONFIG_INDEX][PROJECT_NOTIFICATION_NEW_PROJECT_INDEX].widget.hidden = True

        def get_project_description(project_id):
            if project_id is None or project_id is colander.null or project_id == '':
                project_id = self.project_id

            description_string = "<a href='%s'>[%s]: %s</a>"
            if project_id == self.project_id:
                description_string = "(Current project) " + description_string

            # Handle special characters.
            project_title = self.session.query(Metadata.project_title).filter_by(project_id=project_id).first()[0]
            if isinstance(project_title, basestring):
                if isinstance(project_title, unicode):
                    project_title = project_title.encode("utf-8")
                else:
                    project_title = unicode(project_title, "utf-8")

            return description_string % (
                self.request.route_url("general", project_id=project_id), project_id,
                project_title)
        schema[PROJECT_CONFIGS_INDEX].children[0].get_project_description = get_project_description

        self.form = Form(schema,
            action=self.request.route_url(self.request.matched_route.name, project_id=self.project_id),
            buttons=('Save', ), use_ajax=False, ajax_options=redirect_options)

        appstruct = self._get_post_appstruct()
        if PROJECT_CONFIGS_INDEX in appstruct:
            for notification_settings in appstruct[PROJECT_CONFIGS_INDEX]:
                key_prefix = "projectnotificationconfig:"

                # If this is a newly added configuration, set the project_id and user_notification_config_id.
                if notification_settings[key_prefix + ProjectNotificationConfig.project_id.key] in (None, colander.null):
                    notification_settings[key_prefix + ProjectNotificationConfig.project_id.key] = self.project_id
                    notification_settings[key_prefix + ProjectNotificationConfig.user_notification_config_id.key] = self._model_id

                    # If this page was only called for saving and a rendered response isn't needed, return now.
        if self._handle_form():
            return

        # Selectivly show the add configuration for this project based on if it is already added.
        has_notification_settings = self.session.query(ProjectNotificationConfig).filter_by(project_id=self.project_id,
            user_notification_config_id=self._model_id).count() > 0
        schema[PROJECT_CONFIGS_INDEX].widget.show_add = not has_notification_settings

        # Set the limit to the current number + 1 so that the user can't add a configuration for this project twice.
        notifications_settings_widget_max_len = self.session.query(ProjectNotificationConfig).filter_by(
            user_notification_config_id=self._model_id).count()
        schema[PROJECT_CONFIGS_INDEX].widget.max_len = notifications_settings_widget_max_len + 1

        # Set the default values based on the users notification defaults.
        defaults = self._get_model().default_notification_config
        for config in schema[PROJECT_CONFIGS_INDEX].children[0][PROJECT_NOTIFICATION_CONFIG_INDEX]:
            normalised_name = fix_schema_field_name(config.name)
            config.default = getattr(defaults, normalised_name)

        return self._create_response(page_help=page_help, readonly=False)

    # --------------------WORKFLOW EXCEPTION VIEWS-------------------------------------------
    @view_config(context=Exception, route_name="workflow_exception", permission=NO_PERMISSION_REQUIRED)
    def exception_view(self):
        """
        Exception view for any exception that occurs on project/workflow pages.

        :return: Redirect to the same page (without variables), general or create page.
        """
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
                self.request.session.flash('There is no page at the requested address (%s), please don\'t edit the address bar directly.' % self.request.path_url, 'error')
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
        """
        Exception view for all database errors.
        - MySQL server errors can be fixed by re-displaying the page (eg new DB connection is established).

        :return: Either an internal redirect on server gone away error else display an error message.
        """
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



