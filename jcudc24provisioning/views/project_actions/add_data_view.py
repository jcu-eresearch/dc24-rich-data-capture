import colander
import deform
from jcudc24provisioning.models.common_schemas import Attachment
from jcudc24provisioning.views.workflows import Workflows

__author__ = 'Casey Bajema'

from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.view import view_config


datasets = (
    ('dataset1', 'Dataset 1'),
    ('dataset2', 'Dataset 2'),
    ('dataset3', 'Dataset 3'),
    ('dataset4', 'Dataset 4'),
    ('dataset5', 'Dataset 5'),
    )

class DataSchema(colander.MappingSchema):
    dataset = colander.SchemaNode(colander.String(), title="Select Dataset",
        widget=deform.widget.SelectWidget(values=datasets),
        description="Select the dataset that you would like to add data to")
    description = colander.SchemaNode(colander.String(),
        placeholder="A textual description of the data", missing="")
    date = colander.SchemaNode(colander.Date(), placeholder="", title="Date",
        description='Date the data was collected.')
    data = Attachment(title="Data File")

class AddDataSequence(colander.SequenceSchema):
    data = DataSchema(collapsed=False, collapse_group="data")

class AddDataSchema(colander.MappingSchema):
    data = AddDataSequence(widget=deform.widget.SequenceWidget(min_len=1))

class View(Workflows):
    title = "Add data"

    def __init__(self, request):
        self.request = request
        self.schema = AddDataSchema(description="Manually enter or upload data for a specific dataset.<br/><br/><b>TODO: Generate form on the fly based off the data type schema</b>",
                collapsed=False, collapse_group="add_data").bind(request=request)
        self.form = Form(self.schema, action="submit_add_data", buttons=('Save',), use_ajax=False)

    @view_config(renderer="../../templates/form.pt", name="submit_add_data")   # Use ../../templates/submit.pt for AJAX - File upload doesn't work due to jquery/deform limitations
    def submit(self):
        controls = self.request.POST.items()
        try:
            appstruct = self.form.validate(controls)
    #            print "appstruct: " + str(appstruct)
        except ValidationFailure, e:
            return  {"page_title": self.title, 'form': e.render(), "form_only": self.form.use_ajax}

        # Process the valid form data, do some work
        return {"page_title": self.title, "form": self.form.render(appstruct), "form_only": self.form.use_ajax}

    @view_config(renderer="../../templates/form.pt", name="add_data")
    def add_data_view(self):
        return {"page_title": self.title, "form": self.form.render(), "form_only": False}

