from fanstatic import Library
from fanstatic import Resource
from fanstatic import Group
from js import jqueryui
from js.jquery_form import jquery_form
from js.jquery import jquery
import js.deform

def open_layers_lookup(url):
    return """<script type="text/javascript" src="http://maps.google.com/maps/api/js?v=3&amp;sensor=false"></script>"""

library = Library('jcudc24provisioning', 'static')
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

# Fix the removal of browser for newer versions of jquery (datepicker relies on it).
jquery_mb_browser = Resource(
    library,
    'libraries/jquery.mb.browser-master/jquery.mb.browser.js',
    bottom=False,
    minified="libraries/jquery.mb.browser-master/jquery.mb.browser.min.js",
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
    jquery_mb_browser,
    jquery,
    jqueryui.jqueryui,
    jqueryui.ui_datepicker,
    jqueryui.ui_datepicker_en_AU,
    jqueryui.base,
    jqueryui.ui_lightness,
    js.deform.deform,
    jquery_form,
    enmasse_widgets
])

enmasse_forms = Group([
    enmasse_requirements,
    regex_mask,
])
