# -*- coding: utf-8 -*-
from datetime import datetime
import hashlib
from oauth import oauth
import random
import urllib
import uuid

from django.conf import settings
from django.contrib.auth.hashers import (
    check_password, make_password, is_password_usable)
from django.contrib.auth.signals import user_logged_in
from django.core.exceptions import ImproperlyConfigured
from django.dispatch import receiver
from django.test.signals import setting_changed
from django.utils.datastructures import SortedDict
from django.utils.encoding import smart_str
from django.utils.importlib import import_module
from django.utils.translation import ugettext as _
from sqlalchemy import *
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import (relationship, backref, object_session,
    RelationshipProperty, clear_mappers)

from baph.auth.mixins import UserPermissionMixin
from baph.auth.registration import settings as auth_settings
from baph.db import ORM
from baph.db.models.loading import cache
from baph.db.types import UUID, Dict, List
from baph.utils.strings import random_string
from baph.utils.importing import remove_class
import inspect, sys


orm = ORM.get()
Base = orm.Base


AUTH_USER_FIELD_TYPE = getattr(settings, 'AUTH_USER_FIELD_TYPE', 'UUID')
AUTH_USER_FIELD = UUID if AUTH_USER_FIELD_TYPE == 'UUID' else Integer
PERMISSION_TABLE = getattr(settings, 'BAPH_PERMISSION_TABLE',
                            'baph_auth_permissions')
UNUSABLE_PASSWORD = '!'

def _generate_user_id_column():
    if AUTH_USER_FIELD_TYPE != 'UUID':
        return Column(AUTH_USER_FIELD, primary_key=True)
    return Column(UUID, primary_key=True, default=uuid.uuid4)

def update_last_login(sender, user, **kwargs):
    """
    A signal receiver which updates the last_login date for
    the user logging in.
    """
    user.last_login = datetime.now()
    user.save(update_fields=['last_login'])
user_logged_in.connect(update_last_login)

def get_or_fail(codename):
    session = orm.sessionmaker()
    try:
        perm = session.query(Permission).filter_by(codename=codename).one()
    except:
        raise ValueError('%s is not a valid permission codename' % codename)
    return PermissionAssociation(permission=perm)

def string_to_model(string):
    if string in orm.Base._decl_class_registry:
        return orm.Base._decl_class_registry[string]
    elif string.title() in Base._decl_class_registry:
        return orm.Base._decl_class_registry[string.title()]
    else:
        # this string doesn't match a resource
        return None


# permission classes

class Permission(Base):
    __tablename__ = PERMISSION_TABLE
    __table_args__ = {
        'info': {'preserve_during_flush': True},
        }
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(100))
    codename = Column(String(100), unique=True)
    resource = Column(String(50))
    action = Column(String(16))
    key = Column(String(100))
    value = Column(String(50))


# organization models

class AbstractBaseOrganization(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)

    @classmethod
    def get_current(cls):
        raise NotImplemented('get_current must be defined on the '
            'custom Organization model')

    @classmethod
    def get_current_id(cls, request=None):
        org = cls.get_current()
        if not org:
            return None
        if isinstance(org, dict):
            return org['id']
        else:
            return org.id

    @classmethod
    def get_column_key(cls):
        return cls._meta.model_name+'_id'

    @classmethod
    def get_relation_key(cls):
        return cls._meta.model_name

class BaseOrganization(AbstractBaseOrganization):
    __tablename__ = 'baph_auth_organizations'
    __requires_subclass__ = True
    name = Column(Unicode(200), nullable=False)

class Organization(BaseOrganization):
    class Meta:
        swappable = 'BAPH_ORGANIZATION_MODEL'


# group models

class AbstractBaseGroup(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)

    users = association_proxy('user_groups', 'user',
        creator=lambda v: UserGroup(user=v))
    permissions = association_proxy('permission_assocs', 'permission')
    codenames = association_proxy('permission_assocs', 'codename',
        creator=get_or_fail)

