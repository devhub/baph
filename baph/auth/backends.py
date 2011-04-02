# -*- coding: utf-8 -*-
'''\
=========================================================================
:mod:`baph.auth.backends` -- SQLAlchemy backend for Django Authentication
=========================================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
'''

from .models import orm, User


class SQLAlchemyBackend(object):
    '''Authentication backend using SQLAlchemy. See
    :setting:`AUTHENTICATION_BACKENDS` for details on
    setting this class as the authentication backend for your project.
    '''

    supports_object_permissions = False
    supports_anonymous_user = True

    def authenticate(self, username=None, password=None, session=None):
        # TODO: Model, login attribute name and password attribute name
        # should be configurable.
        if not session:
            session = orm.sessionmaker()
        user = session.query(User) \
                      .filter_by(username=username) \
                      .first()
        if user is None:
            return user
        elif user.check_password(password):
            return user
        else:
            return None

    def get_user(self, user_id, session=None):
        if not session:
            session = orm.sessionmaker()
        return session.query(User).get(user_id)
