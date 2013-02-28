from pyramid.security import Allow, Everyone

__author__ = 'Casey Bajema'


class RootFactory(object):
    __acl__ = [ (Allow, Everyone, 'admin')]

    def __init__(self, request):
        pass
