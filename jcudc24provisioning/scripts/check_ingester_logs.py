"""
Read through the most recent logs of all active ingesters and send email notifications if any errors or warnings
are found.
"""
from jcudc24ingesterapi.authentication import CredentialsAuthentication
import datetime
from jcudc24provisioning.controllers.ingesterapi_wrapper import IngesterAPIWrapper

import os
import os
import sys
from pyramid.request import Request
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
import transaction

import random
from jcudc24provisioning.controllers.authentication import DefaultPermissions, DefaultRoles
from jcudc24provisioning.models import DBSession, Base
from jcudc24provisioning.models.project import Location, ProjectTemplate, Project, Dataset, MethodSchema, MethodSchemaField, Project, MethodTemplate, Method, PullDataSource, DatasetDataSource, NotificationConfig, UserNotificationConfig, ProjectNotificationConfig, Notification
from jcudc24ingesterapi.schemas.data_types import Double
from jcudc24provisioning.models import website

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )
from jcudc24provisioning.models.website import User, Role, Permission

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s production.ini")' % (cmd, cmd))
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    check_logs(config_uri)

def check_logs(config_uri):
    settings = get_appsettings(config_uri)

    # Initialise the database connection.
    engine = engine_from_config(settings, 'sqlalchemy.', pool_recycle=3600)
    DBSession.configure(bind=engine)

    session = DBSession()

    auth = CredentialsAuthentication(settings["ingesterapi.username"], settings["ingesterapi.password"])
    ingester_api = IngesterAPIWrapper(settings["ingesterapi.url"], auth)

    start_time = datetime.datetime.now()

    active_datasets = session.query(Dataset).filter_by(disabled=False).filter(Dataset.dam_id is not None).all()
    for dataset in active_datasets:
        logs = ingester_api.getIngesterLogs(dataset.dam_id)

        error_logs = []
        warning_logs = []
        for log in logs:
            test = start_time - log['timestanp']
            # If this log is from the last 24 hours.
            if  start_time - log['timestanp'] < 86400:
                if log['level'] == 'error':
                    error_logs.append(log)
                elif log['level'] == 'warning':
                    warning_logs.append(log)

        if len(error_logs) > 0:
            send_email_notifications(session, dataset, type=NotificationConfig.log_errors.key, errors=error_logs)

        if len(warning_logs) > 0:
            send_email_notifications(session, dataset, type=NotificationConfig.log_errors.key, warnings=warning_logs)


def send_email_notifications(session, dataset, type, **kw):
    """
    Send email notifications to all users that are configured to receive them for the current project and
    notification type.

    :param type: Name of the configuration type (eg. NotificationsConfig.new_projects.key)
    Lparam project: Optionally pass in the project that this notification is for (this will usually be for creating
                    new projects, as self.project isn't setup correctly yet).
    :return: Nothing.
    """

    BASE_URL = "https://eresearch.jcu.edu.au/enmasse/"
    request = Request.Blank('/', base_url="https://reseawrch.jcu.edu.au/enmasse")

    config_ids = [id_tuple[0] for id_tuple in session.query(NotificationConfig.id).filter(getattr(NotificationConfig, type)==True).all()]
    user_notification_config_ids = [id_tuple[0] for id_tuple in session.query(ProjectNotificationConfig.user_notification_config_id).filter_by(project_id=dataset.project_id).filter(ProjectNotificationConfig.notification_config_id.in_(config_ids)).all()]
    user_ids = [tuple_id[0] for tuple_id in session.query(UserNotificationConfig.user_id).filter(UserNotificationConfig.id.in_(user_notification_config_ids)).all()]
    users = session.query(User).filter(User.id.in_(user_ids)).all()
    email_to = [user.email for user in users]

    variables = {"title": dataset.record_metadata.project_title,
                 "project_id": dataset.project_id, "dataset_id": dataset.id, "url": request.route_url("manage_dataset", project_id=dataset.project_id, dataset_id=dataset.id)}
    variables.update(kw)

    if type == NotificationConfig.log_errors.key:
        email_subject = "[%(dataset_id)s] EnMaSSe Ingester log error(s)" % variables


        email_message = "Hi EnMaSSe User,<br />"\
                        "<p><a href='%(url)s'>dataset_%(dataset_id)s: %(title)s</a> error(s) found in ingester logs:</p>" +\
                        '<br />'.join(["%s - %s - %s - %s - %s - %s.\n" % (
                        log['id'], log['dataset_id'], log['timestamp'], log['class'], log['level'],
                        log['message'].strip()) for log in kw['errors']]) +\
                        "<br />Regards,"\
                        "<br/>EnMaSSe System" % variables

        # Add a record of the notification to the database
        notification = Notification(type, ','.join(email_to), email_subject, email_message,
            ','.join(["%s - %s - %s - %s - %s - %s.\n" % (
            log['id'], log['dataset_id'], log['timestamp'], log['class'], log['level'],
            log['message'].strip()) for log in kw['errors']]
            ), ','.join("%s=%s" % (key, value) for key, value in variables.items()))
        session.add(notification)

    elif type == NotificationConfig.log_warnings.key:
        email_subject = "[%(dataset_id)s] EnMaSSe Ingester log warning(s)" % variables
        email_message = "Hi EnMaSSe User,<br />"\
                        "<p><a href='%(url)s'>dataset_%(dataset_id)s: %(title)s</a> warning(s) found in ingester logs:</p>" +\
                        '<br />'.join(["%s - %s - %s - %s - %s - %s.\n" % (
                            log['id'], log['dataset_id'], log['timestamp'], log['class'], log['level'],
                            log['message'].strip()) for log in kw['warnings']]) +\
                        "<br />Regards,"\
                        "<br/>EnMaSSe System" % variables

        # Add a record of the notification to the database
        notification = Notification(type, ','.join(email_to), email_subject, email_message,
            ','.join(["%s - %s - %s - %s - %s - %s.\n" % (
                log['id'], log['dataset_id'], log['timestamp'], log['class'], log['level'],
                log['message'].strip()) for log in kw['warnings']]
            ), ','.join("%s=%s" % (key, value) for key, value in variables.items()))
        session.add(notification)

    if len(email_to) > 0:
        mailer = get_mailer(request)
        message = Message(subject=email_subject, recipients=email_to, html=email_message)
        mailer.send(message)

