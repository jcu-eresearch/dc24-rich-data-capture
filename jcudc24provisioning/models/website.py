"""
Provides all non-project related Colander (deform) and ColanderAlchemy (deform+SQLAlchemy) models, this includes general
website schema's such as for the login page as well as general models such as users and permissions.
"""

import hashlib
import colander
import itertools
from sqlalchemy.orm import subqueryload, subqueryload_all, backref
from colanderalchemy.declarative import Column, relationship
from sqlalchemy import Integer, ForeignKey, String, Text, Table
import deform
from jcudc24provisioning.models import Base, DBSession
from jcudc24provisioning.models.ca_model import CAModel
import os
import logging

__author__ = 'casey'

logger = logging.getLogger(__name__)


class LocalLogin(colander.MappingSchema):
    """
    Local user login form, this allows non-shibboleth users added directly to the users table to login.
    """
    user_name = colander.SchemaNode(colander.String(),)
    password = colander.SchemaNode(colander.String(), widget=deform.widget.PasswordWidget())

class ShibbolethLogin(colander.MappingSchema):
    """
    Deform schema that is really just a placeholder for a custom template (schema doesn't do anything).

    The template is a static image link to the shibboleth login page.
    """
    link = colander.SchemaNode(colander.String(), widget=deform.widget.HiddenWidget(template="shibboleth_login"))

class Login(colander.MappingSchema):
    """
    The login page that allows users to select either local login or Shibboleth login.
    """
    shibboleth_login = ShibbolethLogin(description="<i>Login over Shibboleth using your organisations credentials.</i>",
        help="Shibboleth is a 'single-sign in', or logging-in system for computer networks and the internet. "
                "It allows people to sign in, using just one 'identity', to various systems run by 'federations' "
                "of different organizations or institutions. The federations are often universities or public service "
                "organizations.", title="Shibboleth Login (Recommended)")
    local_login = LocalLogin(title="Local Login (Advanced)", description="<i>Login directly to the application using provided credentials.</i>",
        help="You will need to contact the administrators if you need a local login.<br />"
                "<i>Use Shibboleth wherever possible, local users are intended for administration purposes.</i>")
    came_from = colander.SchemaNode(colander.String(), widget=deform.widget.HiddenWidget())


class Permission(CAModel, Base):
    """
    Each page can be restricted to a specific permission (2 permissions can't be used), this table/form configures all
    permissions within the system.
    """
    order_counter = itertools.count()

    __tablename__ = 'permission'
    id = Column(Integer, primary_key=True, ca_order=next(order_counter), nullable=False, ca_widget=deform.widget.HiddenWidget())
    name = Column(String(50), ca_order=next(order_counter),)
    description = Column(Text(), ca_order=next(order_counter))

    def __init__(self, name, description=None):
        self.name = name
        self.description = description

"""
Joiner table for permissions and roles, this allows each role to have many permissions and each permission to be added
to many roles
 """
role_permissions_table = Table('role_permissions', Base.metadata,
    Column('permission_id', Integer, ForeignKey('permission.id')),
    Column('role_id', Integer, ForeignKey('role.id'))
)

class Role(CAModel, Base):
    """
    Each role can have any number of permissions and if a user is assigned a role they are are given all permissions
    associated with the role.  Eg. giving a user the admin role gives them almost all permissions.
    """
    order_counter = itertools.count()

    __tablename__ = 'role'
    id = Column(Integer, primary_key=True, ca_order=next(order_counter), nullable=False, ca_widget=deform.widget.HiddenWidget())
    name = Column(String(50), ca_order=next(order_counter))
    description = Column(Text(), ca_order=next(order_counter),)
    permissions = relationship("Permission", cascade="all", secondary=role_permissions_table, backref="roles")

    def __init__(self, name, description=None, permissions=None):
        self.name = name
        self.description = description
        self.permissions = permissions

"""
Joiner table between users and roles wich allows a user to have many roles and each role can be assigned to many users.
"""
user_roles_table = Table('user_roles', Base.metadata,
    Column('role_id', Integer, ForeignKey('role.id')),
    Column('user_id', Integer, ForeignKey('user.id'))
)

