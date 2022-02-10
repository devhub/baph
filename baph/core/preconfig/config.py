from __future__ import absolute_import
import argparse
from functools import partial
import itertools
import os
import sys

from dotenv.main import load_dotenv, dotenv_values

from baph.utils.collections import flatten
from .options import PackageOption, ModuleOption
from .utils import with_empty
from six.moves import map
from six.moves import range


def templatize(key):
  return '{%s}' % key.upper()

def render_tpls(tpls, context):
  rendered = []
  for tpl in tpls:
    try:
      rendered.append(tpl.format(**context))
    except:
      # necessary params not present in context
      pass
  return rendered


class ModuleGenerator(object):
  def __init__(self, bases):
    self.bases = bases
    self.order = [0]

  def apply_prefixes(self, prefixes):
    self.bases = itertools.product(prefixes, self.bases)
    self.order = [0] + [x+1 for x in self.order]

  def apply_suffixes(self, suffixes):
    self.bases = itertools.product(suffixes, self.bases)
    self.order = [x+1 for x in self.order] + [0]

  def normalize(self, combo):
    combo = flatten(combo)
    combo = [combo[i] for i in self.order if combo[i]]
    return '_'.join(combo)

  def __iter__(self):
    for combo in self.bases:
      value = self.normalize(combo)
      if value:
        yield value


class Preconfiguration(object):
  def __init__(self, root, data):
    self.root = root
    self.arg_map = {}
    self.defaults = {}
    self.settings = None
    self.package = data.get('PRECONFIG_PACKAGE')
    self.base = data.get('PRECONFIG_BASE', 'settings')
    self.prefixes = data.get('PRECONFIG_PREFIXES', [])
    self.suffixes = data.get('PRECONFIG_SUFFIXES', [])
    self.load_options(data['PRECONFIG_ARGS'])
    self.settings_actions = data.get('PRECONFIG_ACTIONS', {})
    self.no_init_settings = data.get('PRECONFIG_NO_INIT', False)

  def get_parser(self):
    parser = argparse.ArgumentParser()
    self.add_to_parser(parser)
    return parser

  @property
  def core_settings(self):
    return [opt.name for opt in self.options]

  @property
  def options(self):
    return self.package_options + self.module_options

  @property
  def metavars(self):
    return [opt.metavar for opt in self.options]

  @property
  def context(self):
    return {k: os.environ[k] for k in self.metavars
            if os.environ.get(k)}

  @property
  def all_flags(self):
    flags = set()
    for option in self.options:
      flags.update(option.args)
    return flags

  @property
  def prefix_strings(self):
    return with_empty(self.prefixes)

  @property
  def suffix_strings(self):
    return with_empty(self.suffixes)


  @property
  def package_args(self):
    " returns the names of the package arguments "
    return [opt.name for opt in self.package_options]

  @property
  def package_metavars(self):
    " returns the metavars of the package arguments "
    return [opt.metavar for opt in self.package_options]

  @property
  def package_tpls(self):
    " returns the package name templates "
    packages = [self.package] + list(map(templatize, self.package_args))
    return packages

  @property
  def packages(self):
    " returns the package names "
    context = self.context
    return render_tpls(self.package_tpls, context)


  @property
  def module_args(self):
    " returns the names of the module arguments "
    return [opt.name for opt in self.module_options]

  @property
  def module_metavars(self):
    " returns the metavars of the module arguments "
    return [opt.metavar for opt in self.module_options]

  @property
  def module_variants(self):
    keys = self.module_args
    variants = ['']
    for i in range(len(keys)):
      for j in itertools.combinations(keys, i+1):
        s = '_'.join(map(templatize, j))
        variants.append(s)
    return variants

  @property
  def module_tpls(self):
    gen = ModuleGenerator(['', self.base])
    gen.apply_suffixes(self.module_variants)
    gen.apply_prefixes(self.prefix_strings)
    gen.apply_suffixes(self.suffix_strings)
    return gen

  @property
  def modules(self):
    " returns the module names "
    context = self.context
    return render_tpls(self.module_tpls, context)


  def load_values(self):
    """ get values for preconfig arguments """
    """ priorities are as follows, from highest to lowest:
      - values provided via the command line
      - values already present in os.environ
      - values located in a .env file
      - default values for preconfig args
    """
    values = self.defaults.copy()
    values.update(self.load_values_from_dotenv())
    values.update(self.load_values_from_environ())
    values.update(self.load_values_from_cli())
    return values

  def load_values_from_environ(self):
    " loads config values from os.environ "
    values = {}
    for key in self.metavars:
      if key in os.environ:
        values[key] = os.environ[key]
    return values

  def load_values_from_dotenv(self):
    " loads config values from a .env file, if present "
    path = os.path.join(self.root, '.env')
    if not os.path.exists(path):
      return {}
    values = dotenv_values(path)
    return values

  def load_values_from_cli(self):
    parser = self.get_parser()
    options, args = parser.parse_known_args(sys.argv[1:])
    values = {self.arg_map[k].metavar: self.coerce_cli_value(v)
              for k, v in vars(options).items()}
    return values

  @staticmethod
  def coerce_cli_value(value):
    if str(value).lower() in ('', 'none'):
      return None
    else:
      return value

  def load_options(self, data):
    packages = []
    modules = []
    for name, cfg in data.items():
      metavar = name.upper()
      scope = cfg.pop('scope', 'module')
      if 'default' in cfg:
        self.defaults[metavar] = cfg.pop('default')
      cfg['default'] = argparse.SUPPRESS
      if scope == 'module':
        opt = ModuleOption(name=name, **cfg)
        modules.append(opt)
      elif scope == 'package':
        opt = PackageOption(name=name, **cfg)
        packages.append(opt)
      else:
        raise ValueError('Invalid scope %r (must be "package" or "module")')
      self.arg_map[name] = opt
    self.module_options = sorted(modules, key=lambda x: x.order)
    self.package_options = packages

  def add_to_parser(self, parser):
    from baph.core.management.utils import get_parser_options
    opts = get_parser_options(parser)
    for opt in self.options:
      opt.add_to_parser(parser)

  def populate_env(self):
    values = self.load_values()
    for k, v in values.items():
      if v is None:
        if k in os.environ:
          del os.environ[k]
      else:
        os.environ[k] = v
