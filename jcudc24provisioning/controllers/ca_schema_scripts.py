"""
alters the ColanderAlchemy generated schema to add additional display options including:
 - Removing the top level title (ColanderAlchemy outputs a schema with a name at the top of every form).
- Removing items not on the specified page (based on attributes on schema nodes).
- Allowing form elements to be required.
- Grouping of nodes under a MappingSchema for display purposes.
- Prevent duplicate field names causing problems by adding parent schema names separated by ':'.
- Removal of advanced/restricted fields based on a passed in parameter (this could be upgraded to integrate with the
  Pyramid permissions system).
- There is also a fix_schema_field_name) method that reverts names to their original value.
"""

import ast
from collections import OrderedDict
from datetime import date
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
    return field_name.split(":")[-1]

def convert_schema(schema, restrict_admin=False, **kw):
    schema.title = ''

    if kw.has_key('page'):
        schema = _remove_nodes_not_on_page(schema, kw.pop('page'))

    _force_required(schema)

#    fix_order(schema)

    schema = _group_nodes(schema)

    schema = _prevent_duplicate_fields(schema)

    if restrict_admin:
        _remove_admin_fields(schema)

    return schema

def _remove_admin_fields(schema):
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


def _prevent_duplicate_fields(schema):
    for node in schema.children:
        node.name = schema.name + ":" + node.name

        if isinstance(node.typ, colander.Sequence):
            _prevent_duplicate_fields(node.children[0])
        elif len(node.children) > 0:
            node = _prevent_duplicate_fields(node)
    return schema

def _force_required(schema):
    for node in schema.children:
        if len(node.children) > 0:
            _force_required(node)

        if hasattr(node, 'force_required') and node.force_required:
            setattr(node, 'missing', colander._marker)
        elif hasattr(node, 'force_required') and not node.force_required:
            setattr(node, 'missing', node.default)


def _remove_nodes_not_on_page(schema, page):
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

def _group_nodes(node):
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

def _ungroup_nodes(node):
    children_to_add = {}

    for child in node.children:

        if isinstance(child.typ, colander.Mapping) and not hasattr(child, "__tablename__"):
            child = _ungroup_nodes(child)
            index = node.children.index(child)
            node.children.remove(child)
            node.children.insert(index, child.children[0])

            children_to_add[index] = child.children[1:]

    for index, mapping_children in children_to_add.items():
        for child in mapping_children:
            index += 1
            node.children.insert(index, child)
            node.children.insert(index, child)

    return node

