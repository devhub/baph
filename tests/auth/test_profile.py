# -*- coding: utf-8 -*-

from __future__ import absolute_import
from baph.auth.models import orm, SiteProfileNotAvailable, User
from baph.test.base import TestCase
from django.conf import settings


class ProfileTestCase(TestCase):
    '''Test case for user profiles.'''

    @classmethod
    def setUpClass(cls):
        cls.session = orm.sessionmaker()
        User.__table__.create()
        cls.user = User.create_user(u'testclient', 'testclient@example.com',
                                    session=cls.session)

    @classmethod
    def tearDownClass(cls):
        cls.session.close()
        User.__table__.drop()

    def setUp(self):
        '''Backs up the AUTH_PROFILE_MODULE value, if it exists.'''
        self.old_AUTH_PROFILE_MODULE = getattr(settings,
                                               'AUTH_PROFILE_MODULE', None)

    def tearDown(self):
        '''Restores the AUTH_PROFILE_MODULE -- if it was not set it is deleted,
        otherwise the old value is restored.'''
        if self.old_AUTH_PROFILE_MODULE is None and \
           hasattr(settings, 'AUTH_PROFILE_MODULE'):
            del settings.AUTH_PROFILE_MODULE

        if self.old_AUTH_PROFILE_MODULE is not None:
            settings.AUTH_PROFILE_MODULE = self.old_AUTH_PROFILE_MODULE

    def test_not_available_unset(self):
        '''Calling get_profile without AUTH_PROFILE_MODULE set.'''
        if hasattr(settings, 'AUTH_PROFILE_MODULE'):
            del settings.AUTH_PROFILE_MODULE
        self.assertRaises(SiteProfileNotAvailable, self.user.get_profile)

    def test_not_available_bad_syntax(self):
        '''Bad syntax in AUTH_PROFILE_MODULE'''
        settings.AUTH_PROFILE_MODULE = 'foobar'
        self.assertRaises(SiteProfileNotAvailable, self.user.get_profile)

    def test_not_available_nonexistent_module(self):
        '''Profile module that doesn't exist.'''
        settings.AUTH_PROFILE_MODULE = 'foo.bar'
        self.assertRaises(SiteProfileNotAvailable, self.user.get_profile)
