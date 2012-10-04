__author__ = 'Casey Bajema'

"""
    Base class for access authentication
"""
class _Authentication():
    pass

"""
    Authentication using a private, unique, randomly generated string as a key.
"""
class KeyAuthentication(_Authentication):
    def __init__(self, key):
        self.key = key

"""
    Authentication using a username and password.
"""
class CredentialsAuthentication(_Authentication):
    def __init__(self, username, password):
        self.username = username
        self.password = password

