# -*- coding: utf-8 -*-

from __future__ import absolute_import
from baph.auth.models import orm, User
from baph.test.base import BaseTestCase
from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
import re


class AuthViewsTestCase(BaseTestCase):
    '''Helper base class for all of the following test cases.'''
    urls = 'baph.auth.urls'

    @classmethod
    def setUpClass(cls):
        super(AuthViewsTestCase, cls).setUpClass()
        cls.session = orm.sessionmaker()
        User.__table__.create()
        cls.user = User.create_user(u'testclient', 'testclient@example.com',
                                    session=cls.session)
        cls.user.set_password('password')
        cls.staff = User.create_staff(u'staff', 'staffmember@example.com',
                                      '123', session=cls.session)
        User.create_user(u'testclient2', 'testclient2@example.com',
                         session=cls.session)

    @classmethod
    def tearDownClass(cls):
        cls.session.close()
        User.__table__.drop()
        super(AuthViewsTestCase, cls).tearDownClass()

    def setUp(self):
        self.old_LANGUAGES = settings.LANGUAGES
        self.old_LANGUAGE_CODE = settings.LANGUAGE_CODE
        settings.LANGUAGES = (('en', 'English'),)
        settings.LANGUAGE_CODE = 'en'
        mail.outbox = []

    def tearDown(self):
        settings.LANGUAGES = self.old_LANGUAGES
        settings.LANGUAGE_CODE = self.old_LANGUAGE_CODE


class LoginLogoutTestCase(AuthViewsTestCase):
    '''Test case for auth-related views.'''

    def test_login(self, password='password'):
        response = self.client.post(reverse('baph.auth.views.login'), {
            'username': 'testclient',
            'password': password,
        })
        self.assertEqual(response.status_code, 302)
        self.assert_(response['Location']\
                             .endswith(settings.LOGIN_REDIRECT_URL))

    def test_login_fail(self, password='fail_password'):
        response = self.client.post(reverse('baph.auth.views.login'), {
            'username': 'testclient',
            'password': password,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('Please enter a correct username and password. Note ' \
                      'that both fields are case-sensitive.', response.content)

        response = self.client.post(reverse('baph.auth.views.login'), {
            'username': 'testclientfail',
            'password': password,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('Please enter a correct username and password. Note ' \
                      'that both fields are case-sensitive.', response.content)

    def test_logout(self):
        response = self.client.get(reverse('baph.auth.views.logout'))
        self.assertLess(response.status_code, 400)

    def test_14377(self):
        '''Django bug # 14377.'''
        self.test_login()
        response = self.client.get(reverse('baph.auth.views.logout'))
        self.assertIn('site', response.context)


class PasswordResetTestCase(AuthViewsTestCase):

    def setUp(self):
        super(PasswordResetTestCase, self).setUp()
        self.staff.set_password('123')
        self.session.merge(self.staff)
        self.session.commit()

    def test_email_not_found(self):
        '''Error is raised if the provided email address isn't currently
        registered.
        '''
        response = self.client.get('/password_reset/')
        self.assertEquals(response.status_code, 200)
        response = self.client.post('/password_reset/', {
            'email': 'not_a_real_email@email.com',
        })
        self.assertIn('''\
That e-mail address doesn&amp;#39;t have an associated user account''',
                      str(response))
        self.assertEquals(len(mail.outbox), 0)

    def test_unusable_password(self):
        '''Error is raised if the provided email address doesn't allow the
        password to be set (it's set to UNUSABLE_PASSWORD).
        '''
        response = self.client.get('/password_reset/')
        self.assertEquals(response.status_code, 200)
        response = self.client.post('/password_reset/', {
            'email': 'testclient2@example.com',
        })
        self.assertIn('''\
That e-mail address doesn&amp;#39;t allow the password to be set''',
                      str(response))
        self.assertEquals(len(mail.outbox), 0)

    def test_email_found(self):
        '''Email is sent if a valid email address is provided for password
        reset.'''
        response = self.client.post('/password_reset/', {
            'email': 'staffmember@example.com',
        })
        self.assertEquals(response.status_code, 302)
        self.assertEquals(len(mail.outbox), 1)
        self.assertIn('http://', mail.outbox[0].body)

    def _test_confirm_start(self):
        # Start by creating the email
        response = self.client.post('/password_reset/', {
            'email': 'staffmember@example.com',
        })
        self.assertEquals(response.status_code, 302)
        self.assertEquals(len(mail.outbox), 1)
        return self._read_signup_email(mail.outbox[0])

    def _read_signup_email(self, email):
        urlmatch = re.search(r'https?://[^/]*(/.*reset/\S*)', email.body)
        self.assertIsNotNone(urlmatch, 'No URL found in sent email')
        return urlmatch.group(), urlmatch.groups()[0]

    def test_confirm_valid(self):
        url, path = self._test_confirm_start()
        response = self.client.get(path)
        # redirect to a 'complete' page:
        self.assertEquals(response.status_code, 200)
        self.assertIn('Please enter your new password', response.content)

    def test_confirm_invalid(self):
        url, path = self._test_confirm_start()
        # Let's munge the token in the path, but keep the same length,
        # in case the URLconf will reject a different length.
        path = path[:-5] + ('0' * 4) + path[-1]

        response = self.client.get(path)
        self.assertEquals(response.status_code, 200)
        self.assertIn('The password reset link was invalid', response.content)

    def test_confirm_invalid_post(self):
        '''Same as test_confirm_invalid, but trying to do a POST instead.'''
        url, path = self._test_confirm_start()
        path = path[:-5] + ('0' * 4) + path[-1]

        self.client.post(path, {
            'new_password1': 'anewpassword',
            'new_password2': 'anewpassword',
        })
        # Check the password has not been changed
        u = self.session.query(User) \
                        .filter_by(email='staffmember@example.com') \
                        .first()
        self.assertFalse(u.check_password('anewpassword'))

    def test_confirm_complete(self):
        url, path = self._test_confirm_start()
        response = self.client.post(path, {'new_password1': 'anewpassword',
                                           'new_password2': 'anewpassword'})
        # It redirects us to a 'complete' page:
        self.assertEquals(response.status_code, 302)
        # Check the password has been changed
        u = self.session.query(User) \
                        .filter_by(email='staffmember@example.com') \
                        .first()
        self.assertTrue(u.check_password('anewpassword'))

        # Check we can't use the link again
        response = self.client.get(path)
        self.assertEquals(response.status_code, 200)
        self.assertIn('The password reset link was invalid', response.content)

    def test_confirm_different_passwords(self):
        url, path = self._test_confirm_start()
        response = self.client.post(path, {
            'new_password1': 'anewpassword',
            'new_password2': 'x',
        })
        self.assertEquals(response.status_code, 200)
        self.assertIn('The two password fields didn&amp;#39;t match',
                      response.content)
