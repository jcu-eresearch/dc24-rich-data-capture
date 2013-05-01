from fanstatic import Library
from fanstatic import Resource
from fanstatic import Group
from js.jqueryui import jqueryui
from js.jquery_form import jquery_form
from js.jquery import jquery
import js.deform
from js.jqueryui import ui_lightness

def open_layers_lookup(url):
    return """<script type="text/javascript" src="http://maps.google.com/maps/api/js?v=3&amp;sensor=false"></script>"""

library = Library('jcu.enmasse', 'static')
#Third-party resources
open_layers = Resource(
    library,
    'libraries/openlayers/OpenLayers.js',
    bottom=False,
)

enmasse_widgets = Resource(
    library,
    'scripts/widgets.js',
    bottom=False,
    depends=(jquery, open_layers, js.deform.deform_js)
)

regex_mask = Resource(
    library,
    'libraries/jquery-regex-mask-plugin-master/regex-mask-plugin.js',
    bottom=False,
    depends=()
)

deform_css = Resource(
    library,
    'css/deform.css',
    depends=(js.deform.deform_css,)
)

project_css = Resource(
    library,
    'css/project.css',
)
website_css = Resource(
    library,
    'css/website.css',
)
template_css = Resource(
    library,
    'css/template.css',
)

#Local resources
open_layers_js = Resource(library, 'libraries/open_layers.js', renderer=open_layers_lookup)

enmasse_css = Group([
    deform_css,
    project_css,
    website_css,
    template_css,

])

enmasse_requirements = Group([
    enmasse_css,
    jquery,
    jqueryui,
    ui_lightness,
    js.deform.deform,
    jquery_form,
])

enmasse_forms = Group([
    enmasse_requirements,
    enmasse_css,
    enmasse_widgets,
    regex_mask,
])
