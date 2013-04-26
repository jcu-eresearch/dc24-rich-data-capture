"""
Provides the authentication policy, root factory as well as defining the default roles and permissions.

This module provides application specific functionality, see models/website.py for associated models.
"""

from jcudc24provisioning.models import DBSession
from jcudc24provisioning.models.website import User, Role
from pyramid.httpexceptions import HTTPClientError

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
    """
    Default permissions used within the EnMaSSe application, this class doesn't actually do anything, just defines
    them as constants.

    The initializedb.py script adds all permissions in this class.

    Permissions are defined as 2 element tuples (<permission name>, <permission description>).  The description is
    only there to explain the permissions purpose to users and developers.
    """
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
    """
    Default roles used within the EnMaSSe application, this class doesn't actually do anything, just defines
    them as constants.

    The initializedb.py script adds all roles defined in this class.

    Roles are defined as 3 element tuples (<principle name>, <role description>, <array of permissions>)
    """

    _permissions = DefaultPermissions()
    CREATOR = "g:creator", "Creator of the project, this will be dynamically assigned based on the login credentials.", [
        DefaultPermissions.VIEW_PROJECT, DefaultPermissions.EDIT_PROJECT, DefaultPermissions.SUBMIT,
        DefaultPermissions.EDIT_DATA, DefaultPermissions.EDIT_SHARE_PERMISSIONS]
    AUTHENTICATED = (Authenticated, "Any logged in user.", [DefaultPermissions.CREATE_PROJECT])
    ADMIN = ("g:admin", "Standard administrators of the system.",
             [getattr(_permissions, name) for name in dir(_permissions) if
              name not in (DefaultPermissions.EDIT_PERMISSIONS[0], DefaultPermissions.DELETE) and not name.startswith(
                  "_")])
    SUPER_ADMIN = ("g:super_admin", "Has all permissions",
                   [getattr(_permissions, name) for name in dir(_permissions) if not name.startswith("_")])

    SHARE_VIEW_PROJECT = "s:view_project", "Shared view permissions for a project.", [DefaultPermissions.VIEW_PROJECT]
    SHARE_EDIT_PROJECT = "s:edit_project", "Shared edit permissions for a project.", [DefaultPermissions.EDIT_PROJECT]
    SHARE_SUBMIT = "s:submit", "Shared submit permissions for a project.", [DefaultPermissions.SUBMIT]
    SHARE_EDIT_DATA = "s:edit_data", "Shared data edit permissions for a project.", [DefaultPermissions.EDIT_DATA]
    SHARE_EDIT_INGESTERS = "s:edit_ingesters", "Shared edit ingester permissions for a project.", [
        DefaultPermissions.EDIT_INGESTERS]
    SHARE_DISABLE = "s:disable", "Shared disable ingestion permissions for a project.", [DefaultPermissions.DISABLE]
    SHARE_ENABLE = "s:enable", "Shared enable ingestion permissions for a project.", [DefaultPermissions.ENABLE]


class RootFactory(object):
    """
    This root factory is used to defined the EnMaSSe systems Access Control Levels (ACL).

    This is done by returning all roles in the databases in the required format of (Allow, <principle_name>, <permissions>)
    """

    __acl__ = [
        #        (Allow, Everyone, DefaultRoles.SUPER_ADMIN[2]),     # Only for testing, this disables all permissions.
    ]
    __name__ = "Root"

    def __init__(self, request):
        session = DBSession
        roles = session.query(Role).all()
        self.__acl__.extend(
            [("Allow", role.name, [(permission.name, permission.description) for permission in role.permissions]) for
             role in roles])


@implementer(IAuthenticationPolicy)
class ShibbolethAuthenticationPolicy(object):
    """
    AuthenticationPolicy that reads the user id from the current session and authenticates against the user, permissions
    and roles database tables.
    """

    def __init__(self, settings, prefix="auth."):
        self.prefix = prefix
        self.userid_key = self.prefix + ".userid"
        self.session = DBSession()

    def remember(self, request, principal, **kw):
        request.session[self.userid_key] = principal
        return []

    def forget(self, request):
        if self.userid_key in request.session:
            del request.session[self.userid_key]
        return []

    def authenticated_userid(self, request):
        user = self.session.query(User).filter_by(id=self.unauthenticated_userid(request)).first()

        if user is not None:
            return user.id

        return None

    def unauthenticated_userid(self, request):
        return request.session.get(self.userid_key)

    def effective_principals(self, request):
        """
        This method provides the core permissions framework where it reads and assigns principles for the current user.

        Each user has the following principles:
        - Everyone (any viewer, whether they are logged in or not).
        - Authenticated (every user that can login)
        - Roles that are shared with this user for the current project.
        - Roles the user is assigned to (ag administrator).
        """
        principals = [Everyone]
        user = request.user
        if user:
            principals += [Authenticated, 'u:%s' % user.id]

            # Add the role name for each role this user is assigned to.
            principals.extend((r.name for r in user.roles))

            # Add each role/permission that is shared with user for the currently view project (there are 1:1 mappings
            # of permissions to roles for the purpose of sharing).
            if 'project_id' in request.matchdict:
                project_id = int(request.matchdict['project_id'])

                share_permissions = [p.permission for p in user.project_permissions if int(p.project_id) == project_id]

                share_principles = []
                for permission in share_permissions:
                    role = self.session.query(Role).filter_by(name="s:%s" % permission.name).first()
                    if role is not None:
                        share_principles.append(role.name)

                principals.extend(share_principles)
                project_creator = self.session.execute("SELECT `project_creator` FROM `project` WHERE `id`='%s'" % project_id).first()
                if project_creator is None:
                    raise HTTPClientError("You are trying to access a project that doesn't exist.  Either you have edited the address bar directly or the project no longer exists.")
                project_creator = project_creator[0]
                if project_creator is not None and int(project_creator) == int(user.id):
                    principals.append(DefaultRoles.CREATOR[0])

        return principals


def get_user(request):
    """
    Get the user from a request, this is used to bind user as a attribute of request so that request.user returns the
    full, authenticated user object.
    :param request: The request to get the authenticated user for (basically just get the remembered principle/user id) and look up the database for the user.
    :return: An un-attached User object, it is unattached so that it still works if there are internal changes in the database session.
    """
    userid = authenticated_userid(request)
    if userid is not None:
        user = User.get_user(userid)
        DBSession().expunge(user)
        return user
