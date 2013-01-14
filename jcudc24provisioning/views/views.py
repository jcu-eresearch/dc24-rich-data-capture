import ConfigParser
import urllib2
from pyramid.view import view_config

__author__ = 'Casey Bajema'
from pyramid.renderers import get_renderer
from pyramid.decorator import reify


class Layouts(object):
    def __init__(self, request):
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
        return {"page_title": "Provisioning Dashboard", 'messages' : None}
