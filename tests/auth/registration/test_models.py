# -*- coding: utf-8 -*-

from __future__ import absolute_import
from baph.auth.models import User
from baph.auth.registration.models import RegistrationProfile
from baph.db.orm import ORM
from baph.sites.models import Site
from baph.test.base import BaseTestCase
from datetime import timedelta
from django.conf import settings
from django.core import mail, management
from django.utils.hashcompat import sha_constructor
import six


class RegistrationModelTests(BaseTestCase):
    '''Test the model and manager used in the default backend.'''
    user_info = {'username': 'alice',
                 'password': 'swordfish',
                 'email': 'alice@example.com'}

    @classmethod
    def setUpClass(cls):
        super(RegistrationModelTests, cls).setUpClass()
        Site.__table__.create()
        User.__table__.create()
        orm = ORM.get()
        cls.session = orm.sessionmaker()
        cls.user_info['session'] = cls.session
        site = Site(id=settings.SITE_ID, domain='example.com',
                    name=u'example.com')
        cls.session.add(site)
        cls.session.commit()

    @classmethod
    def tearDownClass(cls):
        User.__table__.drop()
        Site.__table__.drop()
        super(RegistrationModelTests, cls).tearDownClass()

    def setUp(self):
        RegistrationProfile.__table__.create()
        self.old_activation = getattr(settings, 'ACCOUNT_ACTIVATION_DAYS',
                                      None)
        settings.ACCOUNT_ACTIVATION_DAYS = 7
        mail.outbox = []

    def tearDown(self):
        settings.ACCOUNT_ACTIVATION_DAYS = self.old_activation
        for username in [u'alice', u'bob']:
            user = self.session.query(User) \
                       .filter_by(username=username) \
                       .first()
            if user:
                self.session.delete(user)
        self.session.commit()
        RegistrationProfile.__table__.drop()

    def create_inactive_user(self):
        site = Site.get_current()
        return RegistrationProfile.create_inactive_user(site=site,
                                                        **self.user_info)

    def test_profile_creation(self):
        '''Creating a registration profile for a user populates the
        profile with the correct user and a SHA1 hash to use as
        activation key.
        '''
        new_user = User.create_user(**self.user_info)
        profile = RegistrationProfile.create_profile(new_user)

        ct = self.session.query(RegistrationProfile).count()

        self.assertEqual(ct, 1)
        self.assertEqual(profile.user.id, new_user.id)
        self.assertRegexpMatches(profile.activation_key, '^[a-f0-9]{40}$')
        self.assertEqual(six.text_type(profile),
                         u'Registration information for alice')

    def test_activation_email(self):
        ''':meth:`RegistrationProfile.send_activation_email` sends an email.
        '''
        new_user = User.create_user(**self.user_info)
        profile = RegistrationProfile.create_profile(new_user)
        profile.send_activation_email(Site.get_current())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user_info['email']])

    def test_user_creation(self):
        '''Creating a new user populates the correct data, and sets the user's
        account inactive.
        '''
        new_user = self.create_inactive_user()
        self.assertEqual(new_user.username, 'alice')
        self.assertEqual(new_user.email, 'alice@example.com')
        self.assertTrue(new_user.check_password('swordfish'))
        self.assertFalse(new_user.is_active)

    def test_user_creation_email(self):
        '''By default, creating a new user sends an activation email.'''
        self.create_inactive_user()
        self.assertEqual(len(mail.outbox), 1)

    def test_user_creation_no_email(self):
        '''Passing ``send_email=False`` when creating a new user will not
        send an activation email.
        '''
        site = Site.get_current()
        RegistrationProfile.create_inactive_user(send_email=False, site=site,
                                                 **self.user_info)
        self.assertEqual(len(mail.outbox), 0)

    def test_unexpired_account(self):
        ''':meth:`RegistrationProfile.activation_key_expired` is :const:`False`
        within the activation window.
        '''
        new_user = self.create_inactive_user()
        profile = self.session.query(RegistrationProfile) \
                              .filter_by(user=new_user) \
                              .first()
        self.assertFalse(profile.activation_key_expired())

    def test_expired_account(self):
        ''':meth:`RegistrationProfile.activation_key_expired` is :const:`True`
        outside the activation window.
        '''
        new_user = self.create_inactive_user()
        new_user.date_joined -= \
            timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS + 1)
        self.session.commit()
        profile = self.session.query(RegistrationProfile) \
                              .filter_by(user=new_user) \
                              .first()
        self.assertTrue(profile.activation_key_expired())

    def test_valid_activation(self):
        '''Activating a user within the permitted window makes the account
        active, and resets the activation key.
        '''
        new_user = self.create_inactive_user()
        profile = self.session.query(RegistrationProfile) \
                              .filter_by(user=new_user) \
                              .first()
        activated = RegistrationProfile.activate_user(profile.activation_key)

        self.assertTrue(isinstance(activated, User))
        self.assertEqual(activated.id, new_user.id)
        self.assertTrue(activated.is_active)

        profile = self.session.query(RegistrationProfile) \
                              .filter_by(user=new_user) \
                              .first()
        self.assertEqual(profile.activation_key, RegistrationProfile.ACTIVATED)

    def test_expired_activation(self):
        '''Attempting to activate outside the permitted window does not
        activate the account.
        '''
        new_user = self.create_inactive_user()
        new_user.date_joined -= \
            timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS + 1)
        self.session.commit()

        profile = self.session.query(RegistrationProfile) \
                              .filter_by(user=new_user) \
                              .first()
        activated = RegistrationProfile.activate_user(profile.activation_key)

        self.assertFalse(isinstance(activated, User))
        self.assertFalse(activated)

        new_user = self.session.query(User) \
                               .filter_by(username=u'alice') \
                               .first()
        self.assertFalse(new_user.is_active)

        profile = self.session.query(RegistrationProfile) \
                              .filter_by(user=new_user) \
                              .first()
        self.assertNotEqual(profile.activation_key,
                            RegistrationProfile.ACTIVATED)

    def test_activation_invalid_key(self):
        '''Attempting to activate with a key which is not a SHA1 hash fails.'''
        self.assertFalse(RegistrationProfile.activate_user('foo'))

    def test_activation_already_activated(self):
        '''Attempting to re-activate an already-activated account fails.'''
        new_user = self.create_inactive_user()
        profile = self.session.query(RegistrationProfile) \
                              .filter_by(user=new_user) \
                              .first()
        RegistrationProfile.activate_user(profile.activation_key)

        profile = self.session.query(RegistrationProfile) \
                              .filter_by(user=new_user) \
                              .first()
        key = profile.activation_key
        self.assertFalse(RegistrationProfile.activate_user(key))

    def test_activation_nonexistent_key(self):
        """
        Attempting to activate with a non-existent key (i.e., one not
        associated with any account) fails.

        """
        # Due to the way activation keys are constructed during
        # registration, this will never be a valid key.
        invalid_key = sha_constructor('foo').hexdigest()
        self.assertFalse(RegistrationProfile.activate_user(invalid_key))

    def test_expired_user_deletion(self):
        ''':meth:`RegistrationProfile.delete_expired_users` only deletes
        inactive users whose activation window has expired.
        '''
        site = Site.get_current()
        self.create_inactive_user()
        expired_user = \
            RegistrationProfile.create_inactive_user(username='bob',
                                                     password='secret',
                                                     email='bob@example.com',
                                                     session=self.session,
                                                     site=site)
        expired_user.date_joined -= \
            timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS + 1)
        self.session.commit()

        RegistrationProfile.delete_expired_users()
        ct = self.session.query(RegistrationProfile).count()
        self.assertEqual(ct, 1)
        user_count = self.session.query(User) \
                                 .filter_by(username=u'bob') \
                                 .count()
        self.assertEqual(user_count, 0)

    def test_management_command(self):
        '''The ``cleanupregistration`` management command properly deletes
        expired accounts.
        '''
        site = Site.get_current()
        self.create_inactive_user()
        expired_user = \
            RegistrationProfile.create_inactive_user(username='bob',
                                                     password='secret',
                                                     email='bob@example.com',
                                                     session=self.session,
                                                     site=site)
        expired_user.date_joined -= \
            timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS + 1)
        self.session.commit()

        management.call_command('cleanupregistration')
        ct = self.session.query(RegistrationProfile).count()
        self.assertEqual(ct, 1)
        user_count = self.session.query(User) \
                                 .filter_by(username=u'bob') \
                                 .count()
        self.assertEqual(user_count, 0)