class ProjectPermissions(CAModel, Base):
    """
    ProjectPermissions are an extended joiner table between users, permissions and projects which allows:
    - A user to have many permissions for a specific project.
    - A project may have many users with permissions.
    - A user may be given permissions for many projects.

    This allows users to be given permissions for individual projects, this is really useful because users can share
    between themselves without needing administrator assistance.
    """
    __tablename__ = 'project_permissions'
    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False)
    permission_id = Column(Integer, ForeignKey('permission.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    permission = relationship("Permission", lazy="joined", backref=backref("project_permissions", cascade="all"))

    def __init__(self, project_id, permission_id, user_id):
        self.project_id = project_id
        self.permission_id = permission_id
        self.user_id = user_id

#user_permissions_table = Table('user_permissions', Base.metadata,
#    Column('permission_id', Integer, ForeignKey('permission.id')),
#    Column('user_id', Integer, ForeignKey('user.id'))
#)

class User(CAModel, Base):
    """
    Represents a user of the system, when a user logs in through Shibboleth for the first time they are automatically
    added to the user table.
    - User information such as their name and contact details
    - Authentication method (shibboleth/passwd) - passwd authentication uses the username and _password fields,
      Shibboleth uses the username field to store the Shibboleth identifier (see shibboleth_login in views/views.py)
    - Given permissions and roles.
    """
    order_counter = itertools.count()

    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, ca_order=next(order_counter), nullable=False, ca_widget=deform.widget.HiddenWidget())
    display_name = Column(String(128), ca_order=next(order_counter), nullable=False)
    username = Column(String(80), ca_order=next(order_counter), nullable=False)
    _password = Column(String(80), ca_name="password", ca_order=next(order_counter), nullable=False)
    email = Column(String(80), ca_name="email", ca_order=next(order_counter), nullable=False)
    auth_type = Column(String(80), ca_name="auth_type", ca_order=next(order_counter), nullable=False)
    project_permissions = relationship("ProjectPermissions", lazy="joined", backref="users", cascade="all")
    roles = relationship("Role", lazy="joined", secondary=user_roles_table, backref="users", cascade="all")

    def __init__(self, display_name, username, password, email, auth_type="passwd", permissions=None, roles=None):
        self.display_name = display_name
        self.username = username
        self.email = email
        self.auth_type = auth_type
        self.permissions = permissions or []
        self.roles = roles or []
        self. password = password

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        """
        Hash the password before storing it in the database.

        :param password: User entered password that is to be hashed before storing it.
        :return: None
        """
        hashed_password = password

        if isinstance(password, unicode):
            password_8bit = password.encode('UTF-8')
        else:
            password_8bit = password

        salt = hashlib.sha1(os.urandom(60))
        hash = hashlib.sha1(password_8bit + salt.hexdigest())
        hashed_password = salt.hexdigest() + hash.hexdigest()

        if not isinstance(hashed_password, unicode):
            hashed_password = hashed_password.decode('UTF-8')

        self._password = hashed_password

    def validate_password(self, password):
        """
        Validate the the given password is the same as the password originally passed in for hashing and storage.

        This is only valid for passwd authenticated users (not Shibboleth).

        :param password: Unhashed password to validate.
        :return: True if it is the same, False otherwise.
        """

        # Prevent users from logging in with Shibboleth authentication (password is never set)
        if self.auth_type != "passwd":
            return False

        if isinstance(password, unicode):
            password_8bit = password.encode('UTF-8')
        else:
            password_8bit = password

        hashed_pass = hashlib.sha1(password_8bit + self.password[:40])
        return self.password[40:] == hashed_pass.hexdigest()

    @classmethod
    def get_user(cls, userid=None, username=None, auth_type="passwd"):
        """
        Helper function that looks up a user from either the userid or username.

        :param cls: This class (eg. self, but as a class method)
        :param userid: Id of the user, either userid or username needs to be set.
        :param username: user login name, either userid or username needs to be set.
        :param auth_type: Either passwd or shibboleth
        :return: The found user or None
        """
        session = DBSession
        if userid is not None:
            return session.query(cls).filter_by(id=userid).first()
        elif username is not None:
            return session.query(cls).filter_by(username=username, auth_type=auth_type).first()

