"""
Provides AJAX based lock/unlock of all pages.
"""

from datetime import timedelta
import json
from jcudc24provisioning.models import DBSession
from jcudc24provisioning.models.website import PageLock
from pyramid.view import view_config, view_defaults
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
    def lock_page(self, user_id=None, url=None):
        """
        Lock a page using the matchdict user_id and route_name

        :return: None
        """

        if user_id is None:
            assert 'user_id' in self.request.matchdict, "Error: Trying to lock a page without a valid user_id."
            user_id = self.request.matchdict['user_id']

        if url is None:
            assert 'url' in self.request.matchdict, "Error: Trying to lock an unkown page."
            url = '/' + '/'.join(self.request.matchdict['url'])

        current_date = datetime.now()
        expire_period = timedelta(hours=24)
        expire_time = current_date + expire_period
        lock = PageLock(user_id, url, expire_time)
        self.session.add(lock)

        # Clean up expired locks.
        self.session.query(PageLock).filter(PageLock.expire_date < datetime.now()).delete()

        self.session.flush()

        if self.request.matchdict is not None and "user_id" in self.request.matchdict and "url" in self.request.matchdict:
            json_data = json.dumps({'id': lock.id})
            return {'values': json_data}

        return lock.id

    @view_config(route_name="unlock_page")
    def unlock_page(self, lock_id=None):
        """
        Un-lock a page using the matchdict user_id and route_name

        :return: None
        """

        if lock_id is None:
            assert 'lock_id' in self.request.matchdict, "Error: Trying to unlock a page without a valid lock_id."
            lock_id = self.request.matchdict['lock_id']

        self.session.query(PageLock).filter_by(id=lock_id).delete()
        self.session.flush()

        json_data = json.dumps({})
        return {'values': json_data}








