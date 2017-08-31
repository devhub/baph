import argparse
import imp
import inspect
import itertools
import os
import sys


PRECONFIG_MODULE_NAME = 'preconfig'
CONFIG_FOLDERS = ('', 'config', 'conf')

class BaseOption(object):
  def __init__(self, name, args, default=None, choices=None, required=False):
    self.name = name
    self.args = args
    self.default = default
    self.choices = choices
    self.required = required

  @property
  def metavar(self):
    return self.name.upper()

  @property
  def arg_params(self):
    args = self.args
    kwargs = {
      'metavar': self.metavar,
      'dest': self.name,
      'default': self.default,
      'choices': self.choices,
      'required': self.required,
    }
    return (args, kwargs)

class ModuleOption(BaseOption):
  def __init__(self, order=None, **kwargs):
    super(ModuleOption, self).__init__(**kwargs)
    self.order = order or self.name

class PackageOption(BaseOption):
  def __init__(self, base='settings', prefix=None, **kwargs):
    super(PackageOption, self).__init__(**kwargs)
    self.base = base
    self.prefix = prefix

class Preconfigurator(object):
  cache = {}

  def __init__(self):
    self.cmd = os.path.abspath(inspect.stack()[-1][1])
    self.cmd_dir = os.path.dirname(self.cmd)
    self.preconfig_dir = self.find_preconfig_folder(self.cmd_dir)
    if not self.preconfig_dir:
      raise Exception('No preconfiguration folder could be determined')
    if self.preconfig_dir not in self.cache:
      self.cache[self.preconfig_dir] = self.load(self.preconfig_dir)
    self.packages, self.modules = self.cache[self.preconfig_dir]

  @staticmethod
  def get_parent_paths(path):
    # returns all parent folders of the given path
    frags = path.rstrip('/').split('/')
    for i in range(len(frags), 1, -1):
      yield '/'.join(frags[:i])

  @classmethod
  def find_preconfig_folder(cls, path):
    # locates the folder containing the preconfiguration file
    paths = cls.get_parent_paths(path)
    folders = CONFIG_FOLDERS
    filename = '%s.py' % PRECONFIG_MODULE_NAME
    for args in itertools.product(paths, folders):
      folder = os.path.join(*args)
      fullpath = os.path.join(folder, filename)
      if os.path.exists(fullpath):
        return folder

  def load(self, folder):
    modinfo = imp.find_module(PRECONFIG_MODULE_NAME, [folder])
    module = imp.load_module(PRECONFIG_MODULE_NAME, *modinfo)
    args = module.PRECONFIG_ARGS

    modules = []
    packages = []
    for name, data in args.items():
      scope = data.pop('scope', 'module')
      if scope == 'module':
        opt = ModuleOption(name=name, **data)
        modules.append(opt)
      elif scope == 'package':
        opt = PackageOption(name=name, **data)
        packages.append(opt)
      else:
        raise Exception('invalid scope "%s" (must be "package" or "module")'
          % scope)

    modules = sorted(modules, key=lambda x: x.order)
    return (packages, modules)

  @property
  def core_settings(self):
    return self.module_settings + self.package_settings

  @property
  def arg_map(self):
    # maps short names to option instances
    return {opt.name: opt for opt in self.modules + self.packages}

  @property
  def module_settings(self):
    return [opt.name for opt in self.modules]

  @property
  def package_settings(self):
    return [opt.name for opt in self.packages]

  def get_settings_variants(self, keys):
    filenames = []
    for i in range(len(keys)):
      for j in itertools.combinations(keys, i+1):
        s = '_'.join('{%s}' % name for name in j)
        filenames.append(s)
    return filenames

  @property
  def settings_variants(self):
    return self.get_settings_variants(self.module_settings)

  def add_arguments(self, parser):
    for opt in self.modules + self.packages:
      args, kwargs = opt.arg_params
      parser.add_argument(*args, **kwargs)

  def set_environment_var(self, key, value):
    " os.environ values must be strings "
    if value is None:
      value = ''
    elif not isinstance(value, basestring):
      value = str(value)
    os.environ[key] = value

  def process_cmd_args(self, argv):
    " removes preconf args from sys.argv and loads them into the environment "
    parser = argparse.ArgumentParser()
    self.add_arguments(parser)
    args, cmd_args = parser.parse_known_args(argv)
    for key, value in vars(args).items():
      option = self.arg_map[key]
      self.set_environment_var(option.metavar, value)
    return cmd_args