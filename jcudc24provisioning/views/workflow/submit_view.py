from jcudc24provisioning.views.workflow.workflows import Workflows
from deform.form import Form
from jcudc24provisioning.views.schemas.submit_schema import submit_schema

__author__ = 'Casey Bajema'

from pyramid.view import view_config

class SubmitView(Workflows):
    title = "Submit"

    def __init__(self, request):
        self.request = request
        self.schema = submit_schema(description="<b>Save:</b> Save the project as is, it doesn't need to be fully complete or valid.<br/><br/>"\
                                                "<b>Delete:</b> Delete the project, this can only be performed by administrators or before the project has been submitted.<br/><br/>"\
                                                "<b>Submit:</b> Submit this project for admin approval. If there are no problems the project data will be used to create ReDBox-Mint records as well as configuring data ingestion into persistent storage<br/><br/>"\
                                                "<b>Reopen:</b> Reopen the project for editing, this can only occur when the project has been submitted but not yet accepted (eg. the project may require updates before being approved)<br/><br/>" \
                                                "<b>Approve:</b> Approve this project, generate metadata records and setup data ingestion<br/><br/>" \
                                                "<b>Disable:</b> Stop data ingestion, this would usually occur once the project has finished."
                                                ).bind(request=request)
        self.form = Form(self.schema, action="submit", buttons=('Save', 'Delete', 'Submit', 'Reopen', 'Approve', 'Disable'), use_ajax=False)

    @view_config(renderer="../../templates/form.pt", name="submit")
    def setup_view(self):
        return {"page_title": self.title, "form": self.form.render()}
