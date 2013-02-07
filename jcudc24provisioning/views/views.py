import ConfigParser
import logging
from string import split
import urllib2
import sqlalchemy
from pyramid.httpexceptions import HTTPNotFound, HTTPFound
from pyramid.view import view_config

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
]

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
