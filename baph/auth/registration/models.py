# -*- coding: utf-8 -*-
'''\
:mod:`baph.auth.registration.models` -- Registration-related SQLAlchemy Models
==============================================================================
'''

from baph.auth.models import User, AUTH_USER_FIELD
from baph.db.models import Model
from baph.db.orm import ORM
from baph.decorators.db import sqlalchemy_session
from baph.utils.importing import import_attr
render_to_string = import_attr(['coffin.shortcuts'], 'render_to_string')
from datetime import datetime, timedelta
from django.conf import settings
from django.utils.hashcompat import sha_constructor
import random
import re
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relation

orm = ORM.get()
SHA1_RE = re.compile(r'^[a-f0-9]{40}$')


class RegistrationProfile(orm.Base, Model):
    '''A simple profile which stores an activation key for use during user
    account registration.

    While it is possible to use this model as the value of the
    :setting:`AUTH_PROFILE_MODULE` setting, it's not recommended that you do
    so. This model's sole purpose is to store data temporarily during
    account registration and activation.

    '''
    __tablename__ = 'auth_registration_profile'

    ACTIVATED = u"ALREADY_ACTIVATED"

    user_id = Column(AUTH_USER_FIELD, ForeignKey(User.id), primary_key=True)
    activation_key = Column(String(40), nullable=False)

    user = relation(User)

    def __unicode__(self):
        return u'Registration information for %s' % self.user

    def activation_key_expired(self):
        '''Determine whether the user's activation key has expired.

        Key expiration is determined by a two-step process:

        1. If the user has already activated, the key will have been
           reset to the string :attr:`ACTIVATED`. Re-activating is
           not permitted, and so this method returns :const:`True` in this
           case.

        2. Otherwise, the date the user signed up is incremented by
           the number of days specified in the setting
           :const:`ACCOUNT_ACTIVATION_DAYS` (which should be the number of
           days after signup during which a user is allowed to
           activate their account); if the result is less than or
           equal to the current date, the key has expired and this
           method returns :const:`True`.

        :returns: :const:`True` if the key has expired, :const:`False`
                  otherwise.
        :rtype: :class:`bool`
        '''
        expiration_date = timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
        return self.activation_key == self.ACTIVATED or \
               (self.user.date_joined + expiration_date <= datetime.now())
    activation_key_expired.boolean = True

    def send_activation_email(self, site):
        '''Send an activation email to the user associated with this
        ``RegistrationProfile``.

        The activation email will make use of two templates:

        ``registration/activation_email_subject.txt``
            This template will be used for the subject line of the
            email. Because it is used as the subject line of an email,
            this template's output **must** be only a single line of
            text; output longer than one line will be forcibly joined
            into only a single line.

        ``registration/activation_email.txt``
            This template will be used for the body of the email.

        These templates will each receive the following context
        variables:

        ``activation_key``
            The activation key for the new account.

        ``expiration_days``
            The number of days remaining during which the account may
            be activated.

        ``site``
            An object representing the site on which the user
            registered; depending on whether :mod:`baph.sites` is installed,
            this may be an instance of either :class:`baph.sites.models.Site`
            (if the sites application is installed) or
            :class:`baph.sites.models.RequestSite` (if not). Consult the
            documentation for the Django/Baph sites framework for details
            regarding these objects' interfaces.
        '''
        ctx_dict = {
            'activation_key': self.activation_key,
            'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
            'subject_prefix': settings.EMAIL_SUBJECT_PREFIX,
            'site': site,
        }
        subject = render_to_string('registration/activation_email_subject.txt',
                                   ctx_dict)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())

        message = render_to_string('registration/activation_email.txt',
                                   ctx_dict)

        self.user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)

    @classmethod
    @sqlalchemy_session
    def activate_user(cls, activation_key, session=None):
        '''Validate an activation key and activate the corresponding
        :class:`~baph.auth.models.User` if valid.

        If the key is valid and has not expired, return the
        :class:`~baph.auth.models.User` after activating.

        If the key is not valid or has expired, return :const:`False`.

        If the key is valid but the :class:`~baph.auth.models.User` is already
        active, return :const:`False`.

        To prevent reactivation of an account which has been
        deactivated by site administrators, the activation key is
        reset to the string constant :attr:`ACTIVATED` after successful
        activation.

        :param activation_key: The activation key of the user who will be
                               activated.
        :type activation_key: :class:`str`
        '''
        # Make sure the key we're trying conforms to the pattern of a
        # SHA1 hash; if it doesn't, no point trying to look it up in
        # the database.
        if SHA1_RE.search(activation_key):
            profile = session.query(cls) \
                             .filter_by(activation_key=activation_key) \
                             .first()
            if not profile:
                return False
            if not profile.activation_key_expired():
                user = profile.user
                user.is_active = True
                profile.activation_key = cls.ACTIVATED
                session.commit()
                return user
        return False

    @classmethod
    @sqlalchemy_session
    def create_inactive_user(cls, username, email, password, site,
                             send_email=True, session=None):
        '''Create a new, inactive :class:`~baph.auth.models.User`, generate a
        :class:`RegistrationProfile` and email its activation key to the
        :class:`~baph.auth.models.User`.

        :param username: The username of the user.
        :type username: :class:`unicode`
        :param email: The email address of the user.
        :type email: :class:`str`
        :param password: The password of the user.
        :type password: :class:`unicode`
        :param site: The site associated with the user.
        :type site: :class:`baph.sites.models.Site` or
                    :class:`baph.sites.models.RequestSite`
        :param send_email: Whether an activation email will be sent to the new
                           user.
        :type send_email: :class:`bool`
        :rtype: :class:`baph.auth.models.User`
        '''
        new_user = User.create_user(username, email, password,
                                    session=session)
        new_user.is_active = False
        session.commit()

        registration_profile = cls.create_profile(new_user, session=session)

        if send_email:
            registration_profile.send_activation_email(site)

        return new_user

    @classmethod
    @sqlalchemy_session
    def create_profile(cls, user, session=None):
        '''Create a :class:`RegistrationProfile` for a given
        :class:`~baph.auth.models.User`.

        The activation key for the :class:`RegistrationProfile` will be a
        SHA1 hash, generated from a combination of the
        :class:`~baph.auth.models.User`'s username and a random salt.

        :rtype: :class:`RegistrationProfile`
        '''
        salt = sha_constructor(str(random.random())).hexdigest()[:5]
        username = user.username
        if isinstance(username, unicode):
            username = username.encode('utf-8')
        activation_key = sha_constructor(salt + username).hexdigest()
        profile = RegistrationProfile(user=user, activation_key=activation_key)
        session.add(profile)
        session.commit()
        return profile

    @classmethod
    @sqlalchemy_session
    def delete_expired_users(cls, session=None):
        '''Remove expired instances of :class:`RegistrationProfile` and their
        associated users.

        Accounts to be deleted are identified by searching for
        instances of :class:`RegistrationProfile` with expired activation
        keys, and then checking to see if their associated ``User``
        instances have the field ``is_active`` set to ``False``; any
        ``User`` who is both inactive and has an expired activation
        key will be deleted.

        It is recommended that this method be executed regularly as
        part of your routine site maintenance; this application
        provides a custom management command which will call this
        method, accessible as ``manage.py cleanupregistration``.

        Regularly clearing out accounts which have never been
        activated serves two useful purposes:

        1. It alleviates the ocasional need to reset a
           :class:`RegistrationProfile` and/or re-send an activation email
           when a user does not receive or does not act upon the
           initial activation email; since the account will be
           deleted, the user will be able to simply re-register and
           receive a new activation key.

        2. It prevents the possibility of a malicious user registering
           one or more accounts and never activating them (thus
           denying the use of those usernames to anyone else); since
           those accounts will be deleted, the usernames will become
           available for use again.

        If you have a troublesome ``User`` and wish to disable their
        account while keeping it in the database, simply delete the
        associated :class:`RegistrationProfile`; an inactive ``User`` which
        does not have an associated :class:`RegistrationProfile` will not
        be deleted.
        '''
        for profile in session.query(cls).all():
            if profile.activation_key_expired():
                user = profile.user
                if not user.is_active:
                    session.delete(user)
                    session.delete(profile)
        session.commit()
