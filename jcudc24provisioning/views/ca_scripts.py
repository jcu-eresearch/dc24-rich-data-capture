import ast
from collections import OrderedDict
from datetime import date
import colander
import deform
import os

import logging
logger = logging.getLogger(__name__)

__author__ = 'Casey Bajema'

# TODO: It may be possible to update these scripts to work better using for prop in object_mapper(source).iterate_properties:

#def embed_child_objects(schema):
#    """
#    If the schema has children that extend Base - they are just schemas grouped
#    """
#    child_index = 0
#    while child_index < len(schema.children):
#
#        if instanceof(schema.children[child_index], Base):
#            child = schema.children[child_index]
#            schema.children.remove(child)
#            index = child_index
#            for sub_child in schema.children[child_index].children:
#                schema.children.insert()
#        else:
#            child_index += 1
#
#    return schema

def create_sqlalchemy_model(data, model_class=None, model_object=None):
    is_data_empty = True
    if model_object is None and model_class is not None:
        model_object = model_class()

    if model_class is None and model_object is not None:
        model_class = model_object._sa_instance_state.class_

    if model_class is None or model_object is None:
        raise ValueError

    for key, value in data.items():
        key = fix_schema_field_name(key)

        if not hasattr(model_object, key) and isinstance(value, dict):
            # This is a grouping - add its fields to the current model_object
            create_sqlalchemy_model(value, model_class=model_class, model_object=model_object)

        elif hasattr(model_object, key):
            # Fix boolean balues as javascript/CheckBoxWidget False value is u'false' which casts to true
            if value == 'false':
                value = False
            elif value == 'true':
                value = True

            ca_registry = None
            if key in model_class._sa_class_manager:
                if hasattr(model_class._sa_class_manager[key].comparator, 'mapper') and key in model_class._sa_class_manager[key].comparator.mapper.columns._data:
                    ca_registry = model_class._sa_class_manager[key].comparator.mapper.columns._data[key]._ca_registry
                elif hasattr(model_class._sa_class_manager[key], '_parententity') and key in model_class._sa_class_manager[key]._parententity.columns._data:
                    ca_registry = model_class._sa_class_manager[key]._parententity.columns._data[key]._ca_registry

            if ca_registry is not None:
                # If this is a file field
                if 'type' in ca_registry and isinstance(ca_registry['type'], deform.FileData):
                    # If this is a new file
                    if isinstance(value, dict) and 'preview_url' in value:
                        value = str(value['preview_url'])

                    # If this is an already selected and uploaded file
                    elif isinstance(value, dict) and 'fp' in value and hasattr(value['fp'], 'name'):
                        value = str(value['fp'].name)

                    # File was previously uploaded and the user just removed it
                    else:
                        value = None

                    if value != getattr(model_object, key):
                        setattr(model_object, key, value)
                        is_data_empty = False
                    continue

            # If the value hasn't been changed
            if not isinstance(value, dict) and not isinstance(value, list) and (value == getattr(model_object, key) or
                                                                                 (isinstance(getattr(model_object, key), bool) and bool(value) == getattr(model_object, key))):
                continue

            # If the value is now empty and it was set previously
            elif value is colander.null or value is None or value == 'None' or value == 'colander.null':
                # If the attribute is a list there is no need to set the value
                if isinstance(getattr(model_object, key), list):
                    setattr(model_object, key, [])
                else:
                    setattr(model_object, key, None)
                continue

            elif isinstance(value, list):

                # Remove all items from the list, so that any items that aren't there are deleted.
                old_items = []
                for i in reversed(range(len(getattr(model_object, key, [])))):
                    old_items.append(getattr(model_object, key)[i])

                for item in value:
                    if not item or item is colander.null:
                        continue

                    if 'schema_select' in item and len(item) == 2:  # This is the custom developed select mapping - flatten the select out
                        method = item.pop('schema_select')
                        item = item.values()[0]

                    current_object = None

                    if len(item) == 0:
                        continue

                    prefix = item.items()[0][0].split(":")[0] + ":"

                    if prefix + 'id' in item and (isinstance(item[prefix + 'id'], (long, int)) or (isinstance(item[prefix + 'id'], basestring) and item[prefix + 'id'].isnumeric())):
                        for model_item in old_items:
#                            print "ID's: " + str(getattr(model_item, 'id', None)) + " : " + str(item['id'])
                            current_object_id = getattr(model_item, 'id', None)
#                            print (isinstance(current_object_id, (int, long)) or (isinstance(current_object_id, basestring) and current_object_id.isnumeric()))
                            if (isinstance(current_object_id, (int, long)) or (isinstance(current_object_id, basestring) and current_object_id.isnumeric())) and int(getattr(model_item, 'id', None)) == int(item[prefix + 'id']):
                                current_object = model_item
                                old_items.remove(current_object)
