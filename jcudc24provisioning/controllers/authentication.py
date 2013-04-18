

from jcudc24provisioning.models import DBSession
from jcudc24provisioning.models.website import User, Role

from zope.interface import implementer
from pyramid.interfaces import IAuthenticationPolicy
from paste.deploy.converters import asint, asbool
from pyramid.security import ALL_PERMISSIONS, Everyone, Allow, unauthenticated_userid, authenticated_userid
from pyramid.authentication import AuthTktCookieHelper
from pyramid.security import Everyone, Authenticated
import logging

__author__ = 'casey'

logger = logging.getLogger(__name__)

class DefaultPermissions(object):
    ADMINISTRATOR = ("admin", "User can access the administrators page.")
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
    CREATOR = "g:creator", "Creator of the project, this will be dynamically assigned based on the login credentials.", [DefaultPermissions.VIEW_PROJECT, DefaultPermissions.EDIT_PROJECT, DefaultPermissions.SUBMIT, DefaultPermissions.EDIT_DATA, DefaultPermissions.EDIT_SHARE_PERMISSIONS]
    AUTHENTICATED = (Authenticated, "Any logged in user.", [DefaultPermissions.CREATE_PROJECT])
    ADMIN = ("g:admin", "Standard administrators of the system.", [getattr(_permissions, name) for name in dir(_permissions) if name not in (DefaultPermissions.EDIT_PERMISSIONS[0], DefaultPermissions.DELETE) and not name.startswith("_")])
    SUPER_ADMIN = ("g:super_admin", "Has all permissions", [getattr(_permissions, name) for name in dir(_permissions) if not name.startswith("_")])

    SHARE_VIEW_PROJECT = "s:view_project", "Shared view permissions for a project.", [DefaultPermissions.VIEW_PROJECT]
    SHARE_EDIT_PROJECT = "s:edit_project", "Shared edit permissions for a project.", [DefaultPermissions.EDIT_PROJECT]
    SHARE_SUBMIT = "s:submit", "Shared submit permissions for a project.", [DefaultPermissions.SUBMIT]
    SHARE_EDIT_DATA = "s:edit_data", "Shared data edit permissions for a project.", [DefaultPermissions.EDIT_DATA]
    SHARE_EDIT_INGESTERS = "s:edit_ingesters", "Shared edit ingester permissions for a project.", [DefaultPermissions.EDIT_INGESTERS]
    SHARE_DISABLE = "s:disable", "Shared disable ingestion permissions for a project.", [DefaultPermissions.DISABLE]
    SHARE_ENABLE = "s:enable", "Shared enable ingestion permissions for a project.", [DefaultPermissions.ENABLE]

class RootFactory(object):
    __acl__ = [
#        (Allow, DefaultRoles.CREATOR[0], DefaultRoles.CREATOR[2]),
#        (Allow, DefaultRoles.AUTHENTICATED[0], DefaultRoles.AUTHENTICATED[2]),
#        (Allow, DefaultRoles.ADMIN[0], DefaultRoles.ADMIN[2]),
#        (Allow, DefaultRoles.SUPER_ADMIN[0], DefaultRoles.SUPER_ADMIN[2]),
#        (Allow, DefaultRoles.SUPER_ADMIN[0], DefaultRoles.SUPER_ADMIN[2]),
#
#        (Allow, DefaultRoles.SHARE_VIEW_PROJECT[0], DefaultRoles.SHARE_VIEW_PROJECT[2]),
#        (Allow, DefaultRoles.SHARE_EDIT_PROJECT[0], DefaultRoles.SHARE_EDIT_PROJECT[2]),
#        (Allow, DefaultRoles.SHARE_SUBMIT[0], DefaultRoles.SHARE_SUBMIT[2]),
#        (Allow, DefaultRoles.SHARE_EDIT_DATA[0], DefaultRoles.SHARE_EDIT_DATA[2]),
#        (Allow, DefaultRoles.SHARE_EDIT_INGESTERS[0], DefaultRoles.SHARE_EDIT_INGESTERS[2]),
#        (Allow, DefaultRoles.SHARE_DISABLE[0], DefaultRoles.SHARE_DISABLE[2]),
#        (Allow, DefaultRoles.SHARE_ENABLE[0], DefaultRoles.SHARE_ENABLE[2]),

#        (Allow, Everyone, DefaultRoles.SUPER_ADMIN[2]),     # Only for testing, this disables all permissions.
        ]
    __name__ = "Root"

    def __init__(self, request):
        session = DBSession
        roles = session.query(Role).all()
        self.__acl__.extend([("Allow", role.name, [(permission.name, permission.description) for permission in role.permissions]) for role in roles])

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
            principals.extend((r.name for r in user.roles))

            if 'project_id' in request.matchdict:
                share_permissions = [p.permission for p in user.project_permissions if int(p.project_id) == int(request.matchdict['project_id'])]

                session = DBSession
                share_principles = []
                for permission in share_permissions:
                    role = session.query(Role).filter_by(name="s:%s" % permission.name).first()
                    if role is not None:
                        share_principles.append(role.name)

                principals.extend(share_principles)
                project_creator = DBSession.execute("SELECT `project_creator` FROM `project` WHERE `id`='%s'" % request.matchdict['project_id']).first()[0]
                if int(project_creator) == int(user.id):
                    principals.append(DefaultRoles.CREATOR[0])

            principals.extend((p.name for p in (role for role in user.roles)))

        return principals

def get_user(request):
    """
    Get the user from a request, this is used to bind user as a attribute of request so that request.user returns the full, authenticated user object.
    :param request: The request to get the authenticated user for (basically just get the remembered principle/user id) and look up the database for the user.
    :return: An un-attached User object, it is unattached so that it still works if there are internal changes in the database session.
    """
    userid = authenticated_userid(request)
    if userid is not None:
        user = User.get_user(userid)
        DBSession.expunge(user)
        return user
