import ConfigParser
import logging
from string import split
import urllib2
from jcudc24provisioning.controllers.authentication import DefaultPermissions
from jcudc24provisioning.models.ca_model import CAModel
from jcudc24provisioning.models.project import Metadata
import pyramid
from pyramid.httpexceptions import HTTPNotFound, HTTPFound, HTTPClientError, HTTPBadRequest, HTTPForbidden
from pyramid.interfaces import IRoutesMapper, IViewClassifier, IView
from pyramid.view import view_config, forbidden_view_config, view_defaults, render_view_to_response
from pyramid.security import remember, forget, authenticated_userid
from deform.form import Form
from jcudc24provisioning.models.website import Login, User, LocalLogin
from jcudc24provisioning.models import DBSession
from pyramid.request import Request
from zope.interface import providedBy
import deform


__author__ = 'Casey Bajema'
from pyramid.renderers import get_renderer
from pyramid.decorator import reify

logger = logging.getLogger(__name__)

PAGES = [
    {'route_name': 'dashboard', 'title': 'Home', 'page_title': 'EnMaSSE Dashboard', 'hidden': False},
    {'route_name': 'create', 'title': 'New Project', 'page_title': 'Setup a New Project', 'hidden': False},
    {'route_name': 'browse', 'title': 'Browse Projects', 'page_title': 'Browse Projects & Data'},
    {'route_name': 'help', 'title': 'Help & Support', 'page_title': 'Associated Information', 'hidden': False},
    {'route_name': 'search', 'title': 'Search Website', 'page_title': 'Search Website', 'hidden': True},
    {'route_name': 'admin', 'title': 'Administrator', 'page_title': 'Administrator', 'hidden': False},
    {'route_name': 'login', 'title': 'Log in', 'page_title': 'Log in', 'hidden': True},
    {'route_name': 'login_shibboleth', 'title': 'Log in', 'page_title': 'Log in', 'hidden': True},
]

