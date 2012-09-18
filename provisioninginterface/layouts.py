__author__ = 'Casey Bajema'
from pyramid.renderers import get_renderer
from pyramid.decorator import reify

WORKFLOW_STEPS = [
        {'href': 'setup', 'title': 'Project Setup'},
        {'href': 'metadata', 'title': 'Metadata Collection'},
        {'href': 'data_requirements', 'title': 'Data Requirements'},
        {'href': 'data_inputs', 'title': 'Data Inputs'},
        {'href': 'activate', 'title': 'Activate'},
]

class Layouts(object):
    @reify
    def global_template(self):
        renderer = get_renderer("templates/template.pt")
        return renderer.implementation().macros['layout']

    @reify
    def workflow_template(self):
        renderer = get_renderer("templates/workflow_template.pt")
        return renderer.implementation().macros['layout']

    @reify
    def site_menu(self):
        new_menu = WORKFLOW_STEPS[:]
        url = self.request.url
        for menu in new_menu:
            if menu['title'] == 'Provisioning Dashboard':
                menu['current'] = url.endswith('/')
            else:
                menu['current'] = url.endswith(menu['href'])
        return new_menu