#                                print "Current Object: " + str(current_object)
                                break

                    child_table_object = create_sqlalchemy_model(item, model_class=model_object._sa_class_manager[key].property.mapper.class_, model_object=current_object)
                    if child_table_object is not None:
                        is_data_empty = False
                        getattr(model_object, key).append(child_table_object) # Add the modified object
                    elif current_object is not None:
                        getattr(model_object, key).append(current_object) # Re-add the un-modified object

                for item in old_items:
                    getattr(model_object, key).remove(item)
                    del item
                    is_data_empty = False

            elif isinstance(value, dict):
                current_object = None
                if getattr(model_object, key, None) is not None:
                    current_object = getattr(model_object, key, None)

                if not hasattr(model_object._sa_class_manager[key].property, 'mapper'):
                    raise AttributeError("Model conversion scripts have an error, trying to generate a model with invalid values.")
                child_table_object = create_sqlalchemy_model(value, model_class=model_object._sa_class_manager[key].property.mapper.class_, model_object=current_object)

                if child_table_object is not None:
                    setattr(model_object, key, child_table_object)
                    is_data_empty = False
            else:
                # TODO: Need a more reliable way of doing this, these seem to change version to version.
                try:
                    if key in model_class._sa_class_manager:
                        if ('default' not in ca_registry or not value == ca_registry['default']) and str(value) != str(getattr(model_object, key, None)):
                            setattr(model_object, key, value)
                            is_data_empty = False
                except Exception as e:
                    logger.exception("Failed to set model attribute: %s" % key)
                    continue

    if is_data_empty:
        return None

    return model_object

def convert_sqlalchemy_model_to_data(model, schema):
    data = {}

    if model is None:
        return data

    for node in schema:
        name = fix_schema_field_name(node.name)

        if hasattr(model, name):
            value = getattr(model, name, None)

            if isinstance(value, date):
                value = str(value)

            if isinstance(value, bool)  and hasattr(node.widget, 'true_val'):
                if value:
                    value = node.widget.true_val
                elif hasattr(node.widget, 'false_val'):
                    value = node.widget.false_val

            if isinstance(value, list):
                node_list = []
                for item in value:
                    node_list.append(convert_sqlalchemy_model_to_data(item,  node.children[0]))

                data[node.name] = node_list
            elif isinstance(node.typ, deform.FileData) and value is not None:
                tempstore = node.widget.tmpstore.tempstore
                data[node.name] = node.default
                if value is not None:
                    randid = value.split("/")[-1]
                    for file_uid in tempstore:
                        if 'randid' in tempstore[file_uid] and (tempstore[file_uid]['randid']) == str(randid):
                            data[node.name] = tempstore[file_uid]
                            break

            elif len(node.children):
                data[node.name] = convert_sqlalchemy_model_to_data(value,  node)

            elif value is None:
                data[node.name] = node.default
            else:
                data[node.name] = value
        elif len(node.children) > 0:
            node_data = convert_sqlalchemy_model_to_data(model, node.children)

            # Fix data for select mapping schemas
            if not ':' in node.name:
                data['schema_select'] = str(getattr(model, 'method_id', None))


            data[node.name] = node_data

    return data

def fix_schema_field_name(field_name):
    return field_name.split(":")[-1]

def convert_schema(schema, **kw):
    schema.title = ''

    if kw.has_key('page'):
        schema = remove_nodes_not_on_page(schema, kw.pop('page'))

    force_required(schema)

#    fix_order(schema)

    schema = group_nodes(schema)

    schema = prevent_duplicate_fields(schema)

    remove_admin_fields(schema, "TODO")

    return schema

def remove_admin_fields(schema, user_rights):
    denied_nodes = []
    for node in schema.children:
        if hasattr(node, 'requires_admin') and node.requires_admin:
#            print "Removed node: " + str(node)
            denied_nodes.append(node)
        else:
            if len(node.children) > 0:
                remove_admin_fields(node, user_rights)

    for node in denied_nodes:
        schema.children.remove(node)

    return schema

#def fix_order(node):
#    oredering_node = node._reg.cls()
#
#    for child in node.children:
#        source = inspect.getsourcelines(child)
##        print str(child.title) + " : " + str(child._order)
#        if isinstance(child, colander.MappingSchema):
#            fix_order(child)
#        elif isinstance(child.typ, colander.Sequence):
#            fix_order(child.children[0])
#        else:
#            child.order = node._reg.attrs[child.name].node_order
#
##        for attr in inspect.getmembers(child):
##            if attr[0] == "_order":
##                child.order = attr[1]

def prevent_duplicate_fields(schema):
    for node in schema.children:
        node.name = schema.name + ":" + node.name

        if isinstance(node.typ, colander.Sequence):
            prevent_duplicate_fields(node.children[0])
        elif len(node.children) > 0:
            node = prevent_duplicate_fields(node)
    return schema

def force_required(schema):
    for node in schema.children:
        if len(node.children) > 0:
            force_required(node)

        if hasattr(node, 'force_required') and node.force_required:
            setattr(node, 'missing', colander._marker)
        elif hasattr(node, 'force_required') and not node.force_required:
            setattr(node, 'missing', node.default)


def remove_nodes_not_on_page(schema, page):
    children_to_remove = []

    for child in schema.children:
        if len(child.children) > 0:
            remove_nodes_not_on_page(child, page)

        if hasattr(child, 'page') and child.page != page:
            children_to_remove.append(child)

    for child in children_to_remove:
        schema.children.remove(child)

    return schema

def fix_sequence_schemas(sequence_node):
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

def group_nodes(node):
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
            fix_sequence_schemas(child)
            group_nodes(child.children[0])
        elif len(child.children) > 0:
            child = group_nodes(child)

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

def ungroup_nodes(node):
    children_to_add = {}

    for child in node.children:

        if isinstance(child.typ, colander.Mapping) and not hasattr(child, "__tablename__"):
            child = ungroup_nodes(child)
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

