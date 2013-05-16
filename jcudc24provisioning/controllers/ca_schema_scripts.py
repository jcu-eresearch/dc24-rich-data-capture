"""
alters the ColanderAlchemy generated schema to add additional display options including:
- Removing the top level title (ColanderAlchemy outputs a schema with a name at the top of every form).
- Removing items not on the specified page (based on attributes on schema nodes).
- Allowing form elements to be required.
- Grouping of nodes under a MappingSchema for display purposes.
- Prevent duplicate field names causing problems by adding parent schema names separated by :
- Removal of advanced/restricted fields based on a passed in parameter (this could be upgraded to integrate with the
  Pyramid permissions system).
- There is also a fix_schema_field_name) method that reverts names to their original value.
"""

import ast
from collections import OrderedDict
from datetime import date
from beaker.cache import cache_region
import colander
from colanderalchemy.types import SQLAlchemyMapping
import deform
import os
import logging
from pyramid.security import has_permission
#from jcudc24provisioning.models.project import DatasetDataSource, SOSDataSource, PushDataSource, PullDataSource, FormDataSource



logger = logging.getLogger(__name__)

__author__ = 'Casey Bajema'

def fix_schema_field_name(field_name):
    """
    Remove parent form element names that prepend the actual elements name to prevent duplicate form names.
    :param field_name: Name that is used on the output HTML forms.
    :return: model attribute name.
    """
    return field_name.split(":")[-1]

def convert_schema(schema, restrict_admin=False, **kw):
    """
    Convert the default ColanderAlchemy schema to include the required additional features, this may include:
    - Removing the top level title (ColanderAlchemy outputs a schema with a name at the top of every form).
    - Removing items not on the specified page (based on attributes on schema nodes).
    - Allowing form elements to be required.
    - Grouping of nodes under a MappingSchema for display purposes.
    - Prevent duplicate field names causing problems by adding parent schema names separated by :
    - Removal of advanced/restricted fields based on a passed in parameter (this could be upgraded to integrate with the
      Pyramid permissions system).
    - There is also a fix_schema_field_name) method that reverts names to their original value.

    :param schema: original schema
    :param restrict_admin: should fields marked as restricted (ca_requires_admin=True) be removed?
    :param kw: additional paramaters
    :return: modified schema with the desired alterations.
    """
    schema.title = ''

    # Remove elements not on the current page (or in other words, elements that have a non-matching page value set).
    if kw.has_key('page'):
        schema = _remove_nodes_not_on_page(schema, kw.pop('page'))

    # Make fields required (ColanderAlchemy removes the ability to have required fields)
    schema = _force_required(schema)

#    fix_order(schema)

    # Wrap elements between ca_group_start and ca_group_end attributes with a MappingSchema (display purposes)
    schema = schema = _group_nodes(schema)

    # Prepend the elements name with <parent element name>:
    schema = _prevent_duplicate_fields(schema)

    # Remove fields that are marked as ca_require_admin=True if restrict_admin is True
    if restrict_admin:
        schema = _remove_admin_fields(schema)

    return schema

@cache_region('long_term')
def _remove_admin_fields(schema):
    """
    Remove fields that are marked as ca_require_admin=True

    :param schema: schema to remove elements from
    :return: updated schema
    """
    denied_nodes = []
    for node in schema.children:
        if hasattr(node, 'requires_admin') and node.requires_admin:
#        if hasattr(node, 'requires_admin') and node.requires_admin and not has_permission("advanced_fields"):
#            print "Removed node: " + str(node)
            denied_nodes.append(node)
        else:
            if len(node.children) > 0:
                _remove_admin_fields(node)

    for node in denied_nodes:
        schema.children.remove(node)

    return schema

@cache_region('long_term')
def _prevent_duplicate_fields(schema):
    """
    Prepend the elements name with <parent element name>:

    :param schema: schema to update
    :return: updated schema
    """
    for node in schema.children:
        node.name = schema.name + ":" + node.name

        if isinstance(node.typ, colander.Sequence):
            _prevent_duplicate_fields(node.children[0])
        elif len(node.children) > 0:
            node = _prevent_duplicate_fields(node)
    return schema

@cache_region('long_term')
def _force_required(schema):
    """
    Make fields required (ColanderAlchemy removes the ability to have required fields)

    :param schema: schema to update
    :return: updated schema
    """
    for node in schema.children:
        if len(node.children) > 0:
            _force_required(node)

        if hasattr(node, 'force_required') and node.force_required:
            setattr(node, 'missing', colander._marker)
        elif hasattr(node, 'force_required') and not node.force_required:
            setattr(node, 'missing', node.default)

    return schema

