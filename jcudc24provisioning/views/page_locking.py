"""
Provides AJAX based lock/unlock of all pages.
"""

import ConfigParser
from datetime import timedelta
import json
from colanderalchemy.types import SQLAlchemyMapping
from jcudc24ingesterapi.authentication import CredentialsAuthentication
import jcudc24provisioning
from jcudc24provisioning.controllers.ingesterapi_wrapper import IngesterAPIWrapper
from jcudc24provisioning.models import DBSession
from jcudc24provisioning.models.website import PageLock
from pyramid.view import view_config, view_defaults
from jcudc24provisioning.controllers.ca_schema_scripts import convert_schema
from jcudc24provisioning.models.project import *

__author__ = 'Casey Bajema'


@view_defaults(renderer="../templates/search_template.pt")
class PageLocking(object):
    """
    Locks and unlocks pages over AJAX from the main template.
    """
    def __init__(self, request):
        self.request = request
        self.session = DBSession

    @view_config(route_name="lock_page")
    def lock_page(self):
        """
        Lock a page using the matchdict user_id and route_name

        :return: None
        """

        assert 'user_id' in self.request.matchdict, "Error: Trying to lock a page without a valid user_id."
        assert 'route' in self.request.matchdict, "Error: Trying to lock an unkown page."
        user_id = self.request.matchdict['user_id']
        route_name = self.request.matchdict['route']

        current_date = datetime.now()
        expire_period = timedelta(hours=24)
        expire_time = current_date + expire_period
        lock = PageLock(user_id, route_name, expire_time)
        self.session.add(lock)

        # Clean up expired locks.
        self.session.query(PageLock).filter(PageLock.expire_date < datetime.now()).delete()

        self.session.flush()

        json_data = json.dumps({'id': lock.id})
        return {'values': json_data}

    @view_config(route_name="unlock_page")
    def unlock_page(self):
        """
        Un-lock a page using the matchdict user_id and route_name

        :return: None
        """

        assert 'lock_id' in self.request.matchdict, "Error: Trying to unlock a page without a valid lock_id."
        lock_id = self.request.matchdict['lock_id']

        self.session.query(PageLock).filter_by(id=lock_id).delete()
        self.session.flush()

        json_data = json.dumps({})
        return {'values': json_data}








