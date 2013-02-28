#import colander
#import deform
#from jcudc24provisioning.models.common_schemas import SelectMappingSchema
#from jcudc24provisioning.views.workflows import Workflows
#
#__author__ = 'Casey Bajema'
#
#from deform.exception import ValidationFailure
#from deform.form import Form
#from pyramid.view import view_config
#
#class QualityMetadataSchema(colander.MappingSchema):
#    date = colander.SchemaNode(colander.Date())
#    unit = colander.SchemaNode(colander.String(), placeholder="What is the unit of measure for this quality information.", missing="",
#        widget=deform.widget.TextInputWidget(css_class="full_width"), size=15)
#    value = colander.SchemaNode(colander.String(), placeholder="Quality value.", missing="",
#        widget=deform.widget.TextInputWidget(css_class="full_width"), size=100)
#    description = colander.SchemaNode(colander.String(), placeholder="Provide textual information about the selected items.", missing="",
#        widget=deform.widget.TextInputWidget(css_class="full_width"), size=100)
#
#class NoteMetadataSchema(colander.MappingSchema):
#    date = colander.SchemaNode(colander.Date())
#    note = colander.SchemaNode(colander.String(), placeholder="Provide textual information about the selected items.", missing="",
#        widget=deform.widget.TextInputWidget(css_class="full_width"), size=100)
#
#class MetadataSchema(SelectMappingSchema):
#    note = NoteMetadataSchema(widget=deform.widget.MappingWidget(template="inline_mapping"))
#    quality = QualityMetadataSchema()
#
#class AddMetadataSequence(colander.SequenceSchema):
#    information = MetadataSchema(collapsed=False, collapse_group="metadata", collapse_legend="metadata")
#
#class AddMetadataTypeSequence(colander.SequenceSchema):
#    metadata_type = colander.SchemaNode(colander.String(), placeholder="TODO", missing="",
#        widget=deform.widget.TextInputWidget())
#
#class SelectedObjectsSchema(colander.MappingSchema):
#    selected_object_a = colander.SchemaNode(colander.String(), placeholder="TODO", missing="",
#        widget=deform.widget.TextInputWidget(css_class="full_width"), size=100)
#    selected_object_b = colander.SchemaNode(colander.String(), placeholder="TODO", missing="",
#        widget=deform.widget.TextInputWidget(css_class="full_width"), size=100)
#    selected_object_c = colander.SchemaNode(colander.String(), placeholder="TODO", missing="",
#        widget=deform.widget.TextInputWidget(css_class="full_width"), size=100)
#
#class AddMetadataSchema(colander.MappingSchema):
#    selected_objects = SelectedObjectsSchema(description="Selected objects")
#    information = AddMetadataSequence()
#    add_metadata_type = AddMetadataTypeSequence(description="Add new types of metadata that can be added to the selected objects.")
#
#class AddMetadataView(Workflows):
#    title = "Add Metadata"
#
#    def __init__(self, request):
#        self.request = request
#        self.schema = AddMetadataSchema(description="Add metadata to the selected items.").bind(request=request)
#        self.form = Form(self.schema, action="submit_add_metadata", buttons=('Add',), use_ajax=False)
#
#    @view_config(renderer="../../templates/workflow_form.pt", name="submit_add_metadata")   # Use ../../templates/submit.pt for AJAX - File upload doesn't work due to jquery/deform limitations
#    def submit(self):
#        controls = self.request.POST.items()
#        try:
#            appstruct = self.form.validate(controls)
#    #            print "appstruct: " + str(appstruct)
#        except ValidationFailure, e:
#            return  {"page_title": self.title, 'form': e.render(), "form_only": self.form.use_ajax}
#
#        # Process the valid form data, do some work
##        self.form.buttons = ('Delete/Disable', 'Add metadata', 'View related', 'Add metadata type')
#        return {"page_title": self.title, "form": self.form.render(appstruct), "form_only": self.form.use_ajax}
#
#    @view_config(renderer="../../templates/workflow_form.pt", name="add_metadata")
#    def add_metadata_view(self):
#        return {"page_title": self.title, "form": self.form.render(), "form_only": False}
#
