import colander
import deform
from jcudc24provisioning.views.project_actions.add_metadata import AddMetadataView
from views.workflows import Workflows

__author__ = 'Casey Bajema'

from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.view import view_config

class SearchResult(colander.MappingSchema):
    selected = colander.SchemaNode(colander.Boolean(), title="", missing="")
    result = colander.SchemaNode(colander.String(), missing="", title="", placeholder="TODO: Results", widget=deform.widget.TextInputWidget(css_class="full_width", size=100))

class SearchResults(colander.MappingSchema):
    toggle_all = colander.SchemaNode(colander.Boolean(), missing="")
    result_a = SearchResult(widget=deform.widget.MappingWidget(template="inline_mapping"))
    result_b = SearchResult(widget=deform.widget.MappingWidget(template="inline_mapping"))
    result_c = SearchResult(widget=deform.widget.MappingWidget(template="inline_mapping"))

object_types = (
    ('data','Data'),
    ('dataset','Dataset'),
    ('metadata','Metadata'),
    ('region','Region'),
    ('location','Location'),
)

class DataRange(colander.MappingSchema):
    date_from = colander.SchemaNode(colander.Date(), placeholder="",
        missing=colander.null)
    date_to = colander.SchemaNode(colander.Date(), placeholder="",
        missing=colander.null)

class SearchSchema(colander.MappingSchema):
    dataset = colander.SchemaNode(colander.String(), title="Select focus of metadata",
        widget=deform.widget.SelectWidget(values=object_types),
        description="Select the type of data that the metadata is attached to.")
    date_range = DataRange(description="Date range to search over (Date of creation)", widget=deform.widget.MappingWidget(template="inline_mapping"), missing=colander.null)
    region_or_location = colander.SchemaNode(colander.String(), placeholder="TODO: Autocomplete of region and location names", missing=colander.null)
    description = colander.SchemaNode(colander.String(), placeholder="textual search on the description/text fields", missing="",)

class ManageDataSchema(colander.MappingSchema):
    search = SearchSchema(title="Search for datasets or data",
        description="Find dataset's or data entries to add metadata to.  <b>TODO: Search under development.</b>")

class ManageDataResultsSchema(colander.MappingSchema):
    search = SearchSchema(title="Search for datasets or data",
        description="Find dataset's or data entries to add metadata to.  <b>TODO: Search under development.</b>")
    search_results = SearchResults()


class View(Workflows):
    title = "Manage Data"

    def __init__(self, request):
        self.request = request
        self.schema = ManageDataSchema(description="Attach metadata to data already added, such as quality information or notes.  The intent of adding metadata to persistent storage is post markup information about the data, not as actual data itself.<br/><br/><b>TODO: Generate form on the fly based off the models</b>").bind(request=request)
        self.form = Form(self.schema, action="submit_manage_data", buttons=('Search',), use_ajax=False)

    @view_config(renderer="../../templates/form.pt", name="submit_manage_data")   # Use ../../templates/submit.pt for AJAX - File upload doesn't work due to jquery/deform limitations
    def submit(self):
        controls = self.request.POST.items()
        try:
            appstruct = self.form.validate(controls)
    #            print "appstruct: " + str(appstruct)
        except ValidationFailure, e:
            return  {"page_title": self.title, 'form': e.render(), "form_only": self.form.use_ajax}

        if self.request.POST.get('Add_metadata'):
            location = self.request.application_url + '/add_metadata'
            return AddMetadataView(self.request).add_metadata_view()


        # Process the valid form data, do some work
#        self.form.buttons = ('Delete/Disable', 'Add metadata', 'View related', 'Add metadata type')
        self.schema = ManageDataResultsSchema(description="Attach metadata to data already added, such as quality information or notes.  The intent of adding metadata to persistent storage is post markup information about the data, not as actual data itself.<br/><br/><b>TODO: Generate form on the fly based off the models</b>").bind(request=self.request)
        self.form = Form(self.schema, action="submit_manage_data", buttons=('Delete/Disable', 'Add metadata', 'View everything related'), use_ajax=False)
        return {"page_title": self.title, "form": self.form.render(appstruct), "form_only": self.form.use_ajax}

    @view_config(renderer="../../templates/form.pt", name="manage_data")
    def add_data_view(self):
        return {"page_title": self.title, "form": self.form.render(), "form_only": False}

