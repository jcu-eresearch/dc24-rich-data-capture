"""
Views that provide data looked up from mint as JSON for local AJAX usage.
"""

import ConfigParser
import json
import urllib
import urllib2
import colander
import sys
import jcudc24provisioning
from pyramid.view import view_config, view_defaults
from pyramid_debugtoolbar.utils import logger

__author__ = 'Casey Bajema'


@view_defaults(renderer="../templates/search_template.pt")
class MintLookup(object):
    """
    Provides searching of the Mint (Name authority associated with ReDBox) for use with AJAX based templates.
    """

    def __init__(self, request):
        self.request = request

        # Read the Fields of research from Mint and store it into a variable for the template to read
#        config = sys.argv
        config = jcudc24provisioning.global_settings
        if 'mint.location' in config:
            try:
                self.mint_url = config.get('mint.location')
            except ConfigParser.NoSectionError or ConfigParser.NoOptionError:
                raise ValueError("Invalid Mint server configuration in defaults.cfg")
        else:
            raise ValueError("No Mint server configuration in defaults.cfg")

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

        if self.mint_url:
            url_template = self.mint_url + "Activities/opensearch/lookup?count=30&searchTerms=%(search)s"

            data = urllib2.urlopen(url_template % dict(search=urllib.quote_plus(search_terms)))
            result_object = json.loads(data.read(), strict=False)

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

        if self.mint_url:
            url_template = self.mint_url + "Parties_People/opensearch/lookup?count=30&searchTerms=%(search)s"

            data = urllib2.urlopen(url_template % dict(search=urllib.quote_plus(search_terms)))
            result_object = json.loads(data.read(), strict=False)

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

        if self.mint_url:
            url_template = self.mint_url + "default/opensearch/lookup?count=1&searchTerms=dc_identifier:%(search)s"

            data = urllib2.urlopen(url_template % dict(search=urllib.quote_plus(identifier)))
            result_object = json.loads(data.read(), strict=False)


            if len(result_object['results']) <= 0:
                if hasattr(self.request, 'matchdict'):
                    return {'values': ''}
                return None

            if hasattr(self.request, 'matchdict'):
                return {'values': json.dumps(result_object['results'][0])}


            return result_object['results'][0]



