import ConfigParser
import json
import urllib
import urllib2
from pyramid.view import view_config
from pyramid_debugtoolbar.utils import logger

__author__ = 'Casey Bajema'

@view_config(renderer="../templates/search_template.pt", route_name="get_activities")
def get_grants(request):
    if 'search_terms' in request.matchdict:
        search_terms = request.matchdict['search_terms']

    # Read the Fields of research from Mint and store it into a variable for the template to read
    config = ConfigParser.ConfigParser()
    if 'defaults.cfg' in config.read('defaults.cfg'):
        try:
            mint_url = config.get('mint', 'location')
        except ConfigParser.NoSectionError or ConfigParser.NoOptionError:
            logger.error("Invalid mint configuration in defaults.cfg")

        url_template = mint_url + "Activities/opensearch/lookup?count=999&searchTerms=%(search)s"

        data = urllib2.urlopen(url_template % dict(search=urllib.quote_plus(search_terms)))
        result_object = json.loads(data.read(), strict=False)

        grants = []

        for result in result_object['results']:
            grants.append({'label': str(result['dc:title'])})#, 'value': str(result['dc:title'])})

        grants = json.dumps(grants)

        return {'values': grants}

    else:
        logger.error("defaults.cfg file not found")

@view_config(renderer="../templates/search_template.pt", route_name="get_parties")
def get_grants(request):
    if 'search_terms' in request.matchdict:
        search_terms = request.matchdict['search_terms']

    # Read the Fields of research from Mint and store it into a variable for the template to read
    config = ConfigParser.ConfigParser()
    if 'defaults.cfg' in config.read('defaults.cfg'):
        try:
            mint_url = config.get('mint', 'location')
        except ConfigParser.NoSectionError or ConfigParser.NoOptionError:
            logger.error("Invalid mint configuration in defaults.cfg")

        url_template = mint_url + "Parties_People/opensearch/lookup?count=999&searchTerms=%(search)s"

        data = urllib2.urlopen(url_template % dict(search=urllib.quote_plus(search_terms)))
        result_object = json.loads(data.read(), strict=False)

        grants = []

        for result in result_object['results']:
            grants.append({'label': str(result['dc:title'])})#, 'value': str(result['dc:title'])})

        grants = json.dumps(grants)

        return {'values': grants}

    else:
        logger.error("defaults.cfg file not found")