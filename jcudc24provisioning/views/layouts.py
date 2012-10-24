__author__ = 'Casey Bajema'
from pyramid.renderers import get_renderer
from pyramid.decorator import reify

#class Search(colander.MappingSchema):
#    search = colander.SchemaNode(colander.String(), default="Search site")



class Layouts(object):
    def __init__(self, request):
        self.request = request

    @reify
    def global_template(self):
        renderer = get_renderer("../templates/template.pt")
        return renderer.implementation().macros['layout']

    @reify
    def get_message(self):
        return self.request.GET.get('msg')

#    @reify
#    def search_form(self):
#        search = Search()
#        return Form(Search(), action="search", buttons=('Search',)).render()

