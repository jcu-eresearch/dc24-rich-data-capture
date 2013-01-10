from pkg_resources import declare_namespace
from . import models
from models.initialise_templates import InitialiseData

declare_namespace('jcudc24provisioning')

from deform.form import Form
from pyramid.config import Configurator
from pkg_resources import resource_filename
from pyramid_beaker import session_factory_from_settings, set_cache_regions_from_settings
from sqlalchemy.engine import engine_from_config
from models.project import Project, DBSession, Base

__author__ = 'Casey Bajema'


def main(global_config, **settings):
#def main():
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)

    deform_templates = resource_filename('deform', 'templates')
    search_path = (resource_filename('jcudc24provisioning', 'templates/widgets'),resource_filename('jcudc24provisioning', 'templates/widgets/readonly'), deform_templates)
    Form.set_zpt_renderer(search_path)

    set_cache_regions_from_settings(settings)
    my_session_factory = session_factory_from_settings(settings)
    configurator = Configurator(settings=settings, session_factory = my_session_factory)

    configurator.add_static_view('deform_static', 'deform:static', cache_max_age=0)
    configurator.add_static_view('static', 'static')
    configurator.scan()

    InitialiseData()

    return configurator.make_wsgi_app()



#if __name__ == '__main__':
#    app = main("serve ../development.ini")
#    server = make_server('0.0.0.0', 8080, app)
#    server.serve_forever()
