from __future__ import absolute_import
from __future__ import print_function
from baph.core.cache.utils import CacheNamespace
from baph.core.management.base import NoArgsCommand
from six.moves import input


def build_options_list(namespaces):
  options = []
  for ns in namespaces:
    name = ns.name
    attrs = [ns.attr]
    options.append((ns, name, attrs, 'ns', ns.affected_models))
    for model, _attrs in ns.partitions:
      name = model.__name__
      for attr in _attrs:
        options.append((ns, name, attrs + [attr], 'partition', [model]))
  return options

def print_options(options):
  print('\n%s  %s %s' % ('id', 'name'.ljust(16), 'attrs'))
  for i, (ns, name, attr, type, models) in enumerate(options):
    names = sorted([model.__name__ for model in models])
    print('%s   %s %s' % (i, name.ljust(16), attr))
    print('    invalidates: %s' % names)

def get_value_for_attr(attr):
  msg = 'Enter the value for %r (ENTER to cancel): ' % attr
  while True:
    value = input(msg).strip()
    if not value:
      return None
    return value

def get_option(options):
  name_map = {opt[1].lower(): i for i, opt in enumerate(options)}
  msg = '\nIncrement which ns key? (ENTER to list, Q to quit): '
  while True:
    value = input(msg).strip().lower()
    if not value:
      print_options(options)
      continue

    if value == 'q':
      # quit
      sys.exit()

    if value.isdigit():
      # integer index
      index = int(value)
    elif value in name_map:
      # string reference
      index = name_map[value]
    else:
      print('Invalid option: %r' % value)
      continue

    if index >= len(options):
      print('Invalid index: %r' % index)
      continue

    return options[index]

def increment_version_key(cache, key):
  version = cache.get(key)
  print('  current value of %s: %s' % (key, version))
  version = version + 1 if version else 1
  cache.set(key, version)
  version = cache.get(key)
  print('  new value of %s: %s' % (key, version))


class Command(NoArgsCommand):
  requires_model_validation = True

  def main(self):
    print_options(self.options)
    option = get_option(self.options)

    ns, name, attrs, type, models = option
    ns_attr = attrs[0]
    partition_attrs = attrs[1:]
    ns_value = get_value_for_attr(ns_attr)
    if ns_value is None:
      return None

    if not partition_attrs:
      # this is a top-level namespace increment
      version_key = ns.version_key(ns_value)
      increment_version_key(ns.cache, version_key)
      return 1

    # this is a partition increment
    values = {}
    for attr in partition_attrs:
      value = get_value_for_attr(attr)
      if value is None:
        return 1
      values[attr] = value

    model = models[0]
    cache = model.get_cache()
    keys = model.get_cache_partition_version_keys(**values)

    # we need to set an override on the cachenamespace instance
    # so it returns the correct value when called by cache.set
    with ns.override_value(ns_value):
      for version_key in keys:
        increment_version_key(cache, version_key)

    return 1

  def handle_noargs(self, **options):
    self.namespaces = CacheNamespace.get_cache_namespaces()
    self.options = build_options_list(self.namespaces)
    
    while True:
      try:
        result = self.main()
      except KeyboardInterrupt:
        print('')
        break
      if result is None:
        break
