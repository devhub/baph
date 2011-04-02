from baph.auth.models import User
from baph.auth.registration import forms
from baph.auth.registration.models import RegistrationProfile
from baph.db.orm import ORM
from baph.test.base import BaseTestCase
import datetime
from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from sqlalchemy.orm import join


class RegistrationViewTests(BaseTestCase):
    """
    Test the registration views.

    """
    urls = 'auth.registration.urls'

    ALICE_DATA = {
        'username': 'alice',
        'email': 'alice@example.com',
        'password1': 'swordfish',
        'password2': 'swordfish',
    }

    BOB_DATA = {
        'username': 'bob',
        'email': 'bob@example.com',
        'password1': 'secret',
        'password2': 'secret',
    }

    INVALID_BOB_DATA = {
        'username': 'bob',
        'email': 'bobe@example.com',
        'password1': 'foo',
        'password2': 'bar',
    }

    @classmethod
    def setUpClass(cls):
        super(RegistrationViewTests, cls).setUpClass()
        User.__table__.create()
        orm = ORM.get()
        cls.session = orm.sessionmaker()

    @classmethod
    def tearDownClass(cls):
        User.__table__.drop()
        super(RegistrationViewTests, cls).tearDownClass()

    def setUp(self):
        '''These tests use the default backend, since we know it's
        available; that needs to have ``ACCOUNT_ACTIVATION_DAYS`` set.
        '''
        self.old_activation = getattr(settings, 'ACCOUNT_ACTIVATION_DAYS',
                                      None)
        if self.old_activation is None:
            settings.ACCOUNT_ACTIVATION_DAYS = 7
        RegistrationProfile.__table__.create()
        mail.outbox = []

    def tearDown(self):
        '''Yank ``ACCOUNT_ACTIVATION_DAYS`` back out if it wasn't
        originally set.
        '''
        RegistrationProfile.__table__.drop()
        if self.old_activation is None:
            settings.ACCOUNT_ACTIVATION_DAYS = self.old_activation
        for username in [u'alice', u'bob']:
            user = self.session.query(User) \
                       .filter_by(username=username) \
                       .first()
            if user:
                self.session.delete(user)
        self.session.commit()

    @staticmethod
    def url_reverse(view_name):
        return 'http://testserver%s' % reverse(view_name)

    def test_registration_view_initial(self):
        '''A ``GET`` to the ``register`` view uses the appropriate
        template and populates the registration form into the context.
        '''
        response = self.client.get(reverse('registration_register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'registration/registration_form.html')
        self.assertTrue(isinstance(response.context['form'],
                                   forms.RegistrationForm))

    def test_registration_view_success(self):
        '''A ``POST`` to the ``register`` view with valid data properly
        creates a new user and issues a redirect.
        '''
        response = self.client.post(reverse('registration_register'),
                                    data=self.ALICE_DATA)
        self.assertRedirects(response,
                             self.url_reverse('registration_complete'))
        self.assertEqual(self.session.query(RegistrationProfile).count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_registration_view_failure(self):
        '''A ``POST`` to the ``register`` view with invalid data does not
        create a user, and displays appropriate error messages.
        '''
        response = self.client.post(reverse('registration_register'),
                                    data=self.INVALID_BOB_DATA)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertFormError(response, 'form', field=None,
                             errors=u"The two password fields didn't match.")
        self.assertEqual(len(mail.outbox), 0)

    def test_registration_view_closed(self):
        '''Any attempt to access the ``register`` view when registration
        is closed fails and redirects.
        '''
        old_allowed = getattr(settings, 'REGISTRATION_OPEN', True)
        settings.REGISTRATION_OPEN = False

        closed_redirect = 'http://testserver%s' % \
                          reverse('registration_disallowed')

        response = self.client.get(reverse('registration_register'))
        self.assertRedirects(response, closed_redirect)

        # Even if valid data is posted, it still shouldn't work.
        response = self.client.post(reverse('registration_register'),
                                    data=self.ALICE_DATA)
        self.assertRedirects(response, closed_redirect)
        self.assertEqual(self.session.query(RegistrationProfile).count(), 0)

        settings.REGISTRATION_OPEN = old_allowed

    def test_registration_template_name(self):
        '''Passing ``template_name`` to the ``register`` view will result
        in that template being used.
        '''
        path = reverse('registration_test_register_template_name')
        response = self.client.get(path)
        self.assertTemplateUsed(response,
                                'registration/test_template_name.html')

    def test_registration_extra_context(self):
        '''Passing ``extra_context`` to the ``register`` view will
        correctly populate the context.
        '''
        path = reverse('registration_test_register_extra_context')
        response = self.client.get(path)
        self.assertEqual(response.context['foo'], 'bar')
        # Callables in extra_context are called to obtain the value.
        self.assertEqual(response.context['callable'], 'called')

    def test_registration_disallowed_url(self):
        """
        Passing ``disallowed_url`` to the ``register`` view will
        result in a redirect to that URL when registration is closed.

        """
        old_allowed = getattr(settings, 'REGISTRATION_OPEN', True)
        settings.REGISTRATION_OPEN = False

        closed_redirect = \
            self.url_reverse('registration_test_custom_disallowed')

        path = reverse('registration_test_register_disallowed_url')
        response = self.client.get(path)
        self.assertRedirects(response, closed_redirect)

        settings.REGISTRATION_OPEN = old_allowed

    def test_registration_success_url(self):
        """
        Passing ``success_url`` to the ``register`` view will result
        in a redirect to that URL when registration is successful.

        """
        success_redirect = \
            self.url_reverse('registration_test_custom_success_url')
        path = reverse('registration_test_register_success_url')
        response = self.client.post(path, data=self.ALICE_DATA)
        self.assertRedirects(response, success_redirect)

    def test_valid_activation(self):
        '''Test that the ``activate`` view properly handles a valid activation
        (in this case, based on the default backend's activation window).
        '''
        success_redirect = self.url_reverse('registration_activation_complete')

        # First, register an account.
        self.client.post(reverse('registration_register'), data={
            'username': 'alice',
            'email': 'alice@example.com',
            'password1': 'swordfish',
            'password2': 'swordfish',
        })
        profile = self.session.query(RegistrationProfile) \
                              .select_from(join(RegistrationProfile, User)) \
                              .filter(User.username == u'alice') \
                              .first()
        self.assertIsNotNone(profile)
        path = reverse('registration_activate',
                       kwargs={'activation_key': profile.activation_key})
        response = self.client.get(path)
        self.assertRedirects(response, success_redirect)
        alice = self.session.query(User) \
                            .filter_by(username=u'alice') \
                            .first()
        self.assertTrue(alice.is_active)

    def test_invalid_activation(self):
        '''Test that the ``activate`` view properly handles an invalid
        activation (in this case, based on the default backend's activation
        window).
        '''
        # Register an account and reset its date_joined to be outside
        # the activation window.
        self.client.post(reverse('registration_register'),
                         data=self.BOB_DATA)
        expired_user = self.session.query(User) \
                                   .filter_by(username=u'bob') \
                                   .first()
        expired_user.date_joined -= \
            datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
        self.session.commit()

        expired_profile = self.session.query(RegistrationProfile) \
                                      .filter_by(user=expired_user) \
                                      .first()
        path = reverse('registration_activate', kwargs={
            'activation_key': expired_profile.activation_key,
        })
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['activation_key'],
                         expired_profile.activation_key)
        bob = self.session.query(User) \
                          .filter_by(username=u'bob') \
                          .first()
        self.assertIsNotNone(bob)
        self.assertFalse(bob.is_active)

    def test_activation_success_url(self):
        '''Passing ``success_url`` to the ``activate`` view and successfully
        activating will result in that URL being used for the redirect.
        '''
        success_redirect = 'http://testserver%s' % \
                           reverse('registration_test_custom_success_url')
        self.client.post(reverse('registration_register'),
                         data=self.ALICE_DATA)
        profile = self.session.query(RegistrationProfile) \
                              .select_from(join(RegistrationProfile, User)) \
                              .filter(User.username == u'alice') \
                              .first()
        path = reverse('registration_test_activate_success_url',
                       kwargs={'activation_key': profile.activation_key})
        response = self.client.get(path)
        self.assertRedirects(response, success_redirect)

    def test_activation_template_name(self):
        '''Passing ``template_name`` to the ``activate`` view will result
        in that template being used.
        '''
        path = reverse('registration_test_activate_template_name',
                       kwargs={'activation_key': 'foo'})
        response = self.client.get(path)
        self.assertTemplateUsed(response,
                                'registration/test_template_name.html')

    def test_activation_extra_context(self):
        '''Passing ``extra_context`` to the ``activate`` view will
        correctly populate the context.
        '''
        path = reverse('registration_test_activate_extra_context',
                       kwargs={'activation_key': 'foo'})
        response = self.client.get(path)
        self.assertEqual(response.context['foo'], 'bar')
        # Callables in extra_context are called to obtain the value.
        self.assertEqual(response.context['callable'], 'called')
