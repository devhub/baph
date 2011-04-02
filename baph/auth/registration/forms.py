# -*- coding: utf-8 -*-
'''
:mod:`baph.auth.registration.forms` -- Registration-related Forms
=================================================================

Forms and validation code for user registration.
'''

from baph.auth.models import User
from baph.db.orm import ORM
from baph.utils.importing import import_any_module
dforms = import_any_module(['django.forms'])
from django.utils.translation import ugettext_lazy as _
forms = import_any_module(['registration.forms'])

Checkbox = dforms.CheckboxInput
orm = ORM.get()
TERMS_ERROR_MSG = _(u'You must agree to the terms to register')
TERMS_LABEL = _(u'I have read and agree to the Terms of Service')


class RegistrationForm(forms.RegistrationForm):
    '''An SQLAlchemy-based version of django-registration's
    ``RegistrationForm``.
    '''

    def clean_username(self):
        '''Validate that the username is alphanumeric and is not already in
        use.
        '''
        session = orm.sessionmaker()
        user_ct = session.query(User) \
                         .filter_by(username=self.cleaned_data['username']) \
                         .count()
        if user_ct == 0:
            return self.cleaned_data['username']
        else:
            raise dforms.ValidationError(_(u'''\
A user with that username already exists.'''))


class RegistrationFormTermsOfService(RegistrationForm):
    '''Subclass of :class:`RegistrationForm` which adds a required checkbox
    for agreeing to a site's Terms of Service.
    '''
    tos = dforms.BooleanField(widget=Checkbox(attrs=forms.attrs_dict),
                              label=TERMS_LABEL,
                              error_messages={'required': TERMS_ERROR_MSG})


class RegistrationFormUniqueEmail(RegistrationForm):
    '''Subclass of :class:`RegistrationForm`, which enforces uniqueness of
    email addresses.
    '''
    def clean_email(self):
        '''Validate that the supplied email address is unique for the site.'''
        session = orm.sessionmaker()
        user_ct = session.query(User) \
                         .filter_by(email=self.cleaned_data['email']) \
                         .count()
        if user_ct == 0:
            return self.cleaned_data['email']
        else:
            raise dforms.ValidationError(_(u'''\
This email address is already in use. Please supply a different email
address.'''.replace('\n', ' ')))


class RegistrationFormNoFreeEmail(RegistrationForm):
    '''Subclass of :class:`RegistrationForm` which disallows registration with
    email addresses from popular free webmail services; moderately useful for
    preventing automated spam registrations.

    To change the list of banned domains, subclass this form and
    override the attribute ``bad_domains``.
    '''
    bad_domains = ['aim.com', 'aol.com', 'email.com', 'gmail.com',
                   'googlemail.com', 'hotmail.com', 'hushmail.com',
                   'msn.com', 'mail.ru', 'mailinator.com', 'live.com',
                   'yahoo.com']

    def clean_email(self):
        '''Check the supplied email address against a list of known free
        webmail domains.
        '''
        email_domain = self.cleaned_data['email'].split('@')[1]
        if email_domain in self.bad_domains:
            raise dforms.ValidationError(_(u'''\
Registration using free email addresses is prohibited. Please supply a
different email address.'''.replace('\n', ' ')))
        return self.cleaned_data['email']
