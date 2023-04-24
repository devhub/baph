# encoding: utf8
from __future__ import unicode_literals

from __future__ import absolute_import
from django.utils.translation import ugettext_lazy as _


SUBDIVISIONS = ('REGIONS',)

GB_COUNTRIES = (
  ('ENG', 'England'),
  ('SCT', 'Scotland'),
  ('WLS', 'Wales'),
)

GB_PROVINCES = (
  ('NIR', 'Northern Ireland'),
)

REGIONS = tuple(sorted(GB_COUNTRIES + GB_PROVINCES,
                key=lambda obj: obj[1]))
