"""
Contains services or service factories

Created on Aug 21, 2013

@author: nigel
"""
import jcudc24provisioning
from jcudc24ingesterapi.authentication import CredentialsAuthentication
from jcudc24provisioning.controllers.ingesterapi_wrapper import IngesterAPIWrapper

def get_ingester_platform_api(config=jcudc24provisioning.global_settings):
    """Gets the Ingester Platform API object using the settings in the config object.
    """
    auth = CredentialsAuthentication(config["ingesterapi.username"], config["ingesterapi.password"])
    ingester_api = IngesterAPIWrapper(config["ingesterapi.url"], auth)
    return ingester_api

