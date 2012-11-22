from collections import OrderedDict
import colander
from colanderalchemy.types import SQLAlchemyMapping
from pyramid.response import Response
from jcudc24provisioning.views.schemas.setup_schema import SetupSchema
from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.view import view_config
from jcudc24provisioning.views.workflow.workflows import Workflows

__author__ = 'Casey Bajema'

def convert_schema(schema):
    schema = group_nodes(schema)
    schema = ungroup_nodes(schema)

    return schema

def group_nodes(node):
    mappings = OrderedDict()
    groups = []
    chilren_to_remove = []
    for child in node.children:
        print "child: " + str(child.name)

        if hasattr(child, "group_start"):
            print "Start group: " + str(child.group_start)
            groups.append(child.group_start)
            mappings[child.group_start] = colander.MappingSchema(name=child.group_start,
                description=getattr(child, 'group_description', colander.null),
                collapsed=getattr(child, 'group_collapsed', False), collapse_group=child.group_start)

            if len(groups) > 1:
                parent_group = groups[groups.index(child.group_start) - 1]
                mappings[parent_group].children.append(mappings[child.group_start])
            else:
                node.children.insert(node.children.index(child), mappings[child.group_start])

        if isinstance(child, colander.MappingSchema):
            child = group_nodes(child)

        if len(groups) > 0:
            print "Move child to group: " + str(child.name) + " group: " + str(groups[len(groups) - 1])

            # If the child is replaced by a mapping schema, delete it now - otherwise delete it later
            # This is to prevent the schemas children from changing while they are being iterated over.
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

            children_to_add[index] = child.children
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
        self.schema = convert_schema(SQLAlchemyMapping(SetupSchema, unknown='raise',
            ca_description="Fully describe this project and the key people responsible for the project:"\
                           "<ul><li>The entered title and description will be used for metadata record generation, provide detailed information that is relevant to the project as a whole and all datasets.</li>"\
                           "<li>Focus on what is being researched, why it is being researched and who is doing the research. The research locations and how the research is being conducted will be covered in the <i>Methods</i> and <i>Datasets</i> steps</li></ul>")).bind(
            request=request)

        self.form = Form(self.schema, action="submit_setup", buttons=('Save', 'Delete'), use_ajax=False)

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
