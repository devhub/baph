from __future__ import absolute_import
from datetime import datetime

from django.conf import settings
from django.contrib.auth import (SESSION_KEY, BACKEND_SESSION_KEY,
                                 load_backend, user_logged_in)

from baph.utils.module_loading import import_string


default_app_config = 'baph.auth.apps.AuthConfig'


def login(request, user):
    '''Persist a user id and a backend in the request. This way a user doesn't
    have to reauthenticate on every request.

    :param user: The user object.
    :type user: :class:`baph.auth.models.User`
    '''
    if hasattr(request, 'orm'):
        session = request.orm.sessionmaker()
    else:
        from baph.db import ORM
        session = ORM.get().sessionmaker()
    if user is None:
        user = request.user
    # TODO: It would be nice to support different login methods, like signed
    # cookies.
    user.last_login = datetime.now()
    session.commit()

    if SESSION_KEY in request.session:
        if request.session[SESSION_KEY] != user.id:
            # To avoid reusing another user's session, create a new, empty
            # session if the existing session corresponds to a different
            # authenticated user.
            request.session.flush()
    else:
        request.session.cycle_key()
    request.session[SESSION_KEY] = user.id
    request.session[BACKEND_SESSION_KEY] = user.backend
    if hasattr(request, 'user'):
        request.user = user
    user_logged_in.send(sender=user.__class__, request=request, user=user)    


def logout(request):
    '''Removes the authenticated user's ID from the request and flushes their
    session data.
    '''
    request.session.flush()
    if hasattr(request, 'user'):
        from .models import AnonymousUser
        request.user = AnonymousUser()


def get_user(request):
    '''Retrieves the object representing the current user.'''
    from .models import AnonymousUser
    try:
        user_id = request.session[SESSION_KEY]
        backend_path = request.session[BACKEND_SESSION_KEY]
        assert backend_path in settings.AUTHENTICATION_BACKENDS
        backend = load_backend(backend_path)
        user = backend.get_user(user_id) or AnonymousUser()
    except KeyError:
        user = AnonymousUser()
    return user
