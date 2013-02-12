#import colander
#import deform
#from jcudc24provisioning.views.workflows import Workflows
#
#__author__ = 'Casey Bajema'
#
#from deform.exception import ValidationFailure
#from deform.form import Form
#from pyramid.view import view_config
#
#permissions = (
#    ('view','View only'),
#    ('full','Full access'),
#)
#
#class UserSchema(colander.MappingSchema):
#    user = colander.SchemaNode(colander.String(),
#        placeholder="TODO:  Autocomplete on users", widget=deform.widget.TextInputWidget(size=100, css_class="full_width"))
#    view_only = colander.SchemaNode(colander.String(), title="User Permissions", widget=deform.widget.RadioChoiceWidget(values=permissions))
#
#class AddUserSequence(colander.SequenceSchema):
#    user = UserSchema(widget=deform.widget.MappingWidget(template="inline_mapping"))
#
#class SharingSchema(colander.MappingSchema):
#    users = AddUserSequence()
#
#class View(Workflows):
#    title = "Sharing"
#
#    def __init__(self, request):
#        self.request = request
#        self.schema = SharingSchema(description="Share this project with other users").bind(request=request)
#        self.form = Form(self.schema, action="submit_sharing", buttons=('Save',), use_ajax=False)
#
#    @view_config(renderer="../../templates/form.pt", name="submit_sharing")   # Use ../../templates/submit.pt for AJAX - File upload doesn't work due to jquery/deform limitations
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
#    @view_config(renderer="../../templates/form.pt", name="sharing")
#    def add_data_view(self):
#        return {"page_title": self.title, "form": self.form.render(), "form_only": False}
#
