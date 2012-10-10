__author__ = 'Casey Bajema'


class _Authentication():
    """
    Base class for access authentication
    """
    pass


class KeyAuthentication(_Authentication):
    """
    Authentication using a private, unique, randomly generated string as a key.
    """
    def __init__(self, key):
        self.key = key

class CredentialsAuthentication(_Authentication):
    """
    Authentication using a username and password.
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password

