"""
Provides seaching of the provisioning interface database output as JSON for local AJAX usage.
"""

import ConfigParser
import json
from colanderalchemy.types import SQLAlchemyMapping
import jcudc24provisioning
from pyramid.view import view_config, view_defaults
from jcudc24provisioning.controllers.ca_schema_scripts import convert_schema
from jcudc24provisioning.models.project import *
from jcudc24provisioning import services

__author__ = 'Casey Bajema'


@view_defaults(renderer="../templates/search_template.pt")
class Search(object):
    """
    Provides searching of the provisioning interface database for AJAX based templates.
    """
    def __init__(self, request):
        self.request = request
        self.session = DBSession

        # Read the mint_url from the configuration files.
        self.config = jcudc24provisioning.global_settings
        try:
            self.mint_url = self.config['mint.location']
        except ConfigParser.NoSectionError or ConfigParser.NoOptionError:
            raise ValueError("Invalid Mint server configuration in defaults.cfg")

    @view_config(route_name="get_model")
    def get_model(self):
        """
        Find a provisioning interface model based on the provided object_type and id.

        :return: Found model that is dictified and returned as JSON.
        """

        assert 'object_type' in self.request.matchdict and issubclass(eval(self.request.matchdict['object_type']),Base), "Error: Trying to lookup database with invalid type."
        assert 'id' in self.request.matchdict, "Error: Trying to lookup " + self.request.matchdict['object_type'] +" data from database without an id."
        object_type = eval(self.request.matchdict['object_type'])
        object_id = self.request.matchdict['id']

        model = self.session.query(object_type).filter_by(id=object_id).first()
#        print model

        if model:
            data = model.dictify(convert_schema(SQLAlchemyMapping(object_type, unknown='raise', ca_description=""), page='setup'))

            json_data = json.dumps(data)
            return {'values': json_data}

    @view_config(route_name="get_ingester_logs")
    def get_ingester_logs(self):
        """
        Get event logs for the dataset specified by the passed in dam_id.  The logs are retrieved from the ingesterapi.

        :return: Found ingester logs.
        """
        assert 'dam_id' in self.request.matchdict, "Error: Trying to lookup ingester logs without an id."
        dam_id = self.request.matchdict['dam_id']

        ingester_api = services.get_ingester_platform_api(self.config)

        errors = []
        logs = []
        level, start_date, end_date = ("ALL", None, None)
        if self.request.matchdict['filtering']:
            level, start_date, end_date = self.request.matchdict['filtering'].split(",")

            try:
                logs = ingester_api.getIngesterLogs(dam_id)

                for i in reversed(range(len(logs))):
                    if level and str(level) != "ALL" and str(logs[i].level) != str(level):
                        del logs[i]
                        continue

                    try:
                        log_date = logs[i].timestamp.date()
                    except Exception as e:
                        logger.exception("Log date wasn't parsable: %s" % e)
                        continue

                    if start_date:
                        start_date = datetime.strptime(start_date.partition('T')[0], '%Y-%m-%d').date()
                        if log_date < start_date:
                            del logs[i]
                            continue

                    if end_date:
                        end_date = datetime.strptime(end_date.partition('T')[0], '%Y-%m-%d').date()
                        if log_date > end_date:
                            del logs[i]
                            continue

            except Exception as e:
                logger.exception("Exception getting logs: %s", e)
                errors.append("Error occurred: %s" % e)

        return {"values": json.dumps({"dam_id": dam_id, "logs": logs, "logs_error": errors})}








