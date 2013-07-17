"""
Views that provide data looked up from mint as JSON for local AJAX usage.
"""

import ConfigParser
import json
import urllib
import urllib2
import colander
import os
import jcudc24provisioning
from pyramid.view import view_config, view_defaults
import logging

logger = logging.getLogger(__name__)

__author__ = 'Casey Bajema'


class MintHttp(object):
    """
    An implementation of a Mint Client that connects via HTTP
    """
    
    def __init__(self, mint_url):
        if mint_url == None: raise ValueError("No valid Mint URL provided")
        self.mint_url = mint_url
        
    def get_grants(self, search_terms):
        url_template = self.mint_url + "Activities/opensearch/lookup?count=30&searchTerms=%(search)s"

        data = urllib2.urlopen(url_template % dict(search=urllib.quote_plus(search_terms)))
        return json.loads(data.read(), strict=False)

    def get_parties(self, search_terms):
        url_template = self.mint_url + "Parties_People/opensearch/lookup?count=30&searchTerms=%(search)s"

        data = urllib2.urlopen(url_template % dict(search=urllib.quote_plus(search_terms)))
        return json.loads(data.read(), strict=False)
    
    def get_from_identifier(self, identifier):
        url_template = self.mint_url + "default/opensearch/lookup?count=1&searchTerms=dc_identifier:%(search)s"

        data = urllib2.urlopen(url_template % dict(search=urllib.quote_plus(identifier)))
        return json.loads(data.read(), strict=False)

class MintMock(object):
    """
    An implementation of a Mint Client that connects via HTTP
    """
    
    def __init__(self, mock_file):
        if mock_file == None: raise ValueError("No valid Mint URL provided")
        if not os.path.exists(mock_file): raise ValueError("Mock file doesn't exist: " + mock_file)
        with open(mock_file) as f:
            self.data = json.load(f)
            
        if "grants" not in self.data: self.data["grants"] = []
        if "parties" not in self.data: self.data["parties"] = []
        
    def _make_results(self, results):
        return {"OpenSearchResponse": {
                "title": "Generic Search",
                "link": "",
                "totalResults": "14635",
                "startIndex" : "0",
                "itemsPerPage": "25",
                "query": {
                    "role": "request",
                    "searchTerms": "",
                    "startPage": "0"
                }
            },
            "namespaces": {
                "dc": "http://purl.org/dc/terms",
                "owl": "http://www.w3.org/2002/07/owl#",
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
            },
            "results": results}
        
    def get_grants(self, search_terms):
        return self._make_results(list(self.data["grants"]))

    def get_parties(self, search_terms):
        return self._make_results(list(self.data["parties"]))
    
    def get_from_identifier(self, identifier):
        res = self._make_results([r for r in self.data["parties"] if identifier == r["dc:identifier"] ] + \
                                   [r for r in self.data["grants"] if identifier == r["dc:identifier"] ] )
        return res

def mint_factory(config):
    """
    Returns a Mint connection object based on the configuration setting
    """
    if 'mint.location' in config:
        # Use a normal HTTP connection to a Mint server
        try:
            return MintHttp(config.get('mint.location'))
        except ConfigParser.NoSectionError or ConfigParser.NoOptionError:
            raise ValueError("Invalid Mint server configuration in defaults.cfg")
    elif 'mint.mock_file' in config:
        # Make a mock Mint server using the values in the provided file
        return MintMock(config.get('mint.mock_file'))
    else:
        raise ValueError("No Mint server configuration in defaults.cfg")
    

@view_defaults(renderer="../templates/search_template.pt")
class MintLookup(object):
    """
    Provides searching of the Mint (Name authority associated with ReDBox) for use with AJAX based templates.
    """

    def __init__(self, request):
        self.request = request

        # Read the Fields of research from Mint and store it into a variable for the template to read
#        config = sys.argv
        self.mint = mint_factory(jcudc24provisioning.global_settings)

    @view_config(route_name="get_activities")
    def get_grants(self, search_terms=None):
        """
        Outputs the grants found in Mint as JSON.

        :param search_terms: Text to search grants for.
        :return: Found grants as JSON to be rendered.
        """

        assert search_terms is not None or 'search_terms' in self.request.matchdict, "Error: Trying to lookup grant/activities data from Mint without a search term."
        if search_terms is None:
            search_terms = self.request.matchdict['search_terms']

        result_object = self.mint.get_grants(search_terms)

        grants = []

        for result in result_object['results']:
            grants.append({
                'label': str(result['dc:title']),
                'value': str(result['dc:identifier']),
                'about': str(result['rdf:about'])
            })

        grants = json.dumps(grants)
        return {'values': grants}

    @view_config(route_name="get_parties")
    def get_parties(self, search_terms=None):
        """
        Outputs the parties found in Mint as JSON.

        :param search_terms: Text to search parties for.
        :return: Found parties as JSON to be rendered.
        """

        assert search_terms is not None or 'search_terms' in self.request.matchdict, "Error: Trying to lookup people/parties from Mint without a search term."
        if search_terms is None:
            search_terms = self.request.matchdict['search_terms']

        result_object = self.mint.get_parties(search_terms)
        
        grants = []

        for result in result_object['results']:
            name = str(result['result-metadata']['all']['Honorific'][0]) + " " + str(result['result-metadata']['all']['Given_Name'][0]) \
                        + " " + str(result['result-metadata']['all']['Family_Name'][0])
            grants.append({
                'label': name,
                'value': str(result['dc:identifier']),
                'about': str(result['rdf:about'])
            })

        grants = json.dumps(grants)
        return {'values': grants}

    @view_config(route_name="get_from_identifier")
    def get_from_identifier(self, identifier=None):
        """
        Outputs the items found in Mint as JSON.

        :param search_terms: Unique identifier to search Mint with.
        :return: Found items as JSON to be rendered.
        """

        if identifier is None and hasattr(self.request, 'matchdict'):
            assert 'identifier' in self.request.matchdict, "Error: Trying to lookup people/parties from Mint without a search term."
            identifier = self.request.matchdict['identifier']

        if identifier is None or identifier is colander.null or len(str(identifier)) <= 0:
            if hasattr(self.request, 'matchdict'):
                return {'values': ''}
            return None

        result_object = self.mint.get_from_identifier(identifier)


        if len(result_object['results']) <= 0:
            if hasattr(self.request, 'matchdict'):
                return {'values': ''}
            return None

        if hasattr(self.request, 'matchdict'):
            return {'values': json.dumps(result_object['results'][0])}

        return result_object['results'][0]



