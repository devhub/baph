from datetime import datetime

from django.contrib.auth.signals import user_logged_in
from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import RelationshipProperty

from baph.auth.models.organization import Organization
from baph.auth.registration import settings as auth_settings
from .base import BaseUser


class AnonymousUser(object):
    id = None
    email = None
    username = ''
    is_staff = False
    is_active = False
    is_superuser = False

    def is_anonymous(self):
        return True

    def is_authenticated(self):
        return False

    def has_resource_perm(self, resource):
        return False


class User(BaseUser):
    class Meta:
        swappable = 'BAPH_USER_MODEL'


col_key = Organization._meta.model_name + '_id'
setattr(BaseUser, col_key,
        Column(Integer, ForeignKey(Organization.id), index=True))

rel_key = Organization._meta.model_name
rel = RelationshipProperty(Organization,
                           backref=User._meta.model_name_plural,
                           foreign_keys=[getattr(BaseUser, col_key)])
setattr(User, rel_key, rel)

if auth_settings.BAPH_AUTH_UNIQUE_WITHIN_ORG:
    args = [col_key]
else:
    args = []

con = UniqueConstraint(*(args+['email']))
BaseUser.__table__.append_constraint(con)

if not auth_settings.BAPH_AUTH_WITHOUT_USERNAMES:
    con = UniqueConstraint(*(args+[User.USERNAME_FIELD]))
    BaseUser.__table__.append_constraint(con)


def update_last_login(sender, user, **kwargs):
    """
    A signal receiver which updates the last_login date for
    the user logging in.
    """
    user.last_login = datetime.now()
    user.save(update_fields=['last_login'])


user_logged_in.connect(update_last_login)
