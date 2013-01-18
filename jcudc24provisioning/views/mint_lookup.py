import ConfigParser
import json
import urllib
import urllib2
from pyramid.view import view_config, view_defaults
from pyramid_debugtoolbar.utils import logger

__author__ = 'Casey Bajema'


@view_defaults(renderer="../templates/search_template.pt")
class MintLookup(object):
    def __init__(self, request):
        self.request = request

        # Read the Fields of research from Mint and store it into a variable for the template to read
        config = ConfigParser.ConfigParser()
        if 'defaults.cfg' in config.read('defaults.cfg'):
            try:
                self.mint_url = config.get('mint', 'location')
            except ConfigParser.NoSectionError or ConfigParser.NoOptionError:
                raise ValueError("Invalid Mint server configuration in defaults.cfg")
        else:
            raise ValueError("No Mint server configuration in defaults.cfg")

    @view_config(route_name="get_activities")
    def get_grants(self):
        assert 'search_terms' in self.request.matchdict, "Error: Trying to lookup grant/activities data from Mint without a search term."
        search_terms = self.request.matchdict['search_terms']

        if self.mint_url:
            url_template = self.mint_url + "Activities/opensearch/lookup?count=999&searchTerms=%(search)s"

            data = urllib2.urlopen(url_template % dict(search=urllib.quote_plus(search_terms)))
            result_object = json.loads(data.read(), strict=False)

            grants = []

            for result in result_object['results']:
                grants.append({'label': str(result['dc:title']), 'value': str(result['dc:identifier'])})

            grants = json.dumps(grants)
            return {'values': grants}

    @view_config(route_name="get_parties")
    def get_parties(self):
        assert 'search_terms' in self.request.matchdict, "Error: Trying to lookup people/parties from Mint without a search term."
        search_terms = self.request.matchdict['search_terms']

        if self.mint_url:
            url_template = self.mint_url + "Parties_People/opensearch/lookup?count=999&searchTerms=%(search)s"

            data = urllib2.urlopen(url_template % dict(search=urllib.quote_plus(search_terms)))
            result_object = json.loads(data.read(), strict=False)

            grants = []

            for result in result_object['results']:
                name = str(result['result-metadata']['all']['Honorific'][0]) + " " + str(result['result-metadata']['all']['Given_Name'][0]) \
                            + " " + str(result['result-metadata']['all']['Family_Name'][0])
                grants.append({'label': name, 'value': str(result['dc:identifier'])})

            grants = json.dumps(grants)
            return {'values': grants}

    def get_from_identifier(self, identifier):
#        assert 'identifier' in self.request.matchdict, "Error: Trying to lookup people/parties from Mint without a search term."
#        identifier = self.request.matchdict['identifier']

        if self.mint_url:
            url_template = self.mint_url + "default/opensearch/lookup?count=999&searchTerms=dc_identifier:%(search)s"

            data = urllib2.urlopen(url_template % dict(search=urllib.quote_plus(identifier)))
            result_object = json.loads(data.read(), strict=False)

            result = result_object['results'][0]

            return result

