import colander
import deform

__author__ = 'casey'


class Login(colander.MappingSchema):
    user_name = colander.SchemaNode(colander.String())
    password = colander.SchemaNode(colander.String(), widget=deform.widget.PasswordWidget())
    came_from = colander.SchemaNode(colander.String(), widget=deform.widget.HiddenWidget())