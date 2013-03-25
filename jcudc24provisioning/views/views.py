import ConfigParser
import logging
from string import split
import urllib2
import pyramid
from pyramid.httpexceptions import HTTPNotFound, HTTPFound, HTTPClientError
from pyramid.view import view_config, forbidden_view_config, view_defaults
from pyramid.security import remember, forget, authenticated_userid
from deform.form import Form
from jcudc24provisioning.models.website import Login, User
from jcudc24provisioning.models import DBSession


__author__ = 'Casey Bajema'
from pyramid.renderers import get_renderer
from pyramid.decorator import reify

logger = logging.getLogger(__name__)

PAGES = [
        {'route_name': 'dashboard', 'title': 'Home', 'page_title': 'JCU TDH DC24 Dashboard', 'hidden': False},
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

    @reify
    def global_template(self):
        renderer = get_renderer("../templates/template.pt")
        return renderer.implementation().macros['layout']

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

        raise ValueError("There is no page title for this address: " + str(self.request.url))

    @view_config(renderer="../templates/dashboard.pt", route_name="dashboard")
    def dashboard_view(self):

        messages = {
            'error_messages': self.request.session.pop_flash("error"),
            'success_messages': self.request.session.pop_flash("success"),
            'warning_messages': self.request.session.pop_flash("warning")
        }
        return {"page_title": "Provisioning Dashboard", 'messages': messages}

    @view_config(renderer="../templates/dashboard.pt", route_name="search")
    def search_page_view(self):
        raise NotImplementedError("Search hasn't been implemented yet!")

        messages = {
            'error_messages': self.request.session.pop_flash("error"),
            'success_messages': self.request.session.pop_flash("success"),
            'warning_messages': self.request.session.pop_flash("warning")
        }
        return {"page_title": "Provisioning Dashboard", 'messages': messages}



    @view_config(route_name='login', renderer='../templates/form.pt')
    @forbidden_view_config(renderer='../templates/form.pt')
    def login(self):
        request = self.request
        logged_in = authenticated_userid(self.request)

        form = Form(Login(), action=self.request.route_url("login"), buttons=('Login', ))

        login_url = self.request.resource_url(self.request.context, 'login')
        referrer = self.request.url
        if referrer == login_url:
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
                self.request.session.flash('Logged in successfully.', 'success',)
                return HTTPFound(location = came_from,
                                 headers = headers)

            self.request.session.flash('Authentication Failed.', 'error',)
            try:
                appstruct = form.validate(self.request.POST.items())
                display = form.render(appstruct)
            except Exception, e:
                appstruct = e.cstruct
                display = e.render()
        else:
            display = form.render({'came_from': came_from})


        messages = {
                    'error_messages': self.request.session.pop_flash("error"),
                    'success_messages': self.request.session.pop_flash("success"),
                    'warning_messages': self.request.session.pop_flash("warning")
                }

        return dict(
                page_title="Login",
                messages = messages,
                url = self.request.application_url + '/login',
                came_from = came_from,
                login = login,
                password = password,
                form=display
            )

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
            logger.info("Adding: %s %s %s"%(first_name, surname, email))
            user = User(common_name, identifier, "", email, auth_type="shibboleth")
            session = DBSession()
            session.add(user)
            session.flush()

        headers = remember(self.request, user.id)

        return HTTPFound(location = came_from, headers = headers)

    @view_config(route_name='logout')
    def logout(self):
        headers = forget(self.request)
        return HTTPFound(location = self.request.resource_url(self.request.context),
                         headers = headers)


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
        messages = {
            'error_messages': ['Sorry, we are currently experiencing difficulties.'],
            'success_messages': [],
            'warning_messages': []
        }
        return {"exception": "%s" % self.context, "messages": messages}
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
            self.request.session.flash('There is no page at the requested address, please don\'t edit the address bar directly.', 'error')
            return HTTPFound(self.request.route_url('dashboard'))
