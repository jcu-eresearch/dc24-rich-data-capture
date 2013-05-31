"""
Provides all non-project related views, this includes general website pages such as the dashboard, admin and login as
well as exception views.
"""

import ConfigParser
import inspect
import logging
from mhlib import isnumeric
from string import split
import urllib2
import datetime
import colander
from jcudc24provisioning.controllers.authentication import DefaultPermissions, DefaultRoles
from jcudc24provisioning.controllers.ca_schema_scripts import convert_schema
from jcudc24provisioning.models.ca_model import CAModel
from jcudc24provisioning.models.project import Metadata, Dataset, Project
from jcudc24provisioning.resources import enmasse_requirements
from jcudc24provisioning.views.page_locking import PageLocking
import pyramid
from pyramid.httpexceptions import HTTPNotFound, HTTPFound, HTTPClientError, HTTPBadRequest, HTTPForbidden
from pyramid.interfaces import IRoutesMapper, IViewClassifier, IView
from pyramid.view import view_config, forbidden_view_config, view_defaults, render_view_to_response
from pyramid.security import remember, forget, authenticated_userid, has_permission
from deform.form import Form
from jcudc24provisioning.models.website import Login, User, LocalLogin, user_roles_table, Role, PageLock
from jcudc24provisioning.models import DBSession
from pyramid.request import Request
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from sqlalchemy.orm import object_mapper, RelationshipProperty, ColumnProperty
from zope.interface import providedBy
import deform
from colanderalchemy.types import SQLAlchemyMapping
import deform
from deform.exception import ValidationFailure


__author__ = 'Casey Bajema'
from pyramid.renderers import get_renderer
from pyramid.decorator import reify

logger = logging.getLogger(__name__)

PAGES = [
    {'route_name': 'dashboard', 'title': "Home", 'page_title': 'EnMaSSE Dashboard', 'hidden': False},
    {'route_name': 'create', 'title': 'New Project', 'page_title': 'Setup a New Project', 'hidden': False, },
    {'route_name': 'search', 'title': 'Browse Projects', 'page_title': 'Browse Projects & Data'},
    {'route_name': 'help', 'title': 'Help & Support', 'page_title': 'Help & Support', 'hidden': False},
#    {'route_name': 'search', 'title': 'Search Website', 'page_title': 'Search Website', 'hidden': True},
    {'route_name': 'admin', 'title': 'Administrator', 'page_title': 'Administrator', 'view_permission': DefaultPermissions.ADMINISTRATOR},
    {'route_name': 'login', 'title': 'Log in', 'page_title': 'Log in', 'hidden': True},
    {'route_name': 'login_shibboleth', 'title': 'Log in', 'page_title': 'Log in', 'hidden': True},
]

