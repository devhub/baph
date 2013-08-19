# -*- coding: utf-8 -*-
from coffin.shortcuts import render_to_string
from django import forms
from django.contrib.auth.forms import SetPasswordForm as BaseSetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import int_to_base36
from django.utils.translation import ugettext_lazy as _
from .models import orm, UNUSABLE_PASSWORD, User


class PasswordResetForm(forms.Form):
    email = forms.EmailField(label=_('E-mail'), max_length=75)

    def clean_email(self):
        '''Validates that a user exists with the given e-mail address.'''
        email = self.cleaned_data['email']
        session = orm.sessionmaker()
        users = session.query(User) \
                       .filter_by(email=email)
        if users.count() == 0:
            raise forms.ValidationError(_(u'''\
That e-mail address doesn't have an associated user account. Are you sure
you've registered?'''))
        self.users_cache = users.filter(User.password != UNUSABLE_PASSWORD) \
                                .all()
        if len(self.users_cache) == 0:
            raise forms.ValidationError(_(u'''\
That e-mail address doesn't allow the password to be set.'''))
        return email

    def save(self, domain_override=None,
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             request=None):
        '''Generates a one-use only link for resetting password and sends to
        the user.
        '''
        from django.core.mail import send_mail
        for user in self.users_cache:
            if not domain_override:
                # TODO: implement this
                raise Exception('not implemented')
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            c = {
                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': int_to_base36(user.id.int),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': use_https and 'https' or 'http',
            }
            body = render_to_string(email_template_name, c)
            send_mail(_("Password reset on %s") % site_name,
                      body, None, [user.email])


class SetPasswordForm(BaseSetPasswordForm):
    '''A form that lets a user change set his/her password without entering
    the old password.
    '''

    def __init__(self, user, *args, **kwargs):
        self.user = user
        self.session = kwargs.pop('session', orm.sessionmaker())
        super(SetPasswordForm, self).__init__(user, *args, **kwargs)

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.session.commit()
        return self.user
