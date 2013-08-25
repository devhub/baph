# -*- coding: utf-8 -*-
from datetime import datetime
import hashlib
from oauth import oauth
import random
import urllib
import uuid

from django.conf import settings
from django.contrib.auth.hashers import (
    check_password, make_password, is_password_usable, UNUSABLE_PASSWORD)
from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import smart_str
from django.utils.importlib import import_module
from django.utils.translation import ugettext as _
from sqlalchemy import *
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import synonym, relationship, backref, object_session

from baph.auth.mixins import UserPermissionMixin
from baph.db import ORM
from baph.db.types import UUID, Dict, List
from baph.utils.strings import random_string
import inspect


orm = ORM.get()
Base = orm.Base


AUTH_USER_FIELD_TYPE = getattr(settings, 'AUTH_USER_FIELD_TYPE', 'UUID')
AUTH_USER_FIELD = UUID if AUTH_USER_FIELD_TYPE == 'UUID' else Integer

"""
def get_hexdigest(algorithm, salt, raw_password):
    '''Extends Django's :func:`django.contrib.auth.models.get_hexdigest` by
    adding support for all of the other available hash algorithms.

    Inspired by http://u.malept.com/djpwdhash
    '''
    if (hasattr(hashlib, 'algorithms') and algorithm in hashlib.algorithms):
        return hashlib.new(algorithm, salt + raw_password).hexdigest()
    elif algorithm in ('sha1', 'sha224', 'sha256', 'sha384', 'sha512', 'md5'):
        return getattr(hashlib, algorithm)(salt + raw_password).hexdigest()
    else:
        raise Exception('Unsupported algorithm "%s"' % algorithm)

# fun with monkeypatching
exec inspect.getsource(check_password)
"""
def _generate_user_id_column():
    if AUTH_USER_FIELD_TYPE != 'UUID':
        return Column(AUTH_USER_FIELD, primary_key=True)
    return Column(UUID, primary_key=True, default=uuid.uuid4)

def update_last_login(sender, user, **kwargs):
    """
    A signal receiver which updates the last_login date for
    the user logging in.
    """
    user.last_login = get_datetime_now()
    user.save(update_fields=['last_login'])
    # user_logged_in.connect(update_last_login) #TODO: connect this signal

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

