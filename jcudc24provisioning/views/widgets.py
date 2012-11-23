from colander import null, Invalid
import colander
import deform
from deform.field import Field
from deform.widget import Widget, _normalize_choices

__author__ = 'Casey'

class SelectMappingWidget(Widget):
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
    template = 'select_mapping'
    readonly_template = 'readonly/select_mapping'
    item_template = 'mapping_item'
    readonly_item_template = 'readonly/mapping_item'
    error_class = None
    category = 'structural'
    requirements = ( ('deform', None), )
    select_element = "schema_select"

    def serialize(self, field, cstruct, readonly=False):
#        #  Dynamically add the select box for selecting the desired schema
#        found = False
#        for node in field.children:
#            if node.name == "schema_select":
#                found = True
#                break
#
#        if not found:
#            new_child = colander.SchemaNode(colander.String(), name="schema_select", widget = deform.widget.HiddenWidget(), missing="none")
#            field.schema.children.insert(0, new_child)
#            field.children.insert(0,Field(new_child, renderer=field.renderer, counter=field.counter, resource_registry=field.resource_registry))

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

        selected_schema = pstruct.get(self.select_element, null)
        if selected_schema is null or selected_schema == "none":
            return null

        result[self.select_element] = selected_schema

        for num, subfield in enumerate(field.children):
            # If this subfield isn't the slected schema then continue without getting its results.
            if subfield.oid != selected_schema:
                continue

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

class ConditionalCheckboxMapping(Widget):
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
    template = 'conditional_checkbox_mapping'
    readonly_template = 'readonly/conditional_checkbox_mapping'
    item_template = 'mapping_item'
    readonly_item_template = 'readonly/mapping_item'
    error_class = None
    category = 'structural'
    requirements = ( ('deform', None), )
    checkbox_element = "conditional_checkbox"

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

        checkbox_schema = pstruct.get(self.checkbox_element, null)
        if checkbox_schema is null:
            return null

        result[self.checkbox_element] = True

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

        result[self.checkbox_element] = True
        return result

class SelectWithOtherWidget(Widget):
    """
    Renders ``<select>`` field based on a predefined set of values.

    **Attributes/Arguments**

    values
        A sequence of two-tuples (the first value must be of type
        string, unicode or integer, the second value must be string or
        unicode) indicating allowable, displayed values, e.g. ``(
        ('true', 'True'), ('false', 'False') )``.  The first element
        in the tuple is the value that should be returned when the
        form is posted.  The second is the display value.

    size
        The ``size`` attribute of the select input field (default:
        ``None``).

    null_value
        The value which represents the null value.  When the null
        value is encountered during serialization, the
        :attr:`colander.null` sentinel is returned to the caller.
        Default: ``''`` (the empty string).

    template
        The template name used to render the widget.  Default:
        ``select``.

    readonly_template
        The template name used to render the widget in read-only mode.
        Default: ``readonly/select``.

    """
    template = 'select_with_other'
    readonly_template = 'readonly/select'
    null_value = ''
    values = ()
    size = None
    other = None

    def serialize(self, field, cstruct, readonly=False):
        if cstruct in (null, None):
            cstruct = self.null_value
        template = readonly and self.readonly_template or self.template
        return field.renderer(template, field=field, cstruct=cstruct,
            values=_normalize_choices(self.values))

    def deserialize(self, field, pstruct):
        if pstruct in (null, self.null_value):
            return null
        return pstruct


