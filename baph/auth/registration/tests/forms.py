from django.utils.translation import ugettext_lazy as _

from baph.auth.models import User
from baph.auth.registration import forms
from baph.db.orm import ORM
from baph.test import TestCase
from baph.auth.registration import settings as auth_settings


orm = ORM.get()

class SignupFormTests(TestCase):
    """ Test the signup form. """
    fixtures = ['users']

    def test_signup_form(self):
        """
        Test that the ``SignupForm`` checks for unique usernames and unique
        e-mail addresses.

        """
        auth_settings.BAPH_AUTH_WITHOUT_USERNAMES = False

        invalid_data_dicts = [
            # Non-alphanumeric username.
            #{'data': {'username': 'foo@bar',
            #          'email': 'foo@example.com',
            #          'password1': 'foo',
            #          'password2': 'foo',
            #          'tos': 'on'},
            # 'error': ('username', [_(u'Username must contain only letters, '
            #    'numbers, dots and underscores.')])},
            # Password is not the same
            {'data': {'username': 'katy-',
                      'email': 'katy@newexample.com',
                      'password1': 'foo',
                      'password2': 'foo2',
                      'tos': 'on'},
             'error': ('__all__', [_(u'The two password fields didn\'t match.')])},

            # Already taken username
            {'data': {'username': 'john',
                      'email': 'john@newexample.com',
                      'password1': 'foo',
                      'password2': 'foo',
                      'tos': 'on'},
             'error': ('username', [_(u'This username is already taken')])},

            # Forbidden username
            #{'data': {'username': 'SignUp',
            #          'email': 'foo@example.com',
            #          'password1': 'foo',
            #          'password2': 'foo2',
            #          'tos': 'on'},
            # 'error': ('username', [_(u'This username is not allowed.')])},

            # Already taken email
            {'data': {'username': 'alice',
                      'email': 'john@example.com',
                      'password1': 'foo',
                      'password2': 'foo',
                      'tos': 'on'},
             'error': ('email', [_(u'This email is already taken')])},
        ]
        for invalid_dict in invalid_data_dicts:
            form = forms.SignupForm(data=invalid_dict['data'])
            self.failIf(form.is_valid())
            self.assertEqual(form.errors[invalid_dict['error'][0]],
                             invalid_dict['error'][1])


        # And finally, a valid form.
        form = forms.SignupForm(data={'username': 'foo.bla',
                                      'email': 'foo@example.com',
                                      'password1': 'foo',
                                      'password2': 'foo',
                                      'tos': 'on'})

        self.failUnless(form.is_valid())

class AuthenticationFormTests(TestCase):
    """ Test the ``AuthenticationForm`` """

    fixtures = ['users',]

    def test_signin_form(self):
        """
        Check that the ``SigninForm`` requires both identification and password

        """
        auth_settings.BAPH_AUTH_WITHOUT_USERNAMES = False
        
        invalid_data_dicts = [
            {'data': {'identification': '',
                      'password': 'inhalefish'},
             'error': ('identification', [u'Either supply us with your email or username.'])},
            {'data': {'identification': 'john',
                      'password': 'inhalefish'},
             'error': ('__all__', [u'Please enter a correct username or email and password. Note that both fields are case-sensitive.'])}
        ]

        for invalid_dict in invalid_data_dicts:
            form = forms.AuthenticationForm(data=invalid_dict['data'])
            self.failIf(form.is_valid())
            self.assertEqual(form.errors[invalid_dict['error'][0]],
                             invalid_dict['error'][1])

        valid_data_dicts = [
            {'identification': 'john',
             'password': 'blowfish'},
            {'identification': 'john@example.com',
             'password': 'blowfish'}
        ]

        for valid_dict in valid_data_dicts:
            form = forms.AuthenticationForm(valid_dict)
            self.failUnless(form.is_valid())

    def test_signin_form_email(self):
        """
        Test that the signin form has a different label is
        ``USERENA_WITHOUT_USERNAME`` is set to ``True``

        """
        auth_settings.BAPH_AUTH_WITHOUT_USERNAMES = True

        form = forms.AuthenticationForm(data={'identification': "john",
                                              'password': "blowfish"})

        correct_label = "Email"
        self.assertEqual(form.fields['identification'].label,
                         correct_label)

        # Restore default settings
        auth_settings.BAPH_AUTH_WITHOUT_USERNAMES = False

class SignupFormOnlyEmailTests(TestCase):
    """
    Test the :class:`SignupFormOnlyEmail`.

    This is the same form as :class:`SignupForm` but doesn't require an
    username for a successfull signup.

    """
    fixtures = ['users']

    def test_signup_form_only_email(self):
        """
        Test that the form has no username field. And that the username is
        generated in the save method

        """
        valid_data = {'email': 'hans@gretel.com',
                      'password1': 'blowfish',
                      'password2': 'blowfish'}

        form = forms.SignupFormOnlyEmail(data=valid_data)

        # Should have no username field
        self.failIf(form.fields.get('username', False))

        # Form should be valid.
        self.failUnless(form.is_valid())

        # Creates an unique username
        user = form.save()

        self.failUnless(len(user.username), 5)

class ChangeEmailFormTests(TestCase):
    """ Test the ``ChangeEmailForm`` """
    fixtures = ['users']

    def test_change_email_form(self):
        session = orm.sessionmaker()
        user = session.query(User).get(1)
        session.close()
        invalid_data_dicts = [
            # No change in e-mail address
            {'data': {'email': 'john@example.com'},
             'error': ('email', [u'You\'re already known under this email.'])},
            # An e-mail address used by another
            {'data': {'email': 'jane@example.com'},
             'error': ('email', [u'This email is already in use. Please supply a different email.'])},
        ]
        for invalid_dict in invalid_data_dicts:
            form = forms.ChangeEmailForm(user, data=invalid_dict['data'])
            self.failIf(form.is_valid())
            self.assertEqual(form.errors[invalid_dict['error'][0]],
                             invalid_dict['error'][1])

        # Test a valid post
        form = forms.ChangeEmailForm(user,
                                     data={'email': 'john@newexample.com'})
        self.failUnless(form.is_valid())

    def test_form_init(self):
        """ The form must be initialized with a ``User`` instance. """
        self.assertRaises(TypeError, forms.ChangeEmailForm, None)

class EditAccountFormTest(TestCase):
    """ Test the ``EditAccountForm`` """
    pass
