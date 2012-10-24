from jcudc24provisioning.views.workflow.workflows import Workflows

__author__ = 'Casey Bajema'

from pyramid.view import view_config

class SubmitView(Workflows):
    title = "Submit"

    def __init__(self, request):
        self.request = request

    @view_config(renderer="../../templates/activate.pt", name="submit")
    def setup_view(self):
        # We are a GET not a POST
        return {"page_title": 'Submit'}


