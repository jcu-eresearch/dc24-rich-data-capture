import hashlib
import colander
import itertools
from colanderalchemy.declarative import Column, relationship
from sqlalchemy import Integer, ForeignKey, String, Text, Table
import deform
from jcudc24provisioning.models import Base, DBSession
from jcudc24provisioning.models.ca_model import CAModel
import os

__author__ = 'casey'


class Login(colander.MappingSchema):
    user_name = colander.SchemaNode(colander.String())
    password = colander.SchemaNode(colander.String(), widget=deform.widget.PasswordWidget())
    came_from = colander.SchemaNode(colander.String(), widget=deform.widget.HiddenWidget())

class Permission(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'permission'
    id = Column(Integer, primary_key=True, ca_order=next(order_counter), nullable=False, ca_widget=deform.widget.HiddenWidget())
    name = Column(String(50), ca_order=next(order_counter))
    description = Column(Text(), ca_order=next(order_counter))

    def __init__(self, name, description=None):
        self.name = name
        self.description = description

role_permissions_table = Table('role_permissions', Base.metadata,
    Column('permission_id', Integer, ForeignKey('permission.id')),
    Column('role_id', Integer, ForeignKey('role.id'))
)

class Role(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'role'
    id = Column(Integer, primary_key=True, ca_order=next(order_counter), nullable=False, ca_widget=deform.widget.HiddenWidget())
    name = Column(String(50), ca_order=next(order_counter))
    description = Column(Text(), ca_order=next(order_counter))
    permissions = relationship("Permission", secondary=role_permissions_table, backref="roles")

    def __init__(self, name, description=None, permissions=None):
        self.name = name
        self.description = description
        self.permissions = permissions


user_roles_table = Table('user_roles', Base.metadata,
    Column('role_id', Integer, ForeignKey('role.id')),
    Column('user_id', Integer, ForeignKey('user.id'))
)

user_permissions_table = Table('user_permissions', Base.metadata,
    Column('permission_id', Integer, ForeignKey('permission.id')),
    Column('user_id', Integer, ForeignKey('user.id'))
)

class User(CAModel, Base):
    order_counter = itertools.count()

    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, ca_order=next(order_counter), nullable=False, ca_widget=deform.widget.HiddenWidget())
    username = Column(String(80), ca_order=next(order_counter), nullable=False)
    _password = Column(String(80), ca_name="password", ca_order=next(order_counter), nullable=False)
    permissions = relationship("Permission", secondary=user_permissions_table, backref="users")
    roles = relationship("Role", secondary=user_roles_table, backref="users")

    def __init__(self, username, password, permissions=None, roles=None):
        self.username = username
        self._password = password
        self.permissions = permissions or []
        self.roles = roles or []

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        hashed_password = password

        if isinstance(password, unicode):
            password_8bit = password.encode('UTF-8')
        else:
            password_8bit = password

        salt = hashlib.md5(os.urandom(60))
        hash = hashlib.md5(password_8bit + salt.hexdigest())
        hashed_password = salt.hexdigest() + hash.hexdigest()

        if not isinstance(hashed_password, unicode):
            hashed_password = hashed_password.decode('UTF-8')

        self.password = hashed_password

    def validate_password(self, password):
        test = self.password[:40]
        hashed_pass = hashlib.md5(password + self.password[:40])
        return self.password[40:] == hashed_pass.hexdigest()

    @classmethod
    def get_user(cls, userid=None, username=None):
        session = DBSession
        if userid is not None:
            return session.query(cls).filter_by(id=userid).first()
        elif username is not None:
            return session.query(cls).filter_by(username=username).first()

