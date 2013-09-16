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

class MultiSQLAlchemyBackend(SQLAlchemyBackend):
    """Backend which auths via username or email"""
    
    def authenticate(self, identification, password=None, check_password=True):
        session = orm.sessionmaker()
        org_key = Organization.resource_name + '_id'
        try:
            django.core.validators.validate_email(identification)
            if auth_settings.BAPH_AUTH_UNIQUE_EMAIL:
                filters = {'email': identification}
            elif auth_settings.BAPH_AUTH_UNIQUE_ORG_EMAIL:
                filters = {
                    'email': identification,
                    org_key: Organization.get_current_id(),
                    }
            user = session.query(User).filter_by(**filters).first()
            if not user: return None
        except django.core.validators.ValidationError:
            if auth_settings.BAPH_AUTH_UNIQUE_USERNAME:
                filters = {User.USERNAME_FIELD: identification}
            elif auth_settings.BAPH_AUTH_UNIQUE_ORG_USERNAME:
                filters = {
                    User.USERNAME_FIELD: identification,
                    org_key: Organization.get_current_id(),
                    }
            user = session.query(User).filter_by(**filters).first()
            if not user: return None
        if check_password:
            if user.check_password(password):
                return user
            return None
        else: return user    