@view_defaults(permission=pyramid.security.NO_PERMISSION_REQUIRED)
class Layouts(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.config = request.registry.settings
        self.session = DBSession

    @reify
    def global_template(self):
        renderer = get_renderer("../templates/template.pt")
        return renderer.implementation().macros['layout']

    @reify
    def get_user(self):
        return self.request.user

    @reify
    def get_message(self):
        return self.request.GET.get('msg')


    @reify
    def metadata_view(self):
        request_data = self.request.POST.items()
        queryString = ""

        for key, value in request_data:
            queryString += key + "=" + value
        config = ConfigParser.ConfigParser()
        config.read("defaults.cfg")
        location = config.get("mint", "solr_api").strip().strip("?/\\")
        url_template = location + '?%(query)s'
        url = url_template % dict(query=queryString)
        result = ""
        data = urllib2.urlopen(url).read()

        return data

    @reify
    def menu(self):
        new_menu = PAGES[:]

        introspector = self.request.registry.introspector
        hidden = []
        for menu in new_menu:
            menu['current'] = menu['route_name'] == self.request.matched_route.name
            request = self.request

            menu_introspector = introspector.get('routes', menu['route_name'])
            if menu_introspector:
                menu['href'] = menu_introspector['pattern']
            else:
                logger.error("Menu item has an invalid route_name: %s" % menu['route_name'])
                raise ValueError("Menu item has an invalid route_name: %s" % menu['route_name'])

            if 'hidden' in menu and menu['hidden'] is True:
                hidden.append(menu)

        for menu in hidden:
            new_menu.remove(menu)

        return new_menu

    @reify
    def is_hidden_menu(self):
        new_menu = PAGES[:]
        url = split(self.request.url, "?")[0]

        for menu in new_menu:
            if url.endswith(menu['href']) and 'hidden' in menu and menu['hidden'] is True:
                return True

        return False

    def find_page_title(self):
        for page in PAGES:
            if page['route_name'] == self.request.matched_route.name:
                return page['page_title']

        return None

    #        raise ValueError("There is no page title for this address: " + str(self.request.url))

    def _redirect_to_target(self, target):
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

        sub_request = Request.blank(path=target, POST=self.request.POST, referrer=self.request.referrer,
            referer=self.request.referer)

        # Add the user object so the subrequest can authenticate.
        sub_request.user = self.request.user

        # Request sorts the post items (which breaks deform) - fix it directly
        if len(self.request.POST) > 0:
            sub_request.POST._items = self.request.POST._items

        return self.request.invoke_subrequest(sub_request)

    #        return render_view_to_response(None, self.request, name=target)

    #        introspector = self.request.registry.introspector
    #        target_callable = introspector.get('views', target)
    #        route_intr = introspector.get('routes', target)

    def _get_messages(self):
        return {'error_messages': self.request.session.pop_flash("error"),
                'success_messages': self.request.session.pop_flash("success"),
                'warning_messages': self.request.session.pop_flash("warning")
        }

    def _create_response(self, **kwargs):
        response_dict = {
            "page_title": kwargs.pop("page_title", self.find_page_title()),
            'messages': kwargs.pop('messages', self._get_messages()),
            "page_help": kwargs.pop("page_help", ""),
            "user": self.request.user,
            "page_help_hidden": kwargs.pop("page_help_hidden", True),
        }

        response_dict.update(kwargs)
        return response_dict


    @view_config(renderer="../templates/dashboard.pt", route_name="dashboard")
    def dashboard_view(self):
        page_help = "TODO: Video or picture slider."
        self.request.session.flash("This page is still under development.", "warning")

        return self._create_response(page_help=page_help)

    @view_config(renderer="../templates/manage_data.pt", route_name="browse")
    def search_page_view(self):
    #        raise NotImplementedError("Search hasn't been implemented yet!")
        self.request.session.flash("This page is still under development.", "warning")

        return self._create_response()

    @view_config(renderer="../templates/administrator.pt", route_name="admin",
        permission=DefaultPermissions.ADMINISTRATOR)
    def admin_page_view(self):
        self.request.session.flash("This page is still under development.", "warning")
    #        raise NotImplementedError("Search hasn't been implemented yet!")

        return self._create_response()

    @view_config(renderer="../templates/help.pt", route_name="help")
    def help_page_view(self):
        self.request.session.flash("This page is still under development.", "warning")
    #        raise NotImplementedError("Search hasn't been implemented yet!")

        return self._create_response()

    @view_config(route_name="record_data")
    def record_data_view(self):
        metadata_id = self.request.matchdict['metadata_id']

        metadata = self.session.query(Metadata).filter_by(id=metadata_id).first()
        if metadata is None:
            raise ValueError("Data cannot be displayed as the provided record ID doesn't exist!")

        if metadata.dataset_id is not None:
            data_url = "" % (self.config['ingesterapi.data_url'],)
            return HTTPFound(location=data_url)
        else:
            self.request.session.flash("Project records don't have data directly associated with them, please use the contextual options to access data from related datasets.", "success")
            return self._redirect_to_target(self.request.route_url("project", project_id=metadata.project_id))


    @forbidden_view_config(renderer='../templates/form.pt')
    @view_config(route_name='login', renderer='../templates/form.pt')
    def login_view(self):
        request = self.request
        logged_in = authenticated_userid(self.request)

        if isinstance(self.context, HTTPForbidden):
            self.request.session.flash("You are unauthorised to view the requested page, please login first.", "warning")

        form = Form(Login(), action=self.request.route_url("login"), buttons=('Login', ))

        login_url = self.request.route_url('login')
        referrer = self.request.url
        if referrer == login_url or referrer == "":
            referrer = '/' # never use the login form itself as came_from
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
        if self.request.user is not None:
            self.request.session.flash("You have been successfully logged out.", "success")
            if self.request.user is not None and self.request.user.auth_type == "shibboleth":
                    self.request.session.flash("To fully log out of Shibboleth you must close your browser (eg. Firefox, Chrome or Internet Explorer, not just this tab/window).", "warning")
        else:
            self.request.session.flash("You were already logged out.", "success")

        headers = forget(self.request)

        return HTTPFound(location=self.request.route_url("dashboard"),
            headers=headers)

    @view_config(context=Exception, renderer="../templates/exception.pt")
    def exception_view(self):
    #        # TODO: Update standard exception screen to fit.
        logger.exception("An exception occurred in global exception view: %s", self.context)
        #        if self.request.route_url:
        #            try:
        #                self.request.session.flash('Sorry, there was an exception, please try again.', 'error')
        #                self.request.session.flash(self.context, 'error')
        #                self.request.POST.clear()
        #                response = getattr(self, str(self.request.route_url) + "_view")()
        #                return response
        #            except Exception:
        #            logger.exception("Exception occurred in standard view: %s", self.context)

        self.request.session.flash('Sorry, we are currently experiencing difficulties.', 'error_messages')
        return self._create_response(page_title="Exception Has Occurred", exception="%s" % self.context)

    #        else:
    #            self.request.session.flash('There is no page at the requested address, please don\'t edit the address bar directly.', 'error')
    #            return HTTPFound(self.request.route_url('dashboard'))

    @view_config(context=HTTPNotFound, renderer="../templates/exception.pt")
    def http_error_view(self):
    #        # TODO: Update standard exception screen to fit.
    #        logger.exception("An exception occurred in global exception view: %s", self.context)
    #        if self.request.route_url:
    #            try:
    #                self.request.session.flash('Sorry, there was an exception, please try again.', 'error')
    #                self.request.session.flash(self.context, 'error')
    #                self.request.POST.clear()
    #                response = getattr(self, str(self.request.route_url) + "_view")()
    #                return response
    #            except Exception:
    #                logger.exception("Exception occurred while trying to display the view without variables: %s", Exception)
    #                return {"page_title": self.request.url, "form": 'Sorry, we are currently experiencing difficulties.  Please contact the administrators: ' + str(self.context), "form_only": False}
    #        else:
        self.request.session.flash(
            'There is no page at the requested address, please don\'t edit the address bar directly.', 'error')
        return HTTPFound(self.request.route_url('dashboard'))

    @view_config(context=HTTPClientError, renderer="../templates/exception.pt")
    def http_error_view(self):
    #        # TODO: Update standard exception screen to fit.
    #        logger.exception("An exception occurred in global exception view: %s", self.context)
    #        if self.request.route_url:
    #            try:
    #                self.request.session.flash('Sorry, there was an exception, please try again.', 'error')
    #                self.request.session.flash(self.context, 'error')
    #                self.request.POST.clear()
    #                response = getattr(self, str(self.request.route_url) + "_view")()
    #                return response
    #            except Exception:
    #                logger.exception("Exception occurred while trying to display the view without variables: %s", Exception)
    #                return {"page_title": self.request.url, "form": 'Sorry, we are currently experiencing difficulties.  Please contact the administrators: ' + str(self.context), "form_only": False}
    #        else:
        self.request.session.flash(self.context, 'error')
        return HTTPFound(self.request.route_url('dashboard'))


