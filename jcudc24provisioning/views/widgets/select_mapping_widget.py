from colander import null
from deform.compat import string_types
from deform.field import Field
from deform.widget import Widget

__author__ = 'Casey Bajema'

def _prepare_choices(values, cstruct):
    result = []
    for value, field in values:
        assert field in Field

        if not isinstance(value, string_types):
            value = str(value)
        fieldsTemplate = field.readonly and field.readonly_template or field.template
        field_code = field.renderer(fieldsTemplate, field=field, cstruct=cstruct)
        result.append((value, field, field_code))
    return result

class SelectMapping(Widget):
    values = ()
    size = None

    def serialize(self, field, cstruct, readonly=False):
        if cstruct in (null, None):
            cstruct = self.null_value

        values = _prepare_choices(self.values, cstruct)
        self.size = len(values)

        template = readonly and self.readonly_template or self.template
        return field.renderer(template, field=field, cstruct=cstruct, values=values)

    def deserialize(self, field, pstruct):
        if pstruct in (null, self.null_value):
            return null
        return pstruct









"""
Renders a mapping into a set of fields.

**Attributes/Arguments**

template
    The template name used to render the widget.  Default:
    ``mapping``.

readonly_template
    The template name used to render the widget in read-only mode.
    Default: ``readonly/mapping``.

item_template
    The template name used to render each item in the mapping.
    Default: ``mapping_item``.

readonly_item_template
    The template name used to render each item in the form.
    Default: ``readonly/mapping_item``.

"""
template = 'mapping'
readonly_template = 'readonly/mapping'
item_template = 'mapping_item'
readonly_item_template = 'readonly/mapping_item'
error_class = None
category = 'structural'
requirements = ( ('deform', None), )

def serialize(self, field, cstruct, readonly=False):
    if cstruct in (null, None):
        cstruct = {}
    template = readonly and self.readonly_template or self.template
    return field.renderer(template, field=field, cstruct=cstruct,
        null=null)

def deserialize(self, field, pstruct):
    error = None

    result = {}

    if pstruct is null:
        pstruct = {}

    for num, subfield in enumerate(field.children):
        name = subfield.name
        subval = pstruct.get(name, null)

        try:
            result[name] = subfield.deserialize(subval)
        except Invalid as e:
            result[name] = e.value
            if error is None:
                error = Invalid(field.schema, value=result)
            error.add(e, num)

    if error is not None:
        raise error

    return result