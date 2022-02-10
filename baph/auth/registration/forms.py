# -*- coding: utf-8 -*-
'''
:mod:`baph.auth.registration.forms` -- Registration-related Forms
=================================================================

Forms and validation code for user registration.
'''
from __future__ import absolute_import
from hashlib import sha1 as sha_constructor
import random

from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _
from sqlalchemy.orm import joinedload

from baph.auth.models import User, Organization
from baph.auth.registration import settings
from baph.auth.registration.managers import SignupManager
from baph.auth.utils import generate_sha1
from baph.db.orm import ORM
import six


orm = ORM.get()

attrs_dict = {'class': 'required'}


def identification_field_factory(label, error_required):
    """
    A simple identification field factory which enable you to set the label.

    :param label:
        String containing the label for this field.

    :param error_required:
        String containing the error message if the field is left empty.

    """
    return forms.CharField(label=label,
                           widget=forms.TextInput(attrs=attrs_dict),
                           max_length=75,
                           error_messages={'required': _("%(error)s") % {'error': error_required}})

class AuthenticationForm(forms.Form):
    """
    A custom form where the identification can be a e-mail address or username.

    """
    identification = identification_field_factory(_(u"Email or username"),
                       _(u"Either supply us with your email or username."))
    password = forms.CharField(label=_("Password"),
          widget=forms.PasswordInput(attrs=attrs_dict, render_value=False))
    remember_me = forms.BooleanField(widget=forms.CheckboxInput(),
                                     required=False,
                                     label=_(u'Remember me for %(days)s') \
               % {'days': _(settings.BAPH_REMEMBER_ME_DAYS[0])})

    def __init__(self, *args, **kwargs):
        """ A custom init because we need to change the label if no usernames is used """
        super(AuthenticationForm, self).__init__(*args, **kwargs)
        # Dirty hack, somehow the label doesn't get translated without declaring
        # it again here.
        self.fields['remember_me'].label = _(u'Remember me for %(days)s') \
            % {'days': _(settings.BAPH_REMEMBER_ME_DAYS[0])}
        if settings.BAPH_AUTH_WITHOUT_USERNAMES:
            self.fields['identification'] = identification_field_factory(
                _(u"Email"),
                _(u"Please supply your email."))

    def clean(self):
        """
        Checks for the identification and password.

        If the combination can't be found will raise an invalid sign in error.

        """
        identification = self.cleaned_data.get('identification')
        password = self.cleaned_data.get('password')

        if identification and password:
            user = authenticate(identification=identification, password=password)
            if user is None:
                raise forms.ValidationError(_(u"Please enter a correct "
                    "username or email and password. Note that both fields "
                    "are case-sensitive."))
        return self.cleaned_data

class SignupForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        base_form = User.get_form_class()
        if not base_form:
            raise Exception('no form_class found in User.Meta')
        if not settings.BAPH_AUTH_WITHOUT_USERNAMES:
            field_name = User.USERNAME_FIELD
            self.fields[field_name] = base_form.base_fields[field_name]
        for field_name in User.REQUIRED_FIELDS:
            self.fields[field_name] = base_form.base_fields[field_name]
        for field_name in ['password1', 'password2']:
            label = 'Create password' if field_name == 'password1' \
                else 'Repeat Password'
            self.fields[field_name] = forms.CharField(
                widget=forms.PasswordInput(attrs=attrs_dict,
                    render_value=False),
                label=_(label))

    def clean_username(self):
        username = User.USERNAME_FIELD
        filters = {username: self.cleaned_data[username]}
        if settings.BAPH_AUTH_UNIQUE_WITHIN_ORG:
            org_key = Organization._meta.model_name + '_id'
            filters[org_key] = Organization.get_current_id()

        session = orm.sessionmaker()
        user = session.query(User) \
            .options(joinedload('signup')) \
            .filter_by(**filters) \
            .first()
        if user and user.signup and user.signup.activation_key != settings.BAPH_ACTIVATED:
            raise forms.ValidationError(_('This username is already taken but '
                'not yet confirmed. Please check your email for verification '
                'steps.'))
        if user:
            raise forms.ValidationError(_('This username is already taken'))
        return self.cleaned_data[username]

    def clean_email(self):
        filters = {'email': self.cleaned_data['email']}
        if settings.BAPH_AUTH_UNIQUE_WITHIN_ORG:
            org_key = Organization._meta.model_name + '_id'
            filters[org_key] = Organization.get_current_id()

        session = orm.sessionmaker()
        user = session.query(User) \
            .options(joinedload('signup')) \
            .filter_by(**filters) \
            .first()
        if user and user.signup and user.signup.activation_key != settings.BAPH_ACTIVATED:
            raise forms.ValidationError(_('This email is already taken but '
                'not yet confirmed. Please check your email for verification '
                'steps.'))
        if user:
            raise forms.ValidationError(_('This email is already taken'))
        return self.cleaned_data['email']

    def clean(self):
        # check that passwords match
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_('The two password fields didn\'t match.'))
        # check uniqueness of constraints
        return self.cleaned_data

    def save(self):
        """ Creates a new user and account. Returns the newly created user. """
        username, email, password = (self.cleaned_data[User.USERNAME_FIELD],
                                     self.cleaned_data['email'],
                                     self.cleaned_data['password1'])
        extra_kwargs = dict(i for i in self.cleaned_data.items() if i[0] not in
                       [User.USERNAME_FIELD, 'email', 'password1', 'password2'])

        new_user = SignupManager.create_user(username,
                                             email,
                                             password,
                                             not settings.BAPH_ACTIVATION_REQUIRED,
                                             settings.BAPH_ACTIVATION_REQUIRED,
                                             **extra_kwargs)
        return new_user


class SignupFormOnlyEmail(SignupForm):
    """
    Form for creating a new user account but not needing a username.

    This form is an adaptation of :class:`SignupForm`. It's used when
    ``USERENA_WITHOUT_USERNAME`` setting is set to ``True``. And thus the user
    is not asked to supply an username, but one is generated for them. The user
    can than keep sign in by using their email.

    """
    def __init__(self, *args, **kwargs):
        super(SignupFormOnlyEmail, self).__init__(*args, **kwargs)
        if 'username' in self.fields:
            del self.fields['username']

    def save(self):
        """ Generate a random username before falling back to parent signup form """
        session = orm.sessionmaker()
        while True:
            username = six.text_type(sha_constructor(str(random.random())).hexdigest()[:5])
            user = session.query(User).filter(User.username==username).first()
            if not user:
                break

        self.cleaned_data['username'] = username
        return super(SignupFormOnlyEmail, self).save()

class ChangeEmailForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
                                                               maxlength=75)),
                             label=_(u"New email"))

    def __init__(self, user, *args, **kwargs):
        """
        The current ``user`` is needed for initialisation of this form so
        that we can check if the email address is still free and not always
        returning ``True`` for this query because it's the users own e-mail
        address.

        """
        super(ChangeEmailForm, self).__init__(*args, **kwargs)
        if not isinstance(user, User):
            raise TypeError("user must be an instance of %s" % User._meta.model_name)
        else: self.user = user

    def clean_email(self):
        """ Validate that the email is not already in use """
        if self.cleaned_data['email'].lower() == self.user.email:
            raise forms.ValidationError(_(u'You\'re already known under this '
                'email.'))
        
        filters = {'email': self.cleaned_data['email']}
        if settings.BAPH_AUTH_UNIQUE_WITHIN_ORG:
            org_key = Organization._meta.model_name + '_id'
            filters[org_key] = Organization.get_current_id()

        session = orm.sessionmaker()
        user = session.query(User) \
            .filter(User.email != self.user.email) \
            .filter_by(**filters) \
            .first()
        if user:
            raise forms.ValidationError(_(u'This email is already in use. '
                'Please supply a different email.'))
        return self.cleaned_data['email']

    def save(self):
        """
        Save method calls :func:`user.change_email()` method which sends out an
        email with an verification key to verify and with it enable this new
        email address.

        """
        return self.user.signup.change_email(self.cleaned_data['email'])
