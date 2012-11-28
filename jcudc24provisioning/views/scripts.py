
from collections import OrderedDict
import colander
from jcudc24provisioning.models import Base

__author__ = 'Casey Bajema'

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


def convert_schema(schema, **kw):
    schema.title = ''

    print schema.children
    if kw.has_key('page'):
        schema = remove_nodes_not_on_page(schema, kw.pop('page'))

    schema = group_nodes(schema)

    return schema

def remove_nodes_not_on_page(schema, page):
    children_to_remove = []

    for child in schema.children:
        if hasattr(child, 'page') and child.page != page:
            children_to_remove.append(child)

    for child in children_to_remove:
        schema.children.remove(child)

    return schema


def group_nodes(node):
    mappings = OrderedDict()
    groups = []
    chilren_to_remove = []
    for child in node.children:
        print "child: " + str(child.name)

        if hasattr(child, "group_start"):
            group = child.__dict__.pop("group_start")
            group_params = {}

            for param in child.__dict__.copy():
                if param[:6] == 'group_':
                    group_params[param[6:]] = child.__dict__.pop(param)

            group = child.__dict__["group_start"] = group # Need to re-add the group_start attribute for the logic below.

            groups.append(group)
            mappings[group] = colander.MappingSchema(name=group, collapse_group=group,
                **group_params)

            if len(groups) > 1:
                parent_group = groups[groups.index(group) - 1]
                mappings[parent_group].children.append(mappings[group])
            else:
                node.children.insert(node.children.index(child), mappings[group])

        if isinstance(child, colander.MappingSchema):
            child = group_nodes(child)

        if len(groups) > 0:
            print "Move child to group: " + str(child.name) + " group: " + str(groups[len(groups) - 1])

            # If the child is replaced by a mapping schema, delete it now - otherwise delete it later
            # This is to prevent the models children from changing while they are being iterated over.
            if hasattr(child, 'group_start') and len(groups) == 1:
                node.children.remove(child)
            else:
                chilren_to_remove.append(child)

            mappings[groups[len(groups) - 1]].children.append(child)

        if hasattr(child, "group_end"):
            print "End group: " + str(child.group_end)
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
        print "Ungroup child: " + str(child.name)

        if isinstance(child.typ, colander.Mapping) and not hasattr(child, "__tablename__"):
            child = ungroup_nodes(child)
            index = node.children.index(child)
            node.children.remove(child)
            print "Remove mapping: " + str(child.name)
            node.children.insert(index, child.children[0])
            print "insert child: " + str(child.children[0].name)

            children_to_add[index] = child.children[1:]
            print children_to_add

    print children_to_add.items()

    for index, mapping_children in children_to_add.items():
        for child in mapping_children:
            index += 1
            node.children.insert(index, child)
            print "insert child: " + str(child.name) + " at " + str(index)

    return node