@view_defaults(permission=pyramid.security.NO_PERMISSION_REQUIRED)
class Layouts(object):
    """
    Class for displaying all non-project views, this allows much of the functionality to be abstracted and reused.
    """

    def __init__(self, context, request):
        enmasse_requirements.need()
        self.context = context
        self.request = request
        self.config = request.registry.settings
        self.session = DBSession
        global pyramid_request
        pyramid_request = request

        if "lock_ids" not in request.session:
            request.session["lock_ids"] = []

        # Implement page locking - this will only work during normal navigation
        # TODO: This implementation leaves locks for non-form pages in the DB until they timeout.
        self.lock_id = None
        if request.user is not None and 'internal_redirect' not in request.POST:
            locker = PageLocking(request)
            if 'lock_id' in request.POST:
                locker.unlock_page(request.POST['lock_id'])

            self.lock_id = locker.lock_page(request.user.id, request.path)

    @reify
    def global_template(self):
        """
        Returns the root level template that wraps everything.

        :return: Global template.
        """
        renderer = get_renderer("../templates/template.pt")
        return renderer.implementation().macros['layout']

    @reify
    def get_user(self):
        """
        Get the currently logged in user from the request (this is a custom attribute attached by the get_user method
        in controllers/authentication.py)
        :return:
        """
        return self.request.user

    @reify
    def menu(self):
        """
        Loop through the PAGES array to find all menus that should be displayed based on the current page.

        :return: Array of main menu items to display.
        """
        new_menu = PAGES[:]

        introspector = self.request.registry.introspector
        hidden = []
        for menu in new_menu:
            menu['current'] = (menu['route_name'] == self.request.matched_route.name)

            try:
                menu['href'] = self.request.route_url(menu['route_name'], search_info="")

            except Exception as e:
                logger.error("Menu item has an invalid route_name: %s" % menu['route_name'])
                raise ValueError("Menu item has an invalid route_name: %s" % menu['route_name'])

            if 'hidden' in menu and menu['hidden'] is True:
                hidden.append(menu)

            if 'view_permission' in menu and not has_permission(menu['view_permission'], self.context, self.request):
                hidden.append(menu)


        for menu in hidden:
            new_menu.remove(menu)

        return new_menu


    def find_page_title(self):
        """
        Find the title for this page from the PAGES array.  The title is displayed both in the heading and the browser
        tab text.

        :return: Page title based on the current page
        """
        for page in PAGES:
            if page['route_name'] == self.request.matched_route.name:
                return page['page_title']

        return None

    #        raise ValueError("There is no page title for this address: " + str(self.request.url))

    def _redirect_to_target(self, target):
        """
        Do an internal redirect to the target page, the redirect passes all POST variables as well as the request.user
        so that authentication works correctly on the target page.

        :param target:
        :return:
        """
    #        target = self.get_address(self.request.POST['target'])
    #        q = self.request.registry.queryUtility
    #        routes_mapper = q(IRoutesMapper)
    #        info = routes_mapper(self.request)
    #        context_iface = providedBy(self.context)
    #
    #        view_callable = self.request.registry.adapters.lookup(
    #            (IViewClassifier, self.request.request_iface, context_iface),
    #            IView, name=info[], default=None)
    #        response = view_callable(self.context, self.request)

        # Fix target to work when there is a script_name being used.
        target = target.replace(self.request.script_name, "", 1)
        referrer = self.request.referrer.replace(self.request.script_name, "", 1)

        sub_request = Request.blank(path=target, POST=[], referrer=referrer,
            referer=referrer)

        # Add the user object so the subrequest can authenticate.
        sub_request.user = self.request.user

        # Request sorts the post items (which breaks deform) - fix it directly
        if len(self.request.POST) > 0:
            sub_request.POST._items = self.request.POST._items + [("internal_redirect", True),]

        return self.request.invoke_subrequest(sub_request)

    #        return render_view_to_response(None, self.request, name=target)

    #        introspector = self.request.registry.introspector
    #        target_callable = introspector.get('views', target)
    #        route_intr = introspector.get('routes', target)

    def _clone_model(self, source, parent=None, copies=None):
        """
        Clone a database model, this returns a duplicate model with the ID removed.

        :param: parent may be used to test if an ID links to a parent item.
        :param: copies is used to hold all duplicated models so models that are referenced twice only get duplicated once.
        """
        if copies is None:
            copies = {}

        if source is None:
            return None

        if source.__tablename__ + str(source.id) in copies:
            return copies[source.__tablename__ + str(source.id)]
        else:
            new_object = type(source)()
            copies[source.__tablename__ + str(source.id)] = new_object

        for prop in object_mapper(source).iterate_properties:
        #            if isinstance(source, (Dataset, Method)):
        #                test = 1

            if (isinstance(prop, ColumnProperty) or isinstance(prop, RelationshipProperty) and prop.secondary is not None)\
            and not prop.key == "id":
                setattr(new_object, prop.key, getattr(source, prop.key))
            elif isinstance(prop, RelationshipProperty):
                if isinstance(getattr(source, prop.key), list):
                    items = []
                    for item in getattr(source, prop.key):
                        items.append(self._clone_model(item, parent=source, copies=copies))
                    setattr(new_object, prop.key, items)
                else:
                    setattr(new_object, prop.key, self._clone_model(getattr(source, prop.key), parent=source, copies=copies))

        if hasattr(new_object, "id"):
            new_object.id = None

        return new_object

    def _get_messages(self):
        """
        Find and return all messages added using self.request.session.flash('<message>', '<message type>')

        :return: All flash messages that need to be displayed.
        """
        return {'error_messages': self.request.session.pop_flash("error"),
                'success_messages': self.request.session.pop_flash("success"),
                'warning_messages': self.request.session.pop_flash("warning")
        }

    def _create_response(self, **kwargs):
        """
        Abstract the repetitive task of rendering schemas and attributes into the output HTML.

        This also provides 1 location to place default rendering options such as that page help should be hidden.

        :param kwargs: Optional arguments to pass to the rendered form, most arguments will be standard and just
        override the defaults.

        :return: Rendered HTML form ready for display.
        """
        response_dict = {
            "page_title": kwargs.pop("page_title", self.find_page_title()),
            'messages': kwargs.pop('messages', self._get_messages()),
            "page_help": kwargs.pop("page_help", ""),
            "user": self.request.user,
            "page_help_hidden": kwargs.pop("page_help_hidden", True),
            "lock_id": self.lock_id,
            "display_leave_confirmation": kwargs.pop("display_leave_confirmation", False),
        }

        response_dict.update(kwargs)
        return response_dict

    def _save_form(self, appstruct=None, model_id=None, model_type=None):
        """
        Abstracts functionality of saving form pages that is reusable for all project pages.
        - If the model doesn't have an ID it inserts a new row in the database.
        - If the model does have an ID it updates the current database row.
        - If the data returned results in no change (or is empty), nothing is saved.
        """

        if appstruct is None:
            appstruct = self._get_post_appstruct()
        if model_type is None:
            model_type = self.model_type

            if model_type is None:
                return False

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
                    model.date_created = datetime.now().date()
                    model.create_by = self.request.user.id
                else:
                    return
            else:
                raise ValueError("No project found for the given project id(" + str(model_id) + "), please do not directly edit the address bar.")

        else:
            # Update the model with all fields in the data
            if model.update(appstruct):
                self.session.merge(model)
                changed = True

        self._model = model

        if changed:
            model.date_modified = datetime.datetime.now().date()
            model.last_modified_by = self.request.user.id

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

    def _handle_form(self, dont_touch=False, model_id=None, model_type=None):
        """
        Abstract saving and internal redirects to save the referring page correctly.

        :return: If the current page was redirected to for the purpose of saving.
        """
        if self.request.method == 'POST' and len(self.request.POST) > 0:
            if model_type is None:
                model_type = self.model_type

            # If this is a sub-request called just to save.
            matched_route = self.request.matched_route
            if self.request.referrer == self.request.path_url:
                if (
                    (matched_route == "user" and
                     has_permission(DefaultPermissions.ADMINISTRATOR, self.context, self.request)) or
                    (matched_route == "manage_dataset" and
                     has_permission(DefaultPermissions.EDIT_INGESTERS, self.context, self.request)) or
                    (matched_route == "manage_data" and
                     has_permission(DefaultPermissions.EDIT_DATA, self.context, self.request)) or
                    (matched_route == "permissions" and
                     has_permission(DefaultPermissions.EDIT_SHARE_PERMISSIONS, self.context, self.request)) or
                    (matched_route == "data" and
                     has_permission(DefaultPermissions.EDIT_DATA, self.context, self.request)) or
                    has_permission(DefaultPermissions.EDIT_PROJECT, self.context, self.request)
                    ):
                    if self._save_form(model_id=model_id, model_type=model_type):
                        self._form_changed = True

                        if model_type == Project:
                            if not dont_touch:
                                self._touch_page()
                            self.project.validated = False

                        if matched_route.name == "datasets" or matched_route.name == "methods":
                            # Indicate that the datasets changed.
                            if self.project.datasets_ready is None:
                                self.project.datasets_ready = 0
                            else:
                                self.project.datasets_ready += 1
                    else:
                        self._form_changed = False

                    # If this view has been called for saving only, return without rendering.
                    view_name = inspect.stack()[1][3][:-5]
                    if self.request.matched_route.name != view_name:
                        return True
                else:
                    raise HTTPForbidden("You do not have permission to save this data.  Page being saved is %s" % self.title)
            else:
                self._redirect_to_target(self.request.referrer)

            return False

    def _get_post_appstruct(self):
        """
        Convert the request.POST variables into a Deform appstruct, storing any validation errors.

        :return: Deform appstruct as found from the request.POST variables.
        """
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

    def _render_validated_model(self, appstruct=None):
        try:
            if appstruct is None:
                return
            self.render_appstruct = self.form.validate_pstruct(appstruct)
            display = self.form.render(self.render_appstruct, readonly=self._readonly)
        except ValidationFailure, e:
            self.render_appstruct = e.cstruct
            display = e.render()

        return display

    def _render_unvalidated_mode(self, appstruct=None):
        try:
            if appstruct is None:
                return None
            return self.form.render(appstruct, readonly=self._readonly)
        except Exception, e:
            logger.exception("Couldn't display untouched form without validating.")

        return None

    def _render_post(self, **kw):
        """
        Render the form using the data/appstruct from the request.POST variables.
        """
        if self._get_post_appstruct() is not None:
            if hasattr(self, '_validation_error'):
                return self._validation_error.render()
            else:
                return self.form.render(self._get_post_appstruct(), **kw)

        return None


    @view_config(renderer="../templates/dashboard.pt", route_name="dashboard")
    def dashboard_view(self):
        """
        NOT YET IMPLEMENTED
        Dashboard page, this is mainly just rendering a static template.

        :return: Rendered HTML form ready for display.
        """
        page_help = "" # TODO: Video or picture slider.
