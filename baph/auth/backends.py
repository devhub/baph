import django.core.validators

from baph.auth.models import User, Organization
from baph.auth.registration import settings as auth_settings
from baph.db.orm import ORM


orm = ORM.get()

class MultiSQLAlchemyBackend(object):
    """Backend which auths via username or email"""
    
    def authenticate(self, identification, password=None, check_password=True):
        session = orm.sessionmaker()
        org_key = Organization.resource_name.lower() + '_id'
        user = None
        try:
            # if it looks like an email, lookup against the email column
            django.core.validators.validate_email(identification)
            filters = {'email': identification}
            if auth_settings.BAPH_AUTH_UNIQUE_WITHIN_ORG:
                filters[org_key] = Organization.get_current_id()
            user = session.query(User).filter_by(**filters).first()
        except django.core.validators.ValidationError:
            # this wasn't an email
            pass
        if not user:
            # email lookup failed, try username lookup if enabled
            if auth_settings.BAPH_AUTH_WITHOUT_USERNAMES:
                # usernames are not valid login credentials
                return None
            filters = {User.USERNAME_FIELD: identification}
            if auth_settings.BAPH_AUTH_UNIQUE_WITHIN_ORG:
                filters[org_key] = Organization.get_current_id()
            user = session.query(User).filter_by(**filters).first()
        if not user:
            return None
        if check_password:
            if user.check_password(password):
                return user
            return None
        else: return user

    def get_user(self, user_id):
        session = orm.sessionmaker()
        return session.query(User).get(user_id)

