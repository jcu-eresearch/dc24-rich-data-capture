from pyramid.decorator import reify
from views.layouts import Layouts
from pyramid.renderers import get_renderer

__author__ = 'Casey Bajema'

WORKFLOW_STEPS = [
        {'href': 'setup', 'title': 'General'},
        {'href': 'metadata', 'title': 'Metadata'},
        {'href': 'methods', 'title': 'Methods'},
        {'href': 'datasets', 'title': 'Datasets'},
        {'href': 'submit', 'title': 'Submit'},
]

redirect_options = """
        {success:
            function (rText, sText, xhr, form) {
                var loc = xhr.getResponseHeader('X-Relocate');
                var msg = xhr.getResponseHeader('msg');
                if (loc) {
                    document.location = loc + ((msg) ? '?msg=' + msg : '');

                }
            }
        }
        """

class MemoryTmpStore(dict):
    """ Instances of this class implement the
    :class:`deform.interfaces.FileUploadTempStore` interface"""
    def preview_url(self, uid):
        return None

class Workflows(Layouts):
    def __init__(self, request):
        self.request = request

    @reify
    def workflow_menu(self):
        new_menu = WORKFLOW_STEPS[:]
        url = self.request.url
        for menu in new_menu:
            menu['current'] = url.endswith(menu['href'])
        return new_menu

    @reify
    def workflow_template(self):
        renderer = get_renderer("../../templates/workflow_template.pt")
        return renderer.implementation().macros['layout']

    @reify
    def isDelete(self):
        return 'Delete' in self.request.POST