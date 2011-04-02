# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import ugettext_lazy as _


class TwitterRegistrationForm(forms.Form):
    '''Finalizes the Twitter registration.'''

    oauth_token = forms.CharField(widget=forms.HiddenInput)
    oauth_verifier = forms.CharField(widget=forms.HiddenInput)
    given_name = forms.CharField(label=_(u'First (Given) Name'))
    family_name = forms.CharField(label=_(u'Last (Family) Name'))
    email = forms.EmailField(label=_(u'Email Address'))
