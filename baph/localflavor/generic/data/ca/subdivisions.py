# encoding: utf8
from __future__ import unicode_literals

from __future__ import absolute_import
from django.utils.translation import ugettext_lazy as _


SUBDIVISIONS = ('PROVINCES',)

CA_PROVINCES = (
  ('AB', _('Alberta')),
  ('BC', _('British Columbia')),
  ('MB', _('Manitoba')),
  ('NB', _('New Brunswick')),
  ('NL', _('Newfoundland and Labrador')),
  ('NS', _('Nova Scotia')),
  ('ON', _('Ontario')),
  ('PE', _('Prince Edward Island')),
  ('QC', _('Quebec')),
  ('SK', _('Saskatchewan')),
)

CA_TERRITORIES = (
  ('NT', _('Northwest Territories')),
  ('NU', _('Nunavut')),
  ('YT', _('Yukon'))
)

PROVINCES = tuple(sorted(CA_PROVINCES + CA_TERRITORIES,
                  key=lambda obj: obj[1]))