from datetime import datetime
import urllib

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.utils.encoding import smart_str
from sqlalchemy import Boolean, Column, DateTime, String, Unicode
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import object_session

from baph.auth.models.organization import Organization
from baph.auth.models.permission.utils import get_or_fail
from baph.auth.mixins import UserPermissionMixin
from baph.auth.registration import settings as auth_settings
from baph.db import ORM
from .utils import _generate_user_id_column


orm = ORM.get()
Base = orm.Base

UNUSABLE_PASSWORD = '!'


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
        if (
          not getattr(settings, 'BAPH_AUTH_WITHOUT_USERNAMES', False)
          and not username
        ):
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
        session.flush()
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

    username = Column(Unicode(75), index=True,
                      nullable=auth_settings.BAPH_AUTH_WITHOUT_USERNAMES)
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