#        self.request.session.flash("This page is still under development.", "warning")

        return self._create_response(page_help=page_help)


    @view_config(renderer="../templates/administrator.pt", route_name="admin",
        permission=DefaultPermissions.ADMINISTRATOR)
    def admin_view(self):
        """
        NOT YET IMPLEMENTED

        Administration page that allows setting up and configuring:
         - user permissions and roles
         - Templates
         - Standardised fields.

        :return: Rendered HTML form ready for display.
        """
        self.request.session.flash("This page is still under development.", "warning")
    #        raise NotImplementedError("Search hasn't been implemented yet!")

        return self._create_response()

    @view_config(renderer="../templates/help.pt", route_name="help")
    def help_view(self):
        """
        NOT YET IMPLEMENTED
        Help page that provides an overview, contact form and links to additonal help.

        :return: Rendered HTML form ready for display.
        """

        admin_role_id = self.session.query(Role.id).filter_by(name=DefaultRoles.ADMIN[0]).first()[0]
        admins = self.session.query(User).join(user_roles_table).filter(Role.id==admin_role_id).all()
        admin_contact = [(admin.display_name, admin.email, admin.phone) for admin in admins]

        data = {
            'email': self.request.POST.get('email', '').strip(' '),
            'subject': self.request.POST.get('subject', '').strip(' '),
            'message': self.request.POST.get('message', '').strip(' '),
        }
        if 'Send' in self.request.POST:
            recipients = [admin.email for admin in admins]

            try:
                mailer = get_mailer(self.request)
                message = Message(subject=data['subject'], sender=data['email'], recipients=recipients, body=data['message'])
                mailer.send(message)
                self.request.session.flash("Message sent successfully.", "success")
            except Exception as e:
                self.request.session.flash("Failed to send email message: %s" % e, "error")

        return self._create_response(data=data, admins=admin_contact)

    @view_config(route_name="record_data")
    def record_data_view(self):
        """
        Persistent view to provide metadata records and external systems with a consistent URL and implementing a simple
        redirect to the actual data view page.

        :return: Page redirect respons or the results of the internally redirected page.
        """
        metadata_id = self.request.matchdict['metadata_id']
        if metadata_id is None or not isnumeric(metadata_id):
            raise ValueError("You are trying to view data associated with a metadata record with an invalid identifier - you have probably manually entered an invalid website address.")

        metadata = self.session.query(Metadata).filter_by(id=metadata_id).first()
        if metadata is None:
            raise ValueError("Record does not exist!")

        if metadata.dataset_id is not None:
            dataset = self.session.query(Dataset).filter_by(id=metadata.dataset_id).first()
            self.request.session.flash("Click on the Browse Data contextual option to access data.", "success")
            return HTTPFound(self.request.route_url("dataset", project_id=dataset.project_id, dataset_id=dataset.id))
        else:
            self.request.session.flash("Project records don't have data directly associated with them, please use the browse datasets contextual option to access data from related datasets.", "success")
            return HTTPFound(self.request.route_url("general", project_id=metadata.project_id))
