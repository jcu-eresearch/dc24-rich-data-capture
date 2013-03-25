import logging

from paste.deploy.converters import asint, asbool
from pyramid.security import ALL_PERMISSIONS, Everyone, Allow, unauthenticated_userid
from pyramid.authentication import AuthTktCookieHelper
from pyramid.security import Everyone, Authenticated
from jcudc24provisioning.models import DBSession
from jcudc24provisioning.models.website import User

from zope.interface import implementer
from pyramid.interfaces import IAuthenticationPolicy

__author__ = 'casey'

logger = logging.getLogger(__name__)

class DefaultPermissions(object):
    CREATE_PROJECT = ("create_project", "User is allowed to create new projects.")
    VIEW_PROJECT = "view_project", "Allows viewing of project workflow pages.",
    EDIT_PROJECT = "edit_project", "Allows editing of project workflow pages",
    ADVANCED_FIELDS = "advanced_fields", "Allows viewing/editing of advanced fields that are usually hidden.",

    SUBMIT = "submit", "Allows submission of the project for administrator review and approval.",
    REOPEN = "reopen", "Allows resetting the project state to open, allowing standard users to edit again (ie. un-submit)",
    APPROVE = "approve", "Allows approval of the submitted project for ReDBox and Ingester Platform integration (Non-reversible step).",
    DISABLE = "disable", "Allows disabling of a project (which effects data ingesters).",
    ENABLE = "enable", "Allows enabling of ingesters (which effects data ingesters).",
    DELETE = "delete", "Allows deleting projects (Non-reversible).",

    EDIT_DATA = "edit_data", "Allows editing of current data and calibrations.",
    EDIT_INGESTERS = "edit_ingesters", "Allows editing of ingester configurations such as sampling rate or custom processors.",

    EDIT_SHARE_PERMISSIONS = "edit_share_permissions", "Allows granting/removing of a limited set of project permissions per project (namely view and edit).",
    EDIT_USER_PERMISSIONS = "edit_user_permissions", "Allows granting/removing of permissions and roles",
    EDIT_PERMISSIONS = "edit_permissions", "Allows editing of permissions and roles",

class DefaultRoles(object):
    _permissions = DefaultPermissions()
    CREATOR = "creator", "Creator of the project, this will be dynamically assigned based on the login credentials.", [DefaultPermissions.VIEW_PROJECT, DefaultPermissions.EDIT_PROJECT, DefaultPermissions.SUBMIT, DefaultPermissions.EDIT_DATA, DefaultPermissions.EDIT_SHARE_PERMISSIONS]
    AUTHENTICATED = ("authenticated", "Any logged in user.", [DefaultPermissions.CREATE_PROJECT])
    ADMIN = ("admin", "Standard administrators of the system.", [getattr(_permissions, name) for name in dir(_permissions) if name != DefaultPermissions.EDIT_PERMISSIONS[0] and not name.startswith("_")])
    SUPER_ADMIN = ("super_admin", "Has all permissions", [getattr(_permissions, name) for name in dir(_permissions) if not name.startswith("_")])


# TODO: Update this for shibboleth when more details are known
@implementer(IAuthenticationPolicy)
class ShibbolethAuthenticationPolicy(object):
    def __init__(self, settings, prefix="auth."):
        self.prefix = prefix
        self.userid_key = self.prefix + ".userid"

    def remember(self, request, principal, **kw):
        request.session[self.userid_key] = principal
        return []

    def forget(self, request):
        if self.userid_key in request.session:
            del request.session[self.userid_key]
        return []

    def authenticated_userid(self, request):
        # FIXME this needs to check the DB
        return request.session.get(self.userid_key)

    def unauthenticated_userid(self, request):
        return request.session.get(self.userid_key)

    def effective_principals(self, request):
        principals = [Everyone]
        user = request.user
        if user:
            principals += [Authenticated, 'u:%s' % user.id]
            principals.extend(('g:%s' % r.name for r in user.roles))
            principals.extend((p.name for p in user.project_permissions))
            principals.extend((p.name for p in (role for role in user.roles)))
        return principals

def get_user(request):
    # the below line is just an example, use your own method of
    # accessing a database connection here (this could even be another
    # request property such as request.db, implemented using this same
    # pattern).
    userid = unauthenticated_userid(request)
    if userid is not None:
        user = User.get_user(userid)
        DBSession.expunge(user)
        return user
