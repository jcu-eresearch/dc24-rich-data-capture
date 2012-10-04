from pyramid.view import view_config

__author__ = 'Casey Bajema'

from layouts import Layouts

class DashboardView(Layouts):
    def __init__(self, request):
        self.request = request

    @view_config(renderer="../templates/dashboard.pt")
    def dashboard_view(self):
        return {"page_title": "Provisioning Dashboard"}