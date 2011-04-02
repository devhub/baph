# -*- coding: utf-8 -*-
'''\
==========================================================================
:mod:`baph.auth.middleware` -- Django+SQLAlchemy Authentication Middleware
==========================================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
'''


class LazyUser(object):
    '''Allows for the lazy retrieval of the :class:`baph.auth.models.User`
    object.
    '''
    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_cached_user'):
            from . import get_user
            request._cached_user = get_user(request)
        return request._cached_user


class AuthenticationMiddleware(object):
    '''See :class:`django.contrib.auth.middleware.AuthenticationMiddleware`.
    '''

    def process_request(self, request):
        assert hasattr(request, 'session'), '''\
The Django authentication middleware requires session middleware to be
installed. Edit your MIDDLEWARE_CLASSES setting to insert
"django.contrib.sessions.middleware.SessionMiddleware".'''
        request.__class__.user = LazyUser()
        return None
