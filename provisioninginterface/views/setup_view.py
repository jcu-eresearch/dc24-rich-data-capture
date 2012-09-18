import deform

__author__ = 'Casey Bajema'

import colander
from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.view import view_config
from layouts import Layouts


class SetupData(colander.MappingSchema):
    title = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String())
    primaryContact = colander.SchemaNode(colander.String(), title="Primary Contact")
    url = colander.SchemaNode(colander.String(), default="", title="Project Website", description="Link to related data about this project.")

    keywords = colander.SchemaNode(colander.String(), default="+ add more button")
    accessRights = colander.SchemaNode(colander.String(), title="Access Rights")
    accessRightsURL = colander.SchemaNode(colander.String(), title="Link to Access Rights")
    rights = colander.SchemaNode(colander.String())
    rightsURL = colander.SchemaNode(colander.String(), title="Link to Rights")
    license = colander.SchemaNode(colander.String())

    retentionPeriod = colander.SchemaNode(colander.String(), title="Retention Period")
    disposalDate = colander.SchemaNode(colander.Date(), title="Disposal Date", widget=deform.widget.DatePartsWidget(), description='Date that the data should be deleted')
    archivalDate = colander.SchemaNode(colander.Date(), title="Archival Date", widget=deform.widget.DatePartsWidget(), description='Date that the data should be deleted')
    dataOwner = colander.SchemaNode(colander.String(), title="Data Owner (IP)")
    dataCustodian = colander.SchemaNode(colander.String(), title="Data Custodian")




class SetupViews(Layouts):
    def __init__(self, request):
        self.request = request

    @view_config(renderer="../templates/setup.pt", name="setup")
    def setup_view(self):
        schema = SetupData()
        myform = Form(schema, buttons=('submit',))

        if 'submit' in self.request.POST:
            controls = self.request.POST.items()
            try:
                appstruct = myform.validate(controls)
            except ValidationFailure, e:
                return {"page_title": 'Project Setup', 'form': e.render(), 'values': False}
                # Process the valid form data, do some work
            values = {
                "name": appstruct['name'],
                "shoe_size": appstruct['shoe_size'],
                }
            return {"page_title": 'Project Setup', "form": myform.render(), "values": values}

        # We are a GET not a POST
        return {"page_title": 'Project Setup', "form": myform.render(), "values": None}

