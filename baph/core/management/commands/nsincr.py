import sys

from six.moves import input

from baph.core.cache.utils import CacheNamespace
from baph.core.management.new_base import BaseCommand, CommandError


def parse_args(*args):
    """ converts cli args to a dict of options """
    opts = {}
    for arg in args:
        arg = arg.lstrip('-')
        parts = arg.split('=', 1)
        key = parts[0]
        value = parts[1] if len(parts) > 1 else True
        opts[key] = value
    return opts


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


def get_value_for_attr(attr):
    """ prompt the user for an attribute value """
    msg = 'Enter the value for %r (ENTER to cancel): ' % attr
    while True:
        value = input(msg).strip()
        if not value:
            return None
        return value


def print_options(options):
    """ outputs a list of available targets for invalidation """
    print('\n%s    %s %s' % ('id', 'name'.ljust(16), 'attrs'))
    for i, (ns, name, attr, type, models) in enumerate(options):
        names = sorted([model.__name__ for model in models])
        print('%s     %s %s' % (i, name.ljust(16), attr))
        print('        invalidates: %s' % names)


def get_option(options):
    """ prompt the user for which target to invalidate """
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
    old_version = cache.get(key)
    new_version = old_version + 1 if old_version else 1
    cache.set(key, new_version)
    version = cache.get(key)
    return (old_version, version)


class Command(BaseCommand):
    allow_unknown_args = True
    requires_model_validation = True

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput', '--no-input', action='store_false',
            dest='interactive',
            help='Indicates the user should not be prompted for info.',
        )
        parser.add_argument(
            '--namespace', action='store', dest='namespace',
            help='The name of the cache namespace.',
        )

    def get_cli_value(self, key):
        """ get a required value from the cli args """
        if self.values.get(key):
            return self.values[key]
        else:
            raise CommandError('missing required argument "%s"' % key)

    def get_namespace(self):
        """ returns the target namespace information """
        if self.values['interactive']:
            # prompt user for namespace
            print_options(self.options)
            return get_option(self.options)
        else:
            # value provided via cli
            ns = self.get_cli_value('namespace').lower()
            index = self.name_map[ns]
            return self.options[index]

    def get_value_for_attr(self, attr):
        """ get the value for a required attribute """
        if self.values['interactive']:
            # prompt user for value
            return get_value_for_attr(attr)
        else:
            # value provided via cli
            return self.get_cli_value(attr)

    def purge_namespace(self, ns, ns_value):
        """ invalidate everything under a namespace """
        version_key = ns.version_key(ns_value)
        fullkey = ns.cache.make_key(version_key)
        rv = increment_version_key(ns.cache, version_key)
        return [(ns.cache_alias, fullkey, rv[0], rv[1])]

    def purge_partition(self, ns, ns_value, model):
        """ invalidate a target partition within a namespace """
        values = {}
        partition_attrs = model._meta.cache_partitions
        for attr in partition_attrs:
            value = self.get_value_for_attr(attr)
            if value is None:
                return 1
            values[attr] = value
        
        keys = model.get_cache_partition_version_keys(**values)
        cache = model.get_cache()

        # we need to set an override on the cachenamespace instance
        # so it returns the correct value when called by cache.set
        changes = []
        cache_name = model._meta.cache_alias
        with ns.override_value(ns_value):
            for version_key in keys:
                fullkey = cache.make_key(version_key)
                rv = increment_version_key(cache, version_key)
                changes.append((cache_name, fullkey, rv[0], rv[1]))
        return changes

    def main(self):
        option = self.get_namespace()
        ns, name, attrs, type, models = option

        ns_attr = attrs[0]
        ns_value = self.get_value_for_attr(ns_attr)
        if ns_value is None:
            return None

        if type == 'ns':
            changes = self.purge_namespace(ns, ns_value)
        elif type == 'partition':
            changes = self.purge_partition(ns, ns_value, models[0])

        if self.values['interactive']:
            for change in changes:
                print('[%s] %s incremented from %s to %s' % change)
        else:
            return changes

    def run_interactive(self):
        """ prompt user for required invalidation params """
        while True:
            try:
                result = self.main()
            except KeyboardInterrupt:
                print('')
                break
            if result is None:
                break

    def handle(self, *args, **options):
        self.namespaces = CacheNamespace.get_cache_namespaces()
        self.options = build_options_list(self.namespaces)
        self.values = dict(options, **parse_args(*args))
        self.name_map = {opt[1].lower(): i for i, opt in enumerate(self.options)}

        if self.values['interactive']:
            self.run_interactive()
        else:
            result = self.main()
