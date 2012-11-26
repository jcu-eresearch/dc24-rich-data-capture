from collections import OrderedDict
import colander
from colanderalchemy.types import SQLAlchemyMapping
from pyramid.response import Response
from jcudc24provisioning.models.setup_schema import SetupSchema
from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.view import view_config
from jcudc24provisioning.views.workflow.workflows import Workflows
from models.project import ProjectSchema

__author__ = 'Casey Bajema'

def convert_schema(schema, **kw):
    schema.title = ''

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
                parent_group = groups[groups.index(child.group_start) - 1]
                mappings[parent_group].children.append(mappings[child.group_start])
            else:
                node.children.insert(node.children.index(child), mappings[group])

        if isinstance(child, colander.MappingSchema):
            child = group_nodes(child)

        if len(groups) > 0:
            print "Move child to group: " + str(child.name) + " group: " + str(groups[len(groups) - 1])

            # If the child is replaced by a mapping schema, delete it now - otherwise delete it later
            # This is to prevent the models children from changing while they are being iterated over.
            if hasattr(child, 'group_start'):
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


class SetupViews(Workflows):
    title = "Project Setup"

    def __init__(self, request):
        self.request = request
        self.schema = convert_schema(SQLAlchemyMapping(ProjectSchema, unknown='raise', ca_description=""), page='setup').bind(request=request)

        self.form = Form(self.schema, action="setup", buttons=('Save',), use_ajax=False)

    @view_config(renderer="../../templates/form.pt", name="setup")
    def submit(self):
        if self.request.POST.get('Delete') == 'confirmed':
            location = self.request.application_url + '/'
            message = 'Project successfully deleted'
            return Response(self.form.render(),
                headers=[('X-Relocate', location), ('Content-Type', 'text/html'), ('msg', message)])

        if 'Save' in self.request.POST:
            controls = self.request.POST.items()
            try:
                appstruct = self.form.validate(controls)
            except ValidationFailure, e:
                return  {"page_title": 'Project Setup', 'form': e.render(), "form_only": self.form.use_ajax}
                # Process the valid form data, do some work
        return {"page_title": 'Project Setup', "form": self.form.render(), "form_only": False}
