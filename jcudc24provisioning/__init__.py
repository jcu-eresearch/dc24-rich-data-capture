"""
Initialise and start the EnMaSSe provisioning interface application.
"""
from paste.deploy.converters import asint
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import NO_PERMISSION_REQUIRED
from controllers.sftp_filesend import SFTPFileSend
from jcudc24provisioning.controllers.authentication import RootFactory, DefaultPermissions
from jcudc24provisioning.controllers.authentication import ShibbolethAuthenticationPolicy, get_user
from jcudc24provisioning.controllers.authentication import ShibbolethAuthenticationPolicy, get_user
from jcudc24provisioning.scripts.create_redbox_config import create_json_config
from pyramid_mailer.mailer import Mailer

import os

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
    Form.set_zpt_renderer(search_path, encoding="latin-1")

    set_cache_regions_from_settings(settings)
    my_session_factory = session_factory_from_settings(settings)
    config = Configurator(settings=settings, session_factory = my_session_factory, root_factory=RootFactory)

#    ---------------Project/Workflow pages------------------------
    config.add_route('create', '/project/create')              # Project creation wizard - templates, pre-fill etc.
    config.add_route('general', '/project/{project_id}/general')              # Project creation wizard - templates, pre-fill etc.
    config.add_route('description', '/project/{project_id}/description')    # descriptions
    config.add_route('information', '/project/{project_id}/information')    # metadata or associated information
    config.add_route('methods', '/project/{project_id}/methods')            # Data collection methods
    config.add_route('datasets', '/project/{project_id}/datasets')          # Datasets or collections of data
    config.add_route('submit', '/project/{project_id}/submit')              # Submit, review and approval

    # Project action pages
    config.add_route('dataset_log', '/project/{project_id}/logs/dataset_{dataset_id}_logs.txt')
    config.add_route('logs', '/project/{project_id}/logs')
    config.add_route('dataset_calibration', '/project/{project_id}/dataset/{dataset_id}/calibration/*calibration_id')
    config.add_route('dataset', '/project/{project_id}/dataset/*dataset_id')          # Datasets or collections of data
    config.add_route('data_calibration', '/project/{project_id}/datasets/{dataset_id}/data/{id_list}/calibration/*calibration_id')
    config.add_route('data', '/project/{project_id}/datasets/{dataset_id}/data/*data_id')
    config.add_route('permissions', '/project/{project_id}/permissions')
    config.add_route('notifications', '/project/{project_id}/notifications')
    config.add_route('duplicate', '/project/{project_id}/duplicate')
    config.add_route('create_template', '/project/{project_id}/create_template')
    config.add_route('search', '/search*search_info')
    config.add_route('dataset_record', '/project/{project_id}/datasets/{dataset_id}/record')          # Datasets or collections of data
    config.add_route('delete_record', '/project/{project_id}/datasets/{dataset_id}/delete_record')          # Datasets or collections of data

#    config.add_route('browse', '/browse')
#    config.add_route('browse_projects', '/browse/projects/*search_info')
#    config.add_route('browse', '/browse/datasets')
#    config.add_route('browse', '/browse/data')
#    config.add_route('browse', '/browse/data/calibrations')

    # Exception handler
    config.add_route('workflow_exception', '/project/{route:.*}')

#    --------------JSON Search views--------------------------------
    config.add_route('get_model', '/get_model/{object_type}/{id}', xhr=True)
    config.add_route('get_ingester_logs', '/get_ingester_logs/{dam_id}/{filtering:.*}', xhr=True)
    config.add_route('add_method_from_template', '/add/{project_id}/{method_id}', xhr=True)

    config.add_route('get_activities', '/mint/activities/{search_terms}', xhr=True)
    config.add_route('get_parties', '/mint/parties/{search_terms}', xhr=True)
    config.add_route('get_from_identifier', '/mint/{identifier:.*}', xhr=True)

    config.add_route('dashboard', '/')                                      # Home page/user dashboard
    config.add_route('login', '/login')                                     # Login page
    config.add_route('login_shibboleth', '/login/shibboleth')                                     # Login page
    config.add_route('logout', '/logout')                                     # logout and redirect page
    config.add_route('admin', '/admin')                                     # administer user permissions + view admin required items
    config.add_route('help', '/help')                                     # administer user permissions + view admin required items
    config.add_route('lock_page', '/lock_page/{route}/{user_id}')
    config.add_route('unlock_page', '/unlock_page/{lock_id}')
    config.add_route('record_data', '/{metadata_id}')

    #    --------------Static resources--------------------------------
    config.add_static_view('deform_static', 'deform:static', cache_max_age=0)
    config.add_static_view('static', 'jcudc24provisioning:static')
    config.add_static_view('project_uploads', "jcudc24provisioning:project_uploads", permission=DefaultPermissions.VIEW_PROJECT)

    authn_policy = ShibbolethAuthenticationPolicy(settings)
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.set_default_permission(NO_PERMISSION_REQUIRED)

    config.add_request_method(get_user, 'user', reify=True)

    config.scan()

    json_config = create_json_config()
    f = open(settings.get("redbox.local_config_file"), 'w')
    f.write(json_config)

    # Upload the json cofiguration to ReDBox
#    hostname = global_settings.get("redbox.ssh_address") # remote hostname where SSH server is running
#    port = asint(global_settings.get("redbox.ssh_port"))
#    rsa_private_key = global_settings.get("redbox.rsa_private_key")
#    username = global_settings.get("redbox.ssh_username")
#    password = global_settings.get("redbox.ssh_password")
#    file_send = SFTPFileSend(hostname, port, username, password=password, rsa_private_key=rsa_private_key)
#    file_send.upload_file(settings.get("redbox.local_config_file"), settings.get("redbox.ssh_config_file"))
#    file_send.close()

#    try:
#        InitialiseDatabase()
#    except Exception as e:
#        logger.exception("Error initialising database: %s", e)
#        sys.exit()

    # Create the temporary folders if they don't already exist
    if not os.path.exists(settings.get("tmpdir")):
        os.mkdir(settings.get("tmpdir"))
    if not os.path.exists(settings.get("pyramid_deform.tempdir")):
        os.mkdir(settings.get("pyramid_deform.tempdir"))
    if not os.path.exists(settings.get("mint.tmpdir")):
        os.mkdir(settings.get("mint.tmpdir"))
    if not os.path.exists(settings.get("redbox.tmpdir")):
        os.mkdir(settings.get("redbox.tmpdir"))
    if not os.path.exists(settings.get("workflows.files")):
            os.mkdir(settings.get("workflows.files"))
#    if not os.path.exists(settings.get("mail.queue_path")):
#        os.mkdir(settings.get("mail.queue_path"))

    return config.make_wsgi_app()



#if __name__ == '__main__':
#    app = main("serve ../development.ini")
#    server = make_server('0.0.0.0', 8080, app)
#    server.serve_forever()
