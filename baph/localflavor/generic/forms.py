# -*- coding: utf-8 -*-
'''\
:mod:`baph.localflavor.generic.forms` -- Custom Generic "Local Flavor" Fields
=============================================================================

The generic subpackage defines a :class:`CountryField` and a
:class:`LanguageField` that you can use in your form models. They render as a
Drop Down and uses the ISO-3166 code.

Adapted from:
http://code.djangoproject.com/ticket/5446/

Attachment: country_and_language_fields_trunk.4.patch
'''

from baph.utils.importing import import_any_module, import_attr
from django.conf import settings
forms = import_any_module(['django.forms'])
from django.utils.encoding import force_unicode
from django.utils.html import escape, conditional_escape
from django.utils.translation import ugettext_lazy as _
from itertools import chain

COUNTRY_PROVINCES = [u'ar', u'ca', u'es', u'nl', u'za']
COUNTRY_STATES = [u'at', u'au', u'br', u'ch', u'de', u'in_', u'mx', u'us']


def _get_country_divisions(country, div_type):
    country_code = country.strip(u'_')
    module = 'django.contrib.localflavor.%s.%s_%ss' % \
             (country, country_code, div_type)
    attr = '%s_CHOICES' % div_type.upper()
    return (country_code.upper(), import_attr([module], attr))

STATE_PROVINCE_CHOICES = \
    tuple(sorted(chain([_get_country_divisions(country, 'province')
                        for country in COUNTRY_PROVINCES],
                       [_get_country_divisions(country, 'state')
                        for country in COUNTRY_STATES])))


class CountryField(forms.ChoiceField):
    '''A country field, an uppercase two-letter ISO 3166-1 standard country
    code. Countries are defined in
    :const:`baph.localflavor.generic.COUNTRIES`.

    See also: `Country Code List`_.

    .. _`Country Code List`: http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
    '''

    widget = forms.Select(attrs={
        'class': 'localflavor-generic-country',
    })

    def __init__(self, *args, **kwargs):
        from . import COUNTRIES

        kwargs.setdefault('choices', COUNTRIES)

        super(CountryField, self).__init__(*args, **kwargs)


class LanguageField(forms.ChoiceField):
    '''A language code. Generally you would check languages against
    :setting:`LANGUAGES`.
    '''
    def __init__(self, *args, **kwargs):

        kwargs.setdefault('choices', settings.LANGUAGES)

        super(LanguageField, self).__init__(*args, **kwargs)


class StateProvinceSelect(forms.Select):
    '''Special-cased select widget for states/provinces.'''

    class Media:
        js = ('localflavor/generic/js/stateprovince.js',)

    def render_options(self, choices, selected_choices):
        '''Overrides Select.render_options() and adds country-specific classes
        to the options.
        '''

        def render_option(country, value, label):
            value = force_unicode(value)
            if value in selected_choices:
                selected_html = u' selected="selected"'
            else:
                selected_html = u''
            return u'<option class="country-%s" value="%s"%s>%s</option>' % (
                country.lower(), escape(value), selected_html,
                conditional_escape(force_unicode(label)))
        # Normalize to strings.
        selected_choices = set([force_unicode(v) for v in selected_choices])
        output = []
        for country, options in chain(self.choices, choices):
            for value, label in options:
                output.append(render_option(country, value, label))
        return u'\n'.join(output)


class StateProvinceField(forms.ChoiceField):
    '''Selects a state/province of a given country. Requires the
    :class:`CountryField` field in the same form. By default, this field is
    not required, because there are countries without political divisions.
    '''

    widget = StateProvinceSelect(attrs={
        'class': 'localflavor-generic-stateprovince',
    })

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('choices', STATE_PROVINCE_CHOICES)
        kwargs.setdefault('required', False)

        super(StateProvinceField, self).__init__(*args, **kwargs)

    def check_value(self, division, country):
        '''Checks the value of the field to make sure that the state/province
        is part of the specified country. Call this method in the ``clean*()``
        method of your form.

        :param division: The state/province value to check.
        :param country: The country code to check with the state/province
                        value.
        '''
        countries_with_divisions = dict(self.choices)
        msg = _(u'Select a state which corresponds to the country selected.')
        if country in countries_with_divisions:
            choices = countries_with_divisions[country]
            if division in [c for c, d in choices]:
                return division
            else:
                raise forms.ValidationError(msg)
        else:
            return u''