class BaseUser(Base, UserPermissionMixin):
    '''The SQLAlchemy model for Django's ``auth_user`` table.
    Users within the Django authentication system are represented by this
    model.

    Username and password are required. Other fields are optional.
    '''
    __tablename__ = 'auth_user'

    id = _generate_user_id_column()
    username = Column(Unicode(75), nullable=False, unique=True)
    first_name = Column(Unicode(30), nullable=True)
    last_name = Column(Unicode(30), nullable=True)
    email = Column(String(settings.EMAIL_FIELD_LENGTH), index=True,
                    nullable=False)
    password = Column(String(256), nullable=False)
    is_staff = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime, default=datetime.now, nullable=False,
                        onupdate=datetime.now)
    date_joined = Column(DateTime, default=datetime.now, nullable=False)

    permissions = association_proxy('permission_assocs', 'permission')
    codenames = association_proxy('permission_assocs', 'codename')

    def get_absolute_url(self):
        '''The absolute path to a user's profile.

        :rtype: :class:`str`
        '''
        return '/users/%s/' % urllib.quote(smart_str(self.username))
    """
    def check_password(self, raw_password):
        '''Tests if the password given matches the password of the user.'''
        if self.password == UNUSABLE_PASSWORD:
            return False
        return check_password(raw_password, self.password)
    """
    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """
        def setter(raw_password):
            self.set_password(raw_password)
            self.save(update_fields=["password"])
        return check_password(raw_password, self.password, setter)
    
    def email_user(self, subject, message, from_email=None, **kwargs):
        '''Sends an e-mail to this User.'''
        from django.core.mail import send_mail
        if not from_email:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        send_mail(subject, message, from_email, [self.email], **kwargs)

    """
    @staticmethod
    def generate_salt(algo='sha1'):
        '''Generates a salt for generating digests.'''
        return get_hexdigest(algo, str(random.random()),
                             str(random.random()))[:5]
    """
    def get_full_name(self):
        '''Retrieves the first_name plus the last_name, with a space in
        between and no leading/trailing whitespace.
        '''
        full_name = u'%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def has_usable_password(self):
        '''Determines whether the user has a password.'''
        return self.password != UNUSABLE_PASSWORD

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
    """
    def set_password(self, raw_password, algo=None):
        '''Copy of :meth:`django.contrib.auth.models.User.set_password`.

        The important difference: it takes an optional ``algo`` parameter,
        which can change the hash method used to one-way encrypt the password.
        The fallback used is the :setting:`AUTH_DIGEST_ALGORITHM` setting,
        followed by the default in Django, ``sha1``.
        '''
        if not algo:
            algo = getattr(settings, 'AUTH_DIGEST_ALGORITHM', 'sha1')
        salt = self.generate_salt(algo)
        hsh = get_hexdigest(algo, salt, raw_password)
        self.password = '%s$%s$%s' % (algo, salt, hsh)
    """
    def set_unusable_password(self):
        '''Sets a password value that will never be a valid hash.'''
        self.password = UNUSABLE_PASSWORD

    def __repr__(self):
        return '<User(%s, "%s")>' % (self.id, self.get_full_name())

    def __unicode__(self):
        return unicode(self.username)

    @classmethod
    def create_user(cls, username, email, password=None, session=None,
                    first_name=None, last_name=None):
        '''Creates a new User.'''
        if not session:
            session = orm.sessionmaker()
        user = cls(username=username, email=email, first_name=first_name,
                   last_name=last_name, is_staff=False, is_active=True,
                   is_superuser=False)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        session.add(user)
        session.commit()
        return user

    @classmethod
    def create_staff(cls, username, email, password, session=None):
        '''Creates a new User with staff privileges.'''
        if not session:
            session = orm.sessionmaker()
        user = cls(username=username, email=email, is_staff=True,
                   is_active=True, is_superuser=False)
        user.set_password(password)
        session.add(user)
        session.commit()
        return user

    @classmethod
    def create_superuser(cls, username, email, password, session=None):
        '''Creates a new User with superuser privileges.'''
        if not session:
            session = orm.sessionmaker()
        user = cls(username=username, email=email, is_staff=True,
                   is_active=True, is_superuser=True)
        user.set_password(password)
        session.add(user)
        session.commit()
        return user

    def save(self, update_fields=[], **kwargs):
        session = object_session(self)
        if not session:
            session = orm.sessionmaker()
            session.add(self)
        session.commit()

user_cls = getattr(settings, 'BAPH_USER_CLASS', None)
if user_cls:
    try:
        app_label, model_name = user_cls.rsplit('.', 1)
    except ValueError:
        raise exceptions.ImproperlyConfigured('''\
    app_label and model_name should be separated by a dot in the
    BAPH_USER_CLASS setting''')

    try:
        module = import_module(app_label)
        model_cls = getattr(module, model_name, None)
        if model_cls is None:
            raise exceptions.ImproperlyConfigured('''\
    Unable to load the user profile model, check BAPH_USER_CLASS in your project
    settings''')
    except (ImportError, ImproperlyConfigured):
        raise

    User = model_cls
else:
    User = BaseUser
    

def get_or_fail(codename):
    session = orm.sessionmaker()
    try:
        perm = session.query(Permission).filter_by(codename=codename).one()
    except:
        raise ValueError('%s is not a valid permission codename' % codename)
    return PermissionAssociation(permission=perm)


class Group(Base):
    '''Groups'''
    __tablename__ = 'baph_auth_groups'

    id = Column(Integer, primary_key=True)
    whitelabel = Column(Unicode(100), info={'readonly': True})
    name = Column(Unicode(100))

    users = association_proxy('user_groups', 'user',
        creator=lambda v: UserGroup(user=v))

    permissions = association_proxy('permission_assocs', 'permission')
    codenames = association_proxy('permission_assocs', 'codename',
        creator=get_or_fail)
    

class UserGroup(Base):
    '''User groups'''
    __tablename__ = 'baph_auth_user_groups'
    __table_args__ = (
        Index('idx_group_context', 'group_id', 'key', 'value'),
        Index('idx_context', 'key', 'value'),
        )

    user_id = Column(Integer, ForeignKey(User.id), primary_key=True,
        autoincrement=False)
    group_id = Column(Integer, ForeignKey(Group.id), primary_key=True,
        autoincrement=False)
    key = Column(String(32), primary_key=True, default='')
    value = Column(String(32), primary_key=True, default='')

    user = relationship(User, lazy=True, uselist=False,
        backref=backref('groups', lazy=True, uselist=True,
            cascade='all, delete, delete-orphan'))
    
    group = relationship(Group, lazy=True, uselist=False,
        backref=backref('user_groups', lazy=True, uselist=True))

class Permission(Base):
    __tablename__ = 'baph_auth_permissions'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(100))
    codename = Column(String(100), unique=True)
    resource = Column(String(50))
    action = Column(String(16))
    key = Column(String(100))
    value = Column(String(50))

class PermissionAssociation(Base):
    __tablename__ = 'baph_auth_permission_assoc'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    group_id = Column(Integer, ForeignKey(Group.id))
    perm_id = Column(Integer, ForeignKey(Permission.id))

    user = relationship(User, backref='permission_assocs')
    group = relationship(Group, backref='permission_assocs')
    permission = relationship(Permission, lazy='joined')

    codename = association_proxy('permission', 'codename')


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

