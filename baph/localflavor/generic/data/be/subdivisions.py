# encoding: utf8
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _


SUBDIVISIONS = ('REGIONS', 'PROVINCES', 'ARRONDISSEMENTS')

REGIONS = (
  ('BRU', _('Brussels Capital Region')),
  ('VLG', _('Flemish Region')),
  ('WAL', _('Wallonia'))
)

PROVINCES = (
  ('VAN', _('Antwerp'), 'VLG'),
  ('BRU', _('Brussels'), 'BRU'),
  ('VOV', _('East Flanders'), 'VLG'),
  ('VBR', _('Flemish Brabant'), 'VLG'),
  ('WHT', _('Hainaut'), 'WAL'),
  ('WLG', _('Liege'), 'WAL'),
  ('VLI', _('Limburg'), 'VLG'),
  ('WLX', _('Luxembourg'), 'WAL'),
  ('WNA', _('Namur'), 'WAL'),
  ('WBR', _('Walloon Brabant'), 'WAL'),
  ('VWV', _('West Flanders'), 'VLG')
)

ARRONDISSEMENTS = (
  ('1', 'Brussels', 'BRU', 'BRU'),
  ('2', 'Antwerp', 'VLG', 'VAN'),
  ('3', 'Mechelen', 'VLG', 'VAN'),
  ('4', 'Turnhout', 'VLG', 'VAN'),
  ('5', 'Hasselt', 'VLG', 'VLI'),
  ('6', 'Maaseik', 'VLG', 'VLI'),
  ('7', 'Tongeren', 'VLG', 'VLI'),
  ('8', 'Aalst', 'VLG', 'VOV'),
  ('9', 'Dendermonde', 'VLG', 'VOV'),
  ('10', 'Eeklo', 'VLG', 'VOV'),
  ('11', 'Ghent', 'VLG', 'VOV'),
  ('12', 'Oudenaarde', 'VLG', 'VOV'),
  ('13', 'Sint-Niklaas', 'VLG', 'VOV'),
  ('14', 'Halle-Vilvoorde', 'VLG', 'VBR'),
  ('15', 'Leuven', 'VLG', 'VBR'),
  ('16', 'Bruges', 'VLG', 'VWV'),
  ('17', 'Diksmuide', 'VLG', 'VWV'),
  ('18', 'Ypres', 'VLG', 'VWV'),
  ('19', 'Kortrijk', 'VLG', 'VWV'),
  ('20', 'Ostend', 'VLG', 'VWV'),
  ('21', 'Roeselare', 'VLG', 'VWV'),
  ('22', 'Tielt', 'VLG', 'VWV'),
  ('23', 'Veurne', 'VLG', 'VWV'),
  ('24', 'Nivelles', 'WAL', 'WBR'),
  ('25', 'Ath', 'WAL', 'WHT'),
  ('26', 'Charleroi', 'WAL', 'WHT'),
  ('27', 'Mons', 'WAL', 'WHT'),
  ('28', 'Mouscron', 'WAL', 'WHT'),
  ('29', 'Soignies', 'WAL', 'WHT'),
  ('30', 'Thuin', 'WAL', 'WHT'),
  ('31', 'Tournai', 'WAL', 'WHT'),
  ('32', 'Huy', 'WAL', 'WLG'),
  ('33', 'Liège', 'WAL', 'WLG'),
  ('34', 'Verviers', 'WAL', 'WLG'),
  ('35', 'Waremme', 'WAL', 'WLG'),
  ('36', 'Arlon', 'WAL', 'WLX'),
  ('37', 'Bastogne', 'WAL', 'WLX'),
  ('38', 'Marche-en-Famenne', 'WAL', 'WLX'),
  ('39', 'Neufchâteau', 'WAL', 'WLX'),
  ('40', 'Virton', 'WAL', 'WLX'),
  ('41', 'Dinant', 'WAL', 'WNA'),
  ('42', 'Namur', 'WAL', 'WNA'),
  ('43', 'Philippeville', 'WAL', 'WNA'),
)
