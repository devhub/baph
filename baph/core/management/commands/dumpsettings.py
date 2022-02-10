from __future__ import absolute_import
from __future__ import print_function
import json
import pprint

from django.core.management.base import CommandError

from baph.core.management.new_base import BaseCommand


class Command(BaseCommand):
  requires_model_validation = True
  suppress_stdout = True

  def add_arguments(self, parser):
    parser.add_argument('args', metavar='keys', nargs='*',
      help='limits results to only the specified keys')
    parser.add_argument('--scalar', action='store_true',
      dest='scalar', default=False,
      help='returns only the value (no key) for a single setting')
    parser.add_argument('--pprint', action='store_true',
      dest='pprint', default=False,
      help='format results with pprint (response will not be parseable with '
           'javascript\'s JSON.parse')

  def generate_settings(self, keys):
    from django.conf import settings
    all_keys = set(vars(settings._wrapped))
    invalid_keys = set(keys) - all_keys
    if invalid_keys:
      raise CommandError('Invalid keys not found in settings: %s'
        % ', '.join(invalid_keys))
    if not keys:
      keys = all_keys

    _settings = {}
    for key in keys:
      v = getattr(settings, key)
      try:
        output = json.dumps(v)
      except:
        raise CommandError('The value for %r is not JSON-serializable' % key)
      _settings[key] = v
    return _settings

  def handle(self, *keys, **options):
    scalar = options['scalar']
    pretty = options['pprint']
    settings = self.generate_settings(keys)

    if scalar:
      # return the value for a single setting (no key)
      if len(settings) != 1:
        raise CommandError('--scalar can only be used when requesting '
          'a single setting')
      output = json.dumps(list(settings.values()).pop())
    else:
      # return a dict of key/value pairs
      output = json.dumps(settings, sort_keys=True)

    if pretty:
      pprint.pprint(output)
    else:
      print(output)
