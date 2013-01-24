import ConfigParser
import logging
import urllib2
import sqlalchemy
from pyramid.httpexceptions import HTTPNotFound, HTTPFound
from pyramid.view import view_config

__author__ = 'Casey Bajema'
from pyramid.renderers import get_renderer
from pyramid.decorator import reify

logger = logging.getLogger(__name__)

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

    @view_config(renderer="../templates/dashboard.pt", route_name="dashboard")
    def dashboard_view(self):

        messages = {
            'error_messages': self.request.session.pop_flash("error"),
            'success_messages': self.request.session.pop_flash("success"),
            'warning_messages': self.request.session.pop_flash("warning")
        }
        return {"page_title": "Provisioning Dashboard", 'messages' : messages}




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
        return {"exception": "%s" % self.context, "message": 'Sorry, we are currently experiencing difficulties.  Please contact the administrators: ' + str(self.context)}
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