class BaseGroup(AbstractBaseGroup):
    __tablename__ = 'baph_auth_groups'
    __requires_subclass__ = True
    name = Column(Unicode(100))

class Group(BaseGroup):
    class Meta:
        swappable = 'BAPH_GROUP_MODEL'

col_key = Organization._meta.model_name+'_id'
col = getattr(BaseGroup.__table__.c, col_key, None)
if col is None:
    setattr(BaseGroup, col_key,
        Column(Integer, ForeignKey(Organization.id), index=True))

rel_key = Organization._meta.model_name
rel = getattr(Group, rel_key, None)
if rel is None:
    rel = RelationshipProperty(Organization, 
        backref=Group._meta.model_name_plural,
        foreign_keys=[getattr(BaseGroup, col_key)])
    setattr(Group, rel_key, rel)
    

# user models

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

class AbstractBaseUser(Base, UserPermissionMixin):
    __abstract__ = True
    id = _generate_user_id_column()
    email = Column(String(settings.EMAIL_FIELD_LENGTH), index=True,
                    nullable=False)
    password = Column(String(256), nullable=False)
    last_login = Column(DateTime, default=datetime.now, nullable=False)
    is_staff = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    date_joined = Column(DateTime, default=datetime.now, nullable=False)

    permissions = association_proxy('permission_assocs', 'permission')
    codenames = association_proxy('permission_assocs', 'codename',
                                  creator=get_or_fail)

    # this is to allow the django password reset token generator to work
    @property
    def pk(self):
        return self.id

    def get_username(self):
        "Return the identifying username for this User"
        return getattr(self, self.USERNAME_FIELD)

    def is_anonymous(self):
        '''Always returns :const:`False`. This is a way of comparing
        :class:`User` objects to anonymous users.
        '''
        return False

    def is_authenticated(self):
        '''Tells if a user's authenticated. Always :const:`True` for this
        class.
        '''
        return True

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """
        def setter(raw_password):
            self.set_password(raw_password)
            self.save(update_fields=["password"])
        return check_password(raw_password, self.password, setter)

    def has_usable_password(self):
        '''Determines whether the user has a password.'''
        return self.password != UNUSABLE_PASSWORD

    def set_unusable_password(self):
        '''Sets a password value that will never be a valid hash.'''
        self.password = UNUSABLE_PASSWORD

    # from UserManager

    @classmethod
    def normalize_email(cls, email):
        """
        Normalize the address by lowercasing the domain part of the email
        address.
        """
        email = email or ''
        try:
            email_name, domain_part = email.strip().rsplit('@', 1)
        except ValueError:
            pass
        else:
            email = '@'.join([email_name, domain_part.lower()])
        return email

    @classmethod
    def _create_user(cls, username, email, password, is_staff, is_superuser,
                     **extra_fields):
        now = datetime.now()
        if not getattr(settings, 'BAPH_AUTH_WITHOUT_USERNAMES', False) and not username:
            raise ValueError('The given username must be set')
        org_key = Organization._meta.model_name
        if not any(f in extra_fields for f in (org_key, org_key+'_id')):
            extra_fields[org_key+'_id'] = Organization.get_current_id()

        email = cls.normalize_email(email)
        user = cls(username=username, email=email, is_staff=is_staff,
                   is_active=True, is_superuser=is_superuser, 
                   last_login=now, date_joined=now, **extra_fields)
        user.set_password(password)
        session = orm.sessionmaker()
        session.add(user)
        session.commit()
        return user

    @classmethod
    def create_user(cls, username, email=None, password=None, **extra_fields):
        return cls._create_user(username, email, password, False, False,
                                 **extra_fields)

    @classmethod
    def create_superuser(cls, username, email, password, **extra_fields):
        return cls._create_user(username, email, password, True, True,
                                 **extra_fields)


class BaseUser(AbstractBaseUser):
    __tablename__ = 'auth_user'
    __requires_subclass__ = True
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    username = Column(Unicode(75), 
        nullable=auth_settings.BAPH_AUTH_WITHOUT_USERNAMES, index=True)
    first_name = Column(Unicode(30))
    last_name = Column(Unicode(30))

    def email_user(self, subject, message, from_email=None, **kwargs):
        '''Sends an e-mail to this User.'''
        from django.core.mail import send_mail
        if not from_email:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def get_absolute_url(self):
        '''The absolute path to a user's profile.

        :rtype: :class:`str`
        '''
        return '/users/%s/' % urllib.quote(smart_str(self.username))

    def get_full_name(self):
        '''Retrieves the first_name plus the last_name, with a space in
        between and no leading/trailing whitespace.
        '''
        full_name = u'%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def save(self, update_fields=[], **kwargs):
        session = object_session(self)
        if not session:
            session = orm.sessionmaker()
            session.add(self)
        session.commit()

class User(BaseUser):
    class Meta:
        swappable = 'BAPH_USER_MODEL'

col_key = Organization._meta.model_name+'_id'
#col = getattr(BaseUser.__table__.c, col_key, None)
#if col is None:
setattr(BaseUser, col_key,
    Column(Integer, ForeignKey(Organization.id), index=True))

rel_key = Organization._meta.model_name
#rel = getattr(User, rel_key, None)
#if rel is None:
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


# association classes

class UserGroup(Base):
    '''User groups'''
    __tablename__ = 'baph_auth_user_groups'
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'group_id', 'key', 'value'),
        Index('idx_group_context', 'group_id', 'key', 'value'),
        Index('idx_context', 'key', 'value'),
        )

    class Meta:
        permission_parents = ['user']
        permission_handler = 'user'

    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    group_id = Column(Integer, ForeignKey(Group.id), nullable=False)
    key = Column(String(32), default='')
    value = Column(String(32), default='')

    user = relationship(User, backref=backref('groups',
        cascade='all, delete-orphan'))
    group = relationship(Group, backref=backref('user_groups',
        cascade='all, delete-orphan'))

class PermissionAssociation(Base):
    __tablename__ = PERMISSION_TABLE + '_assoc'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    group_id = Column(Integer, ForeignKey(Group.id))
    perm_id = Column(Integer, ForeignKey(Permission.id), nullable=False)

    user = relationship(User, backref=backref('permission_assocs',
        cascade='all, delete-orphan'))
    group = relationship(Group, backref=backref('permission_assocs',
        cascade='all, delete-orphan'))
    permission = relationship(Permission, lazy='joined')

    codename = association_proxy('permission', 'codename')


# OAuth models

MAX_KEY_LEN = 255
MAX_SECRET_LEN = 255
KEY_LEN = 32
SECRET_LEN = 32

class OAuthConsumer(Base):
    __tablename__ = 'auth_oauth_consumer'
    id = Column(Integer, ForeignKey(User.id), primary_key=True)
    key = Column(String(MAX_KEY_LEN), unique=True)
    secret = Column(String(MAX_SECRET_LEN))

    user = relationship(User, lazy=True, uselist=False)

    def __init__(self, **kwargs):
        super(OAuthConsumer, self).__init__(**kwargs)
        if not self.key:
            self.key = random_string(length=KEY_LEN)
        if not self.secret:
            self.secret = random_string(length=SECRET_LEN)

    @classmethod
    def create(cls, user_id, **kwargs):
        kwargs['id'] = user_id
        return cls(**kwargs)

    def as_consumer(self):
        '''Creates an oauth.OAuthConsumer object from the DB data.
        :rtype: oauth.OAuthConsumer
        '''
        return oauth.OAuthConsumer(self.key, self.secret)

class OAuthNonce(Base):
    __tablename__ = 'auth_oauth_nonce'
    id = Column(Integer, primary_key=True)
    token_key = Column(String(32))
    consumer_key = Column(String(MAX_KEY_LEN), ForeignKey(OAuthConsumer.key))
    key = Column(String(255), nullable=False, unique=True)

