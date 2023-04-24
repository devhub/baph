from __future__ import absolute_import
import unittest

from django import forms

from baph.localflavor.generic.forms import (CountryField,
    CountryCodeField, StateProvinceField, StateProvinceCodeField)


class TestForm(forms.Form):
    country = CountryCodeField()
    subdivision = StateProvinceCodeField(required=False)

class LocalflavorFormTest(unittest.TestCase):

    def test_country_code_field(self):
        data = {'country': 'US'}
        form = TestForm(data)
        self.assertTrue(form.is_valid())
        data2 = form.cleaned_data
        self.assertEqual(data2['country'], data['country'])

    def test_country_code_field_invalid(self):
        data = {'country': 'DERP'}
        form = TestForm(data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['country'],
            [u'Select a valid choice. DERP is not one of the available '
                'choices.'])

    def test_localflavor_subdivision_code_field(self):
        data = {
            'country': 'US',
            'subdivision': 'WA',
        }
        form = TestForm(data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['country'], data['country'])
        self.assertEqual(form.cleaned_data['subdivision'], data['subdivision'])

    def test_localflavor_subdivision_code_field_invalid(self):
        data = {
            'country': 'US',
            'subdivision': '98',
        }
        form = TestForm(data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['subdivision'],
            [u'Select a valid choice. 98 is not one of the available choices.'])

    def test_generic_subdivision_code_field(self):
        data = {
            'country': 'DO',
            'subdivision': '32',
        }
        form = TestForm(data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['country'], data['country'])
        self.assertEqual(form.cleaned_data['subdivision'], data['subdivision'])

    def test_generic_subdivision_code_field_invalid(self):
        data = {
            'country': 'DO',
            'subdivision': 'ZZ',
        }
        form = TestForm(data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['subdivision'],
            [u'Select a valid choice. ZZ is not one of the available choices.'])
