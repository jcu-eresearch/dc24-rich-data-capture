from jcudc24provisioning.models import DBSession
from sqlalchemy.engine import engine_from_config

__author__ = 'Casey Bajema'

from deform.form import Form
from pyramid.config import Configurator
from pkg_resources import resource_filename
from pyramid_beaker import session_factory_from_settings, set_cache_regions_from_settings

def main(global_config, **settings):
#def main():
    """ This function returns a Pyramid WSGI application.
    """

    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)

    deform_templates = resource_filename('deform', 'templates')
    search_path = (resource_filename('jcudc24provisioning', 'templates\widgets'), deform_templates)
    Form.set_zpt_renderer(search_path)

    set_cache_regions_from_settings(settings)
    my_session_factory = session_factory_from_settings(settings)
    config = Configurator(settings=settings, session_factory = my_session_factory)

    config.add_static_view('deform_static', 'deform:static', cache_max_age=0)
    config.add_static_view('static', 'static')
    config.scan()
    return config.make_wsgi_app()



#if __name__ == '__main__':
#    app = main("serve ../development.ini")
#    server = make_server('0.0.0.0', 8080, app)
#    server.serve_forever()