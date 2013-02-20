import ast
from collections import OrderedDict
from datetime import date
import colander
from colanderalchemy.types import SQLAlchemyMapping
import deform
import os
#from jcudc24provisioning.models.project import DatasetDataSource, SOSDataSource, PushDataSource, PullDataSource, FormDataSource

import logging
logger = logging.getLogger(__name__)

__author__ = 'Casey Bajema'

# TODO: It may be possible to update these scripts to work better using for prop in object_mapper(source).iterate_properties:

#def get_ca_registry(field_name, model_class):
#    try:
#        ca_registry = None
#        if field_name in model_class._sa_class_manager:
#            if hasattr(model_class._sa_class_manager[field_name].comparator, 'mapper') and field_name in model_class._sa_class_manager[field_name].comparator.mapper.columns._data:
#                ca_registry = model_class._sa_class_manager[field_name].comparator.mapper.columns._data[field_name]._ca_registry
#            elif hasattr(model_class._sa_class_manager[field_name], '_parententity') and field_name in model_class._sa_class_manager[field_name]._parententity.columns._data:
#                ca_registry = model_class._sa_class_manager[field_name]._parententity.columns._data[field_name]._ca_registry
#            elif hasattr(model_class._sa_class_manager[field_name], '_parententity') and field_name in model_class._sa_class_manager[field_name]._parententity.relationships._data:
#                ca_registry = model_class._sa_class_manager[field_name]._parententity.relationships._data[field_name].ca_registry
#            else:
#                raise NotImplementedError("ca_registry lookup for this object isn't implemented.")
##                return None
#        return ca_registry
#    except Exception as e:
#        logger.exception("Exception occurred while getting model's ca_registry: %s" % e)
#        raise e
#
#def get_model_class(model_object):
#    return model_object._sa_instance_state.class_
#
#def fileupload_to_filehandle(field_name, value, model_class=None, ca_registry=None, model_object=None):
#    try:
#        if ca_registry is None and model_class is None and model_object is None:
#            raise ValueError("Requires either ca_registry, model_object or model_class")
#
#        if ca_registry is None and model_class is None:
#            model_class = get_model_class(model_object)
#
#        if ca_registry is None:
#            ca_registry = get_ca_registry(field_name, model_class)
#
#            # This isn't a form
#            if ca_registry is None:
#                return value
#
#        # Handle file uploads
#        # If this is a file field
#        if 'type' in ca_registry and isinstance(ca_registry['type'], deform.FileData):
#            # If this is a new file
#            if isinstance(value, dict) and 'preview_url' in value:
#                value = str(value['preview_url'])
#
#            # If this is an already selected and uploaded file
#            elif isinstance(value, dict) and 'fp' in value and hasattr(value['fp'], 'name'):
#                value = str(value['fp'].name)
#
#            # File was previously uploaded and the user just removed it
#            else:
#                value = None
#
#        return value
#
#    except Exception as e:
#        logger.exception("Exception occurred while converting file upload to filehandle: %s" % e)
#        raise e
#
#def normalize_form_value(field_name, value, model_object):
#    try:
#        # Normalise values returned from forms
#        if not isinstance(value, list) and not isinstance(value, dict):
#            if value == 'false' or (isinstance(getattr(model_object, field_name), bool) and not bool(value)):
#                value = False
#            elif value == 'true' or (isinstance(getattr(model_object, field_name), bool) and bool(value)):
#                value = True
#            elif value == colander.null or value == 'None' or value == 'colander.null':
#                value = None
#            elif isinstance(value, str) and value == '':
#                value = None
#
#            # Best attempt, cast all values to their required type
#            if value is not None and isinstance(getattr(model_object, field_name), (int, long, float, str)):
#                value = (type(getattr(model_object, field_name)))(value)
#
#        elif (isinstance(value, dict) or value is None):
#            value = fileupload_to_filehandle(field_name, value, model_object)
#
#        return value
#    except Exception as e:
#        logger.exception("Exception occurred while normalizing model value: %s" % e)
#        raise e
#
#def create_sqlalchemy_model(data, model_class=None, model_object=None):
#    is_data_empty = True
#    if model_object is None and model_class is not None:
#        model_object = model_class()
#
#    if model_class is None and model_object is not None:
#        model_class = get_model_class(model_object)
#
#    if model_class is None or model_object is None:
#        raise ValueError("Model class or model object could not be found while creating sqlalchemy model.")
#
#    if data is None or not isinstance(data, dict) or len(data) <= 0:
#        return None
#
#    prefix = ''.join(str(x + ":") for x in data.items()[0][0].split(":")[:-1])
#    new_model = True
#    if model_object.id is not None and model_object.id >= 0:
#        new_model = False
#    elif prefix + 'id' in data and (isinstance(data[prefix + 'id'], (long, int)) or (isinstance(data[prefix + 'id'], basestring) and data[prefix + 'id'].isnumeric())) and long(data[prefix + 'id']) >= 0:
#        new_model = False
#
#    for field_name, value in data.items():
#        field_name = fix_schema_field_name(field_name)
#
#        # If this is a grouping - add its fields to the current model_object
#        if not hasattr(model_object, field_name) and isinstance(value, dict):
#            create_sqlalchemy_model(value, model_class=model_class, model_object=model_object)
#        elif hasattr(model_object, field_name):
#            # Fix form values to be the correct class and type and post formatting (eg. fileupload gets file handle from dict, bool is converted from 'false' to False, etc.).
#            value = normalize_form_value(field_name, value, model_object)
#
#            if isinstance(getattr(model_object, field_name), list) or isinstance(value, list):
#                # If the value hasn't changed
#                if value is None or value == getattr(model_object, field_name):
#                    continue
#                # If all items have been removed
#                if value is None:
#                    is_data_empty = False
#                    setattr(model_object, field_name, [])
#                    continue
#
#                # Otherwise the list has been changed in some other way
#                # Remove all items from the list, so that any items that aren't there are deleted.
#                old_items = []
#                for i in reversed(range(len(getattr(model_object, field_name, [])))):
#                    old_items.append(getattr(model_object, field_name)[i])
#
#                for item in value:
#                    if item is None or item is colander.null or not isinstance(item, dict) or len(item) <= 0:
#                        continue
#
#                    if 'schema_select' in item and len(item) == 2:  # This is the custom developed select mapping - flatten the select out
#                        method = item.pop('schema_select')
#                        item = item.values()[0]
#
#                    current_object = None
#
#                    prefix = ''.join(str(x + ":") for x in item.items()[0][0].split(":")[:-1])
#
#                    # If the item has an id and the id==an item in the model_object, update the model object item instead of creating a new one.
#                    if prefix + 'id' in item and (isinstance(item[prefix + 'id'], (long, int)) or (isinstance(item[prefix + 'id'], basestring) and item[prefix + 'id'].isnumeric())):
#                        for model_item in old_items:
##                            print "ID's: " + str(getattr(model_item, 'id', None)) + " : " + str(item['id'])
#                            current_object_id = getattr(model_item, 'id', None)
##                            print (isinstance(current_object_id, (int, long)) or (isinstance(current_object_id, basestring) and current_object_id.isnumeric()))
#                            if (isinstance(current_object_id, (int, long)) or (isinstance(current_object_id, basestring) and current_object_id.isnumeric())) and int(getattr(model_item, 'id', None)) == int(item[prefix + 'id']):
#                                current_object = model_item
#                                old_items.remove(current_object)
##                                print "Current Object: " + str(current_object)
#                                break
#
#                    child_table_object = create_sqlalchemy_model(item, model_class=model_object._sa_class_manager[field_name].property.mapper.class_, model_object=current_object)
#                    if child_table_object is not None:
#                        is_data_empty = False
#                        getattr(model_object, field_name).append(child_table_object) # Add the modified object
#                    elif current_object is not None:
#                        getattr(model_object, field_name).append(current_object) # Re-add the un-modified object
#
#                # Delete items in the list that were missing from the new data
#                for item in old_items:
#                    getattr(model_object, field_name).remove(item)
#                    del item
#                    is_data_empty = False
#
#            elif isinstance(getattr(model_object, field_name), dict) or isinstance(value, dict):
#                # If the value hasn't been changed
#                if value == getattr(model_object, field_name):
#                    continue
#                elif value is None:
#                    # If the value is now empty and it was set previously
#                    is_data_empty = False
#                    setattr(model_object, field_name, None)
#                    continue
#
#                current_object = None
#                if getattr(model_object, field_name) is not None:
#                    current_object = getattr(model_object, field_name, None)
#
#                if not hasattr(model_object._sa_class_manager[field_name].property, 'mapper'):
#                    raise AttributeError("Model conversion scripts have an error, trying to generate a model with invalid values.")
#                child_table_object = create_sqlalchemy_model(value, model_class=model_object._sa_class_manager[field_name].property.mapper.class_, model_object=current_object)
#
#                if child_table_object is not None:
#                    setattr(model_object, field_name, child_table_object)
#                    is_data_empty = False
#
#            else:
#                # If the value hasn't been changed
#                if value == getattr(model_object, field_name):
#                    continue
#
#                # If the value is now empty and it was set previously
#                elif value is None:
#                    setattr(model_object, field_name, None)
#                    is_data_empty = False
#                    continue
#                try:
#
#                    # Don't use default values to determine if the data is a new object.
#                    ca_registry = get_ca_registry(field_name, model_class)
#                    if 'default' not in ca_registry or not value == ca_registry['default'] or not new_model:
#                        is_data_empty = False
#                    setattr(model_object, field_name, value)
#
#                except Exception as e:
#                    logger.exception("Failed to set model attribute: %s" % field_name)
#                    continue
#
#
#    if is_data_empty:
#        return None
#
#    if not isinstance(model_object.id, (int, long)):
#        test = 2
#
#    return model_object
#
#def convert_sqlalchemy_model_to_data(model, schema=None):
#    if schema is None:
#        # This will not take groupings into account
#        schema = convert_schema(SQLAlchemyMapping(type(model)))
#
#    data = {}
#
#    if model is None:
#        return data
#
#    for node in schema:
#        name = fix_schema_field_name(node.name)
#
#        if hasattr(model, name):
#            value = getattr(model, name, None)
#
#            if isinstance(value, date):
#                try:
#                    colander.Date().serialize(None, value)
#                except colander.Invalid, e:
#                    value = str(value)
#
#            if isinstance(value, bool)  and hasattr(node.widget, 'true_val'):
#                if value:
#                    value = node.widget.true_val
#                elif hasattr(node.widget, 'false_val'):
#                    value = node.widget.false_val
#
#            if isinstance(value, list):
#                node_list = []
#                for item in value:
#                    node_list.append(convert_sqlalchemy_model_to_data(item,  node.children[0]))
#
#                data[node.name] = node_list
#            elif isinstance(node.typ, deform.FileData) and value is not None:
#                tempstore = node.widget.tmpstore.tempstore
#                data[node.name] = node.default
#                if value is not None:
#                    randid = value.split("/")[-1]
#                    for file_uid in tempstore:
#                        if 'randid' in tempstore[file_uid] and (tempstore[file_uid]['randid']) == str(randid):
#                            data[node.name] = tempstore[file_uid]
#                            break
#
#            elif len(node.children):
#                data[node.name] = convert_sqlalchemy_model_to_data(value,  node)
#
#            elif value is None:
#                data[node.name] = node.default
#            else:
#                data[node.name] = value
#        elif len(node.children) > 0:
#            node_data = convert_sqlalchemy_model_to_data(model, node.children)
#
#            # Fix data for select mapping schemas
#            if not ':' in node.name:
#                data['schema_select'] = str(getattr(model, 'method_id', None))
#
#
#            data[node.name] = node_data
#
#    return data

def fix_schema_field_name(field_name):
    return field_name.split(":")[-1]

def convert_schema(schema, **kw):
    schema.title = ''

    if kw.has_key('page'):
        schema = _remove_nodes_not_on_page(schema, kw.pop('page'))

    _force_required(schema)

#    fix_order(schema)

    schema = _group_nodes(schema)

    schema = _prevent_duplicate_fields(schema)

    _remove_admin_fields(schema, "TODO")

    return schema

def _remove_admin_fields(schema, user_rights):
    denied_nodes = []
    for node in schema.children:
        if hasattr(node, 'requires_admin') and node.requires_admin:
#            print "Removed node: " + str(node)
            denied_nodes.append(node)
        else:
            if len(node.children) > 0:
                _remove_admin_fields(node, user_rights)

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

