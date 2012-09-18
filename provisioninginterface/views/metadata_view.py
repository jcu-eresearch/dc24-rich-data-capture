__author__ = 'Casey Bajema'

import colander
from deform.exception import ValidationFailure
from deform.form import Form
from pyramid.view import view_config
from layouts import Layouts


class MetadataData(colander.MappingSchema):
    parties = colander.SchemaNode(colander.String(), default="To be redeveloped similar to ReDBox")
    activities = colander.SchemaNode(colander.String(), default="Autocomplete - Mint/Mint DB")
    contributors = colander.SchemaNode(colander.String(), default="Plain Text + add more button")
    fieldOfResearch = colander.SchemaNode(colander.String(), title="Fields of Research", default="To be redeveloped similar to ReDBox")
    socioEconomicObjective = colander.SchemaNode(colander.String(), title="Socio-Economic Objectives", default="To be redeveloped similar to ReDBox")

    dataAffiliation = colander.SchemaNode(colander.String(), title="Data Affiliation")
    fundingBody = colander.SchemaNode(colander.String(), title="Funding Body")
    grantNumber = colander.SchemaNode(colander.String(), default="linked", title="Grant Number")
    projectTitle = colander.SchemaNode(colander.String(), title="Project Title")
    depositor = colander.SchemaNode(colander.String())
    institutionalDataManagementPolicy = colander.SchemaNode(colander.String(), title="Institutional Data Management Policy")
    attachFile = colander.SchemaNode(colander.String(), title="Attach File")
    citation = colander.SchemaNode(colander.String(), default="To be redeveloped similar to ReDBox")


class MetaDataView(Layouts):
    def __init__(self, request):
        self.request = request

    @view_config(renderer="../templates/metadata.pt", name="metadata")
    def setup_view(self):
        schema = MetadataData()
        myform = Form(schema, buttons=('submit',))

        if 'submit' in self.request.POST:
            controls = self.request.POST.items()
            try:
                appstruct = myform.validate(controls)
            except ValidationFailure, e:
                return {"page_title": 'Metadata', 'form': e.render(), 'values': False}
                # Process the valid form data, do some work
            values = {
                "name": appstruct['name'],
                "shoe_size": appstruct['shoe_size'],
                }
            return {"page_title": 'Metadata', "form": myform.render(), "values": values}

        # We are a GET not a POST
        return {"page_title": 'Metadata', "form": myform.render(), "values": None}