#            return self._redirect_to_target(self.request.route_url("general", project_id=metadata.project_id))


    @view_config(route_name='user', renderer='../templates/form.pt', permission=DefaultPermissions.ADMINISTRATOR)
    def user_view(self):
        page_help = ""
        schema = convert_schema(SQLAlchemyMapping(User, unknown='raise', ca_description=""), restrict_admin=not has_permission(DefaultPermissions.ADVANCED_FIELDS, self.context, self.request).boolval).bind(request=self.request)
        self.form = Form(schema, action=self.request.route_url(self.request.matched_route.name), buttons=('Save', ), )

        password_changed = False
        if self.request.POST and self.request.user._password != self.request.POST.get('user:password', self.request.user._password):
           password_changed = True

        # If this page was only called for saving and a rendered response isn't needed, return now.
        if self._handle_form(model_id=self.request.user.id, model_type=User):
            return

        # Fix the password from plain text to hashed.
        user = self.session.query(User).filter_by(id=self.request.user.id).first() # self.request.user is detached from db
        if password_changed:
            user.password = user._password

        self._readonly = not has_permission(DefaultPermissions.ADMINISTRATOR, self.context, self.request).boolval
        appstruct = user.dictify()
        display = self._render_validated_model(appstruct)

        return self._create_response(page_help=page_help, form=display)


    @forbidden_view_config(renderer='../templates/form.pt')
    @view_config(route_name='login', renderer='../templates/form.pt')
    def login_view(self):
        """
        Login page that allows users to login either using Shibboleth or local users added directly to the database.

        :return: Rendered HTML form ready for display.
        """
        logged_in = authenticated_userid(self.request)

        if isinstance(self.context, HTTPForbidden):
            if self.request.user is None:
                self.request.session.flash("You are unauthorised to view the requested page, please login first.", "warning")
            elif "project_id" in self.request.matchdict :
                self.request.session.flash("You don't have permission to view the requested page, please request permission from the project creator or administrators.", "warning")
            else:
                self.request.session.flash("You don't have permission to view the requested page, please request permission from the administrators.", "warning")
        schema = Login()
        schema['shibboleth_login'].children[0].request = self.request
        form = Form(schema, action=self.request.route_url("login"), buttons=('Login', ))

        login_url = self.request.route_url('login')
        referrer = self.request.referrer
        if referrer == login_url or referrer == "":
            referrer = self.request.route_url("dashboard") # never use the login form itself as came_from
        came_from = self.request.params.get('came_from', referrer)
        login = ''
        password = ''
        if 'Login' in self.request.params:
            login = self.request.params['user_name']
            password = self.request.params['password']
            user = User.get_user(username=login)
            if user and user.validate_password(password):
                headers = remember(self.request, user.id)
                self.request.session.flash('Logged in successfully.', 'success', )
                return HTTPFound(location=came_from,
                    headers=headers)

            self.request.session.flash('Authentication Failed.', 'error', )
            try:
                appstruct = form.validate(self.request.POST.items())
                display = form.render(appstruct)
            except Exception, e:
                appstruct = e.cstruct
                display = e.render()
        else:
            display = form.render({"came_from": came_from})

        return self._create_response(url=self.request.application_url + '/login', came_from=came_from,
            login=login, password=password, form=display)

    @view_config(route_name='login_shibboleth', renderer='../templates/form.pt')
    def login_shibboleth(self):
        """
        Shibboleth login page that reads headers added by Shibboleth.  If the user doesn't already exist they are added
        to the database.

        :return: Rendered HTML form ready for display.
        """
        request = self.request
        logged_in = authenticated_userid(self.request)

        login_url = self.request.route_url('login_shibboleth')
        referrer = self.request.url
        if referrer == login_url:
            referrer = '/' # never use the login form itself as came_from
        came_from = self.request.params.get('came_from', referrer)

        try:
            common_name = self.request.headers['commonName']
            first_name = self.request.headers['givenName']
            surname = self.request.headers['surname']
            email = self.request.headers['email']
            identifier = self.request.headers['auEduPersonSharedToken']
        except KeyError as e:
            return HTTPClientError("Missing Shibboleth headers")

        user = User.get_user(username=identifier, auth_type="shibboleth")
        if not user:
            # Create the user
            logger.info("Adding: %s %s %s" % (first_name, surname, email))
            user = User(common_name, identifier, "", email, auth_type="shibboleth")
            self.session.add(user)
            self.session.flush()

        headers = remember(self.request, user.id)

        return HTTPFound(location=came_from, headers=headers)

    @view_config(route_name='logout')
    def logout(self):
        """
        When visited this view removes the user authentication and redirects to the dashboard.

        Shibboleth users have to close their browser before they fully log out, this has to do with how Shibboleth works
        and the complexity of single login systems.

        :return: External redirect to the dashboard.
        """
        if self.request.user is not None:
            self.request.session.flash("You have been successfully logged out.", "success")
            if self.request.user is not None and self.request.user.auth_type == "shibboleth":
                    self.request.session.flash("To fully log out of Shibboleth you must close your browser (eg. Firefox, Chrome or Internet Explorer, not just this tab/window).", "warning")
        else:
            self.request.session.flash("You were already logged out.", "success")

        headers = forget(self.request)

        return HTTPFound(self.request.referrer,
            headers=headers)

    @view_config(context=Exception, renderer="../templates/exception.pt")
    def exception_view(self):
        """
        Handles all exceptions that aren't caught by another exception view.

        :return: Rendered view showing the exception message.
        """
        logger.exception("An exception occurred in global exception view: %s", self.context)

        self.request.session.flash('An exception has occurred - please try again.', 'error_messages')
        return self._create_response(page_title="Exception Has Occurred", exception="%s" % self.context)


    @view_config(context=HTTPNotFound, renderer="../templates/exception.pt")
    def http_not_found_view(self):
        """
        Exception view for when the user tries to access a url that doesn't exist, this displays an error message and
        redirects to the dashboard page.

        :return: Redirect to the dashboard page.
        """

        self.request.session.flash(
            'There is no page at the requested address (%s), please don\'t edit the address bar directly.' % self.request.path_url, 'error')
        return HTTPFound(self.request.route_url('dashboard'))

    @view_config(context=HTTPClientError, renderer="../templates/exception.pt")
    def http_error_view(self):
        """
        Exception view errors that the standard exception view doesn't catch.

        :return: Redirect to the dashboard page and display an error message.
        """

        self.request.session.flash(self.context, 'error')
        return HTTPFound(self.request.route_url('dashboard'))


