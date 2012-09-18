__author__ = 'Casey Bajema'

from pyramid.view import view_config
from layouts import Layouts

class ActivateView(Layouts):
    def __init__(self, request):
        self.request = request

    @view_config(renderer="../templates/activate.pt", name="activate")
    def setup_view(self):
        # We are a GET not a POST
        return {"page_title": 'Activate'}


