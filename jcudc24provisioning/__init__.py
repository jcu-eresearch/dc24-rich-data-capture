

global global_settings

import logging
logger = logging.getLogger(__name__)

# This line is only required for activiting the virtualenv within the IntelliJ IDE
try:
#    execfile("D:/Repositories/JCU-DC24/venv/Scripts/activate_this.py", dict(__file__="D:/Repositories/JCU-DC24/venv/Scripts/activate_this.py"))
    execfile("../../venv/Scripts/activate_this.py", dict(__file__="../../venv/Scripts/activate_this.py"))
except Exception as e:
    logger.exception("Virtual env activation failed, please update the activate_this.py address in the base __init__ if developing on a windows machine.")

import jcudc24provisioning
from deform.form import Form
from pyramid.config import Configurator
from pkg_resources import resource_filename
from pyramid_beaker import session_factory_from_settings, set_cache_regions_from_settings

from pkg_resources import declare_namespace
from . import models
import sys
import scripts.initializedb

declare_namespace('jcudc24provisioning')

__author__ = 'Casey Bajema'


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    jcudc24provisioning.global_settings = settings

    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARN)
    logging.captureWarnings(True)
#    execfile("D:/Repositories/JCU-DC24/venv/Scripts/activate_this.py", dict(__file__="D:/Repositories/JCU-DC24/venv/Scripts/activate_this.py"))

#def main():
    scripts.initializedb.initialise_all_db(settings)

    deform_templates = resource_filename('deform', 'templates')
    search_path = (resource_filename('jcudc24provisioning', 'templates/widgets'),resource_filename('jcudc24provisioning', 'templates/widgets/readonly'), resource_filename('jcudc24provisioning', 'templates/custom_widgets'), resource_filename('jcudc24provisioning', 'templates/custom_widgets/readonly'), deform_templates)
    Form.set_zpt_renderer(search_path)

    set_cache_regions_from_settings(settings)
    my_session_factory = session_factory_from_settings(settings)
    config = Configurator(settings=settings, session_factory = my_session_factory)

    config.add_route('dashboard', '/')                                      # Home page/user dashboard
    config.add_route('login', '/login')                                     # Login page
    config.add_route('search', '/search_page')                                   # Search and manage projects and data
    config.add_route('browse', '/project')                                     # administer user permissions + view admin required items
    config.add_route('admin', '/admin')                                     # administer user permissions + view admin required items
    config.add_route('help', '/help')                                     # administer user permissions + view admin required items

#    ---------------Project/Workflow pages------------------------
    config.add_route('share', '/project/share')                             # Set project permissions
    config.add_route('create', '/project/create')              # Project creation wizard - templates, pre-fill etc.
    config.add_route('general', '/project/{project_id}/general')              # Project creation wizard - templates, pre-fill etc.
    config.add_route('description', '/project/{project_id}/description')    # descriptions
    config.add_route('information', '/project/{project_id}/information')    # metadata or associated information
    config.add_route('methods', '/project/{project_id}/methods')            # Data collection methods
    config.add_route('datasets', '/project/{project_id}/datasets')          # Datasets or collections of data
    config.add_route('view_record', '/project/{project_id}/datasets/view_record/{dataset_id}')          # Datasets or collections of data
    config.add_route('edit_record', '/project/{project_id}/datasets/edit_record/{dataset_id}')          # Datasets or collections of data
    config.add_route('delete_record', '/project/{project_id}/datasets/delete_record/{dataset_id}')          # Datasets or collections of data
    config.add_route('submit', '/project/{project_id}/submit')              # Submit, review and approval
    config.add_route('manage', '/project/{project_id}/manage')              # Manage projecct data, eg. change sample rates, add data values

    # Project action pages
    config.add_route('dataset_logs', '/project/{project_id}/logs/dataset_{dataset_id}_logs.txt')
    config.add_route('logs', '/project/{project_id}/logs')
    config.add_route('add_data', '/project/{project_id}/add_data')
    config.add_route('manage_data', '/project/{project_id}/manage_data')
    config.add_route('permissions', '/project/{project_id}/permissions')
    config.add_route('duplicate', '/project/{project_id}/duplicate')

    # Exception handler
    config.add_route('workflow_exception', '/project/{route:.*}')

#    --------------JSON Search views--------------------------------
    config.add_route('get_model', '/get_model/{object_type}/{id}', xhr=True)
    config.add_route('add_method_from_template', '/add/{project_id}/{method_id}', xhr=True)

    config.add_route('get_activities', '/search/activities/{search_terms}', xhr=True)
    config.add_route('get_parties', '/search/parties/{search_terms}', xhr=True)
    config.add_route('get_from_identifier', '/search/{identifier:.*}', xhr=True)

    #    --------------Static resources--------------------------------
    config.add_static_view('deform_static', 'deform:static', cache_max_age=0)
    config.add_static_view('static', 'static')


    config.scan()

#    try:
#        InitialiseDatabase()
#    except Exception as e:
#        logger.exception("Error initialising database: %s", e)
#        sys.exit()

    return config.make_wsgi_app()



#if __name__ == '__main__':
#    app = main("serve ../development.ini")
#    server = make_server('0.0.0.0', 8080, app)
#    server.serve_forever()
