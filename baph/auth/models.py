# -*- coding: utf-8 -*-
'''\
======================================================================
:mod:`baph.auth.models` -- SQLAlchemy models for Django Authentication
======================================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>

SQLAlchemy versions of models from :mod:`django.contrib.auth.models`.

.. setting:: AUTH_DIGEST_ALGORITHM

Setting: AUTH_DIGEST_ALGORITHM
------------------------------

The default hash algorithm used to set passwords with. Defaults to ``sha1``.
'''

import inspect

from baph.db.models import Model
from baph.db.orm import ORM
from baph.db.types import UUID
from baph.utils.importing import import_attr
from datetime import datetime
from django.conf import settings
(AnonymousUser, check_password, base_get_hexdigest, SiteProfileNotAvailable,
 UNUSABLE_PASSWORD) = \
    import_attr(['django.contrib.auth.models'],
                ['AnonymousUser', 'check_password', 'get_hexdigest',
                 'SiteProfileNotAvailable', 'UNUSABLE_PASSWORD'])
from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import smart_str
from django.utils.importlib import import_module
from django.utils.translation import ugettext as _
import hashlib
import random
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Unicode
from sqlalchemy.orm import synonym
import urllib
import uuid

orm = ORM.get()

AUTH_USER_FIELD_TYPE = getattr(settings, 'AUTH_USER_FIELD_TYPE', 'UUID')
AUTH_USER_FIELD = UUID if AUTH_USER_FIELD_TYPE == 'UUID' else Integer(10)


def get_hexdigest(algorithm, salt, raw_password):
    '''Extends Django's :func:`django.contrib.auth.models.get_hexdigest` by
    adding support for all of the other available hash algorithms.

    Inspired by http://u.malept.com/djpwdhash
    '''
    if (hasattr(hashlib, 'algorithms') and algorithm in hashlib.algorithms):
        return hashlib.new(algorithm, salt + raw_password).hexdigest()
    elif algorithm in ('sha224', 'sha256', 'sha384', 'sha512'):
        return getattr(hashlib, algorithm)(salt + raw_password).hexdigest()
    else:
        return base_get_hexdigest(algorithm, salt, raw_password)

# fun with monkeypatching
exec inspect.getsource(check_password)

def _generate_user_id_column():
    if AUTH_USER_FIELD_TYPE != 'UUID':
        return Column(AUTH_USER_FIELD, primary_key=True)
    return Column(UUID, primary_key=True, default=uuid.uuid4)

class User(orm.Base, Model):
    '''The SQLAlchemy model for Django's ``auth_user`` table.
    Users within the Django authentication system are represented by this
    model.

    Username and password are required. Other fields are optional.
    '''
    __tablename__ = 'auth_user'

    id = _generate_user_id_column()
    '''Unique ID of the :class:`User`.'''
    username = Column(Unicode(75), nullable=False, unique=True)
    '''See :attr:`django.contrib.auth.models.User.username`.'''
    first_name = Column(Unicode(30), nullable=True)
    '''See :attr:`django.contrib.auth.models.User.first_name`.'''
    last_name = Column(Unicode(30), nullable=True)
    '''See :attr:`django.contrib.auth.models.User.last_name`.'''
    _email = Column('email', String(settings.EMAIL_FIELD_LENGTH), index=True,
                    nullable=False)
    '''See :attr:`django.contrib.auth.models.User.email`.'''
    password = Column(String(256), nullable=False)
    '''See :attr:`django.contrib.auth.models.User.password`.'''
    is_staff = Column(Boolean, default=False, nullable=False)
    '''See :attr:`django.contrib.auth.models.User.is_staff`.'''
    is_active = Column(Boolean, default=True, nullable=False)
    '''See :attr:`django.contrib.auth.models.User.is_active`.'''
    is_superuser = Column(Boolean, default=False, nullable=False)
    '''See :attr:`django.contrib.auth.models.User.is_superuser`.'''
    last_login = Column(DateTime, default=datetime.now, nullable=False,
                        onupdate=datetime.now)
    '''See :attr:`django.contrib.auth.models.User.last_login`.'''
    date_joined = Column(DateTime, default=datetime.now, nullable=False)
    '''See :attr:`django.contrib.auth.models.User.date_joined`.'''

    def _get_email(self):
        '''See :attr:`django.contrib.auth.models.User.email`.'''
        return self._email

    def _set_email(self, value):
        # Normalize the address by lowercasing the domain part of the email
        # address.
        try:
            email_name, domain_part = value.strip().split('@', 1)
        except ValueError:
            raise ValueError(_('The email address supplied is invalid.'))
        else:
            self._email = '@'.join([email_name, domain_part.lower()])

    email = synonym('_email', descriptor=property(_get_email, _set_email))

    def get_absolute_url(self):
        '''The absolute path to a user's profile.

        :rtype: :class:`str`
        '''
        return '/users/%s/' % urllib.quote(smart_str(self.username))

    def check_password(self, raw_password):
        '''Tests if the password given matches the password of the user.'''
        if self.password == UNUSABLE_PASSWORD:
            return False
        return check_password(raw_password, self.password)

    def email_user(self, subject, message, from_email=None, **kwargs):
        '''Sends an e-mail to this User.'''
        from django.core.mail import send_mail
        if not from_email:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        send_mail(subject, message, from_email, [self.email], **kwargs)

    @staticmethod
    def generate_salt(algo='sha1'):
        '''Generates a salt for generating digests.'''
        return get_hexdigest(algo, str(random.random()),
                             str(random.random()))[:5]

    def get_full_name(self):
        '''Retrieves the first_name plus the last_name, with a space in
        between and no leading/trailing whitespace.
        '''
        full_name = u'%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_profile(self, session=None):
        '''Returns site-specific profile for this user. Raises
        :exc:`~django.contrib.auth.models.SiteProfileNotAvailable` if this
        site does not allow profiles.
        '''
        if not hasattr(self, '_profile_cache'):
            from django.conf import settings
            if not getattr(settings, 'AUTH_PROFILE_MODULE', False):
                raise SiteProfileNotAvailable('''\
You need to set AUTH_PROFILE_MODULE in your project settings''')
            try:
                app_label, model_name = settings.AUTH_PROFILE_MODULE \
                                                .rsplit('.', 1)
            except ValueError:
                raise SiteProfileNotAvailable('''\
app_label and model_name should be separated by a dot in the
AUTH_PROFILE_MODULE setting''')

            try:
                module = import_module(app_label)
                model_cls = getattr(module, model_name, None)
                if model_cls is None:
                    raise SiteProfileNotAvailable('''\
Unable to load the profile model, check AUTH_PROFILE_MODULE in your project
settings''')
                if not session:
                    session = orm.sessionmaker()
                self._profile_cache = session.query(model_cls) \
                                             .get(self.id)
            except (ImportError, ImproperlyConfigured):
                raise SiteProfileNotAvailable
        return self._profile_cache

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

    def set_unusable_password(self):
        '''Sets a password value that will never be a valid hash.'''
        self.password = UNUSABLE_PASSWORD

    def __repr__(self):
        return '<User(%s, "%s")>' % (self.id, self.get_full_name())

    def __unicode__(self):
        return unicode(self.username)

    @classmethod
    def create_user(cls, username, email, password=None, session=None):
        '''Creates a new User.'''
        if not session:
            session = orm.sessionmaker()
        user = cls(username=username, email=email, is_staff=False,
                   is_active=True, is_superuser=False)
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
