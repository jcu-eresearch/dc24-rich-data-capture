import json
from pyramid.response import Response
from jcudc24provisioning.views.schemas.metadata_schema import MetadataData
from jcudc24provisioning.views.workflow.workflows import Workflows
from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.view import view_config
import urllib2

__author__ = 'Casey Bajema'

class MetadataView(Workflows):
    title = "Get Mint Users"

    def __init__(self, request):
        self.request = request

    @view_config(renderer="../../templates/get_mint_users.pt", name="mint_users.xml")
    def metadata_view(self):
        request_data = self.request.POST.items()
        print request_data
        queryString = ""

        for key, value in request_data:
            queryString += key + "=" + value

        url_template = 'http://tdh-ms-dev.hpc.jcu.edu.au:9001/solr/fascinator/select?%(query)s'
        url = url_template % dict(query=queryString)
        result = ""
        print url
        data = urllib2.urlopen(url).read()
        print data

        return {"page_title": 'Mint Users', "values": data}

