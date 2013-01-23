import ConfigParser
import copy
import json
import urllib
import urllib2
import colander
from colanderalchemy.types import SQLAlchemyMapping
from jcudc24provisioning.models.project import DBSession
from pyramid.view import view_config, view_defaults
from jcudc24provisioning.views.ca_scripts import convert_sqlalchemy_model_to_data, convert_schema, create_sqlalchemy_model
from jcudc24provisioning.models.project import *
import transaction

__author__ = 'Casey Bajema'


@view_defaults(renderer="../templates/search_template.pt")
class Search(object):
    def __init__(self, request):
        self.request = request
        self.session = DBSession

        # Read the Fields of research from Mint and store it into a variable for the template to read
        config = ConfigParser.ConfigParser()
        if 'defaults.cfg' in config.read('defaults.cfg'):
            try:
                self.mint_url = config.get('mint', 'location')
            except ConfigParser.NoSectionError or ConfigParser.NoOptionError:
                raise ValueError("Invalid Mint server configuration in defaults.cfg")
        else:
            raise ValueError("No Mint server configuration in defaults.cfg")

    @view_config(route_name="get_model")
    def get_model(self):
        assert 'object_type' in self.request.matchdict and issubclass(eval(self.request.matchdict['object_type']),Base), "Error: Trying to lookup database with invalid type."
        assert 'id' in self.request.matchdict, "Error: Trying to lookup " + self.request.matchdict['object_type'] +" data from database without an id."
        object_type = eval(self.request.matchdict['object_type'])
        object_id = self.request.matchdict['id']

        model = self.session.query(object_type).filter_by(id=object_id).first()
        print model

        if model:
            data = convert_sqlalchemy_model_to_data(model, convert_schema(SQLAlchemyMapping(object_type, unknown='raise', ca_description=""), page='setup'))

            json_data = json.dumps(data)
            return {'values': json_data}






