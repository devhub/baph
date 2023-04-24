# -*- coding: utf-8 -*-

from __future__ import absolute_import
from baph.localflavor.generic import COUNTRIES
from baph.localflavor.generic.forms import (
    CountryField, LanguageField, StateProvinceField, StateProvinceSelect,
    STATE_PROVINCE_CHOICES)
from baph.test.base import BaseTestCase
from django import forms
from django.conf import settings


class TestCountryForm(forms.Form):
    country = CountryField()
    default = CountryField(initial='PT')


class TestLanguageForm(forms.Form):
    language = LanguageField()


class TestStateProvinceForm(forms.Form):
    country = CountryField()
    division = StateProvinceField(required=False)

    def clean_division(self):
        field = self.fields['division']
        return field.check_value(self.cleaned_data['division'],
                                 self.cleaned_data['country'])


class LocalFlavorGenericTestCase(BaseTestCase):
    '''Tests the :mod:`baph.localflavor.generic` package.'''

    def test_country_field(self):
        form = TestCountryForm()
        field = form.fields['country']
        self.assertIsInstance(field.widget, forms.Select)
        self.assertSequenceEqual(field.choices, COUNTRIES)
        field = form.fields['default']
        self.assertEqual(field.clean(field.initial), 'PT')

        form = TestCountryForm({'country': None})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['country'], [u'This field is required.'])

    def test_language_field(self):
        form = TestLanguageForm()
        field = form.fields['language']
        self.assertIsInstance(field.widget, forms.Select)
        self.assertSequenceEqual(field.choices, settings.LANGUAGES)

    def test_stateprovince_field(self):
        form = TestStateProvinceForm()
        field = form.fields['division']
        self.assertIsInstance(field.widget, StateProvinceSelect)
        self.assertSequenceEqual(field.choices, STATE_PROVINCE_CHOICES)

        form = TestStateProvinceForm({'country': 'ZZ'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['division'], u'')

        form = TestStateProvinceForm({
            'country': 'US',
            'division': 'WA',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['division'], u'WA')

        form = TestStateProvinceForm({
            'country': 'US',
            'division': 'YUC',  # in MX
        })
        self.assertFalse(form.is_valid())
        error_msg = u'''\
Select a state which corresponds to the country selected.'''
        self.assertEqual(form.errors['division'], [error_msg])
