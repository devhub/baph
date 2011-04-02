# -*- coding: utf-8 -*-

from baph.auth.models import AnonymousUser, orm, User
from baph.test.base import BaseTestCase
from django.conf import settings
from django.core import mail


class AuthTestCase(BaseTestCase):
    '''Test case for :mod:`baph.auth`.'''

    @classmethod
    def setUpClass(cls):
        super(AuthTestCase, cls).setUpClass()
        cls.session = orm.sessionmaker()
        User.__table__.create()

    @classmethod
    def tearDownClass(cls):
        super(AuthTestCase, cls).tearDownClass()
        cls.session.close()
        User.__table__.drop()

    def setUp(self):
        mail.outbox = []
        self.old_algorithm = getattr(settings, 'AUTH_DIGEST_ALGORITHM', 'sha1')

    def tearDown(self):
        settings.AUTH_DIGEST_ALGORITHM = self.old_algorithm
        self.session.rollback()

    def test_anonymous_user(self):
        a = AnonymousUser()
        self.assertFalse(a.is_active)
        self.assertTrue(a.is_anonymous())
        self.assertFalse(a.is_authenticated())
        self.assertFalse(a.is_staff)
        self.assertFalse(a.is_superuser)

    def test_create_user(self):
        u = User.create_user(u'testuser', 'test@example.com', 'testpw')
        self.assertTrue(u.has_usable_password())
        self.assertFalse(u.check_password('bad'))
        self.assertTrue(u.check_password('testpw'))
        u.set_unusable_password()
        u.first_name = u' ¡'
        u.last_name = u'π '
        self.session.commit()
        self.assertFalse(u.check_password('testpw'))
        self.assertTrue(u.is_active)
        self.assertFalse(u.is_anonymous())
        self.assertTrue(u.is_authenticated())
        self.assertFalse(u.is_staff)
        self.assertFalse(u.is_superuser)
        self.assertEqual(unicode(u), u'testuser')
        self.assertEqual(u.get_full_name(), u'¡ π')

        u2 = User.create_user(u'testuser2', 'test2@example.com',
                              session=self.session)
        self.assertFalse(u2.has_usable_password())

        uu = User.create_user(u'testμser', 'testunicode@example.com',
                              session=self.session)
        self.assertEqual(uu.get_absolute_url(), '/users/test%CE%BCser/')

    def test_user_email(self):
        u3 = User.create_user(u'testuser3', 'test3@EXAMPLE.com',
                              session=self.session)
        self.assertEqual(u3.email, 'test3@example.com')

        self.assertRaises(ValueError, User.create_user, u'testuser4', 'test4',
                          session=self.session)

    def test_create_staff(self):
        st = User.create_staff(u'staff', 'staff@example.com', 'staff',
                               session=self.session)
        self.assertFalse(st.is_superuser)
        self.assertTrue(st.is_active)
        self.assertTrue(st.is_staff)
        st = User.create_staff(u'staff2', 'staff2@example.com', 'staff2',
                               session=self.session)
        self.assertFalse(st.is_superuser)
        self.assertTrue(st.is_active)
        self.assertTrue(st.is_staff)

    def test_create_superuser(self):
        su = User.create_superuser(u'super', 'super@example.com', 'super',
                                   session=self.session)
        self.assertTrue(su.is_superuser)
        self.assertTrue(su.is_active)
        self.assertTrue(su.is_staff)
        su = User.create_superuser(u'super2', 'super2@example.com', 'super2')
        self.assertTrue(su.is_superuser)
        self.assertTrue(su.is_active)
        self.assertTrue(su.is_staff)

    def test_email_user(self):
        addr = 'testuseremail@example.com'
        eu = User.create_user('testuseremail', addr, session=self.session)
        subject = 'Test Subject'
        msg = 'This is a Test.'
        eu.email_user(subject, msg, 'foo@example.com')
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [addr])
        self.assertEqual(email.subject, subject)
        self.assertEqual(email.body, msg)

    def test_password_algorithm(self):
        settings.AUTH_DIGEST_ALGORITHM = 'sha256'
        user = User.create_user('testalgo', 'testalgo@example.com', 'testpw',
                                session=self.session)
        self.assertIn('$', user.password)
        algo = user.password.split('$')[0]
        self.assertEqual(algo, settings.AUTH_DIGEST_ALGORITHM)
        self.assertTrue(user.check_password('testpw'))
        user.set_password('testpw224', algo='sha224')
        self.session.commit()
        self.assertIn('$', user.password)
        algo = user.password.split('$')[0]
        self.assertEqual(algo, 'sha224')
        self.assertTrue(user.check_password('testpw224'))
        settings.AUTH_DIGEST_ALGORITHM = 'sha512'
        user2 = User.create_user('testalgo2', 'testalgo2@example.com',
                                 'testpw2', session=self.session)
        self.assertIn('$', user2.password)
        algo = user2.password.split('$')[0]
        self.assertEqual(algo, settings.AUTH_DIGEST_ALGORITHM)
        self.assertTrue(user2.check_password('testpw2'))
