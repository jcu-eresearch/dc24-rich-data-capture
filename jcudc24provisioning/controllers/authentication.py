from pyramid.security import ALL_PERMISSIONS, Everyone, Allow

__author__ = 'casey'

def authenticate_user(user_name, password):
    if user_name == password:
        return True

    return False

def get_groups(user_id, request):
    if True:
        return [ALL_PERMISSIONS, "admin"]

    return None