def _remove_nodes_not_on_page(schema, page):
    """
    Remove elements not on the current page (or in other words, elements that have a non-matching page value set).

    :param schema: schema to update
    :param page: page value that is allowed, all elements with a non-matching page value are removed.
    :return: updated schema
    """
    children_to_remove = []

    for child in schema.children:
        if len(child.children) > 0:
            _remove_nodes_not_on_page(child, page)

        if hasattr(child, 'page') and child.page != page:
            children_to_remove.append(child)

    for child in children_to_remove:
        schema.children.remove(child)

    return schema

def _fix_sequence_schemas(sequence_node):
    """
    Sequence schemas have some display problems that ca_child_... elements are used to fix.
    Some other problems include displaying of labels when there is only 1 element (which looks odd).

    :param sequence_node: sequence item to fix/update
    :return: None
    """
    # Set the childs widget if ca_child_widget has been set on the sequence (I can't see any other way to do it)
    for attr in sequence_node.__dict__:
        if attr[:6] == "child_":
            setattr(sequence_node.children[0], attr[6:], sequence_node.__dict__[attr])

#                if hasattr(child, "child_widget"):
#                    child.children[0].widget = child.child_widget

    # If there is only 1 displayed child, hide the labels etc so that the item looks like a list
    only_one_displayed = True
    displayed_child = None

    for sub_child in sequence_node.children[0].children:
        if not isinstance(sub_child.widget, deform.widget.HiddenWidget):
            if displayed_child:
                only_one_displayed = False
                continue

            displayed_child = sub_child

    if only_one_displayed and displayed_child:
        sequence_node.children[0].widget = deform.widget.MappingWidget(template="ca_sequence_mapping", item_template="ca_sequence_mapping_item")

    return sequence_node

@cache_region('long_term')
def _group_nodes(node):
    """
    Wrap elements between ca_group_start and ca_group_end attributes with a MappingSchema (display purposes).

    :param node: schema to update
    :return: updated schema
    """
    mappings = OrderedDict()
    groups = []
    chilren_to_remove = []
    for child in node.children:
        if hasattr(child, "group_start"):
            group = child.__dict__.pop("group_start")
            group_params = {}

            for param in child.__dict__.copy():
                if param[:6] == 'group_' and not param == 'group_end':
                    group_params[param[6:]] = child.__dict__.pop(param)

            child.__dict__["group_start"] = group # Need to re-add the group_start attribute for the logic below.

            groups.append(group)
            if 'schema' not in group_params:
                mappings[group] = colander.MappingSchema(name=group, collapse_group=group,
                    **group_params)
            else:
                mappings[group] = group_params.pop('schema')(name=group, collapse_group=group,
                    **group_params)

            if len(groups) > 1:
                parent_group = groups[groups.index(group) - 1]
                mappings[parent_group].children.append(mappings[group])
            else:
                node.children.insert(node.children.index(child), mappings[group])

        if isinstance(child.typ, colander.Sequence):
            _fix_sequence_schemas(child)
            _group_nodes(child.children[0])
        elif len(child.children) > 0:
            child = _group_nodes(child)

        if len(groups) > 0:

            # If the child is replaced by a mapping schema, delete it now - otherwise delete it later
            # This is to prevent the models children from changing while they are being iterated over.
            if hasattr(child, 'group_start') and len(groups) == 1:
                node.children.remove(child)
            else:
                chilren_to_remove.append(child)

            mappings[groups[len(groups) - 1]].children.append(child)

        if hasattr(child, "group_end"):
            i = 0
            popped_group = None
            # Delete the ended group as well as all subgroups that have been invalidly left open.
            while len(groups) > 0 and popped_group != child.group_end:
                popped_group = groups.pop()
                mappings.pop(popped_group)

    for child in chilren_to_remove:
        node.children.remove(child)

    return node


#def _ungroup_nodes(node):
#    children_to_add = {}
#
#    for child in node.children:
#
#        if isinstance(child.typ, colander.Mapping) and not hasattr(child, "__tablename__"):
#            child = _ungroup_nodes(child)
#            index = node.children.index(child)
#            node.children.remove(child)
#            node.children.insert(index, child.children[0])
#
#            children_to_add[index] = child.children[1:]
#
#    for index, mapping_children in children_to_add.items():
#        for child in mapping_children:
#            index += 1
#            node.children.insert(index, child)
#            node.children.insert(index, child)
#
#    return node

