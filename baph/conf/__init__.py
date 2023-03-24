from __future__ import absolute_import
import ast
from contextlib import contextmanager
import imp
import importlib
import logging
import os
import pkgutil
import sys

from chainmap import ChainMap
from django.conf import global_settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import LazyObject, empty

from baph.core.preconfig.loader import PreconfigLoader
import six


ENVIRONMENT_VARIABLE = "DJANGO_SETTINGS_MODULE"
NOT_SET = object()
DEFAULT_ACTIONS = {'*': 'set'}
TUPLE_SETTINGS = (
  "INSTALLED_APPS",
  "TEMPLATE_DIRS",
  "LOCALE_PATHS",
)

#formatter = logging.Formatter(fmt='%(message)s')
#handler = logging.StreamHandler()
#handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
#logger.setLevel(logging.INFO)
#logger.addHandler(handler)

@contextmanager
def local_path():
  orig = sys.path
  sys.path = []
  if 'PROJECT_ROOT' in os.environ:
    sys.path.append(os.environ['PROJECT_ROOT'])
  yield
  sys.path = orig

class SettingsMeta(type):
  def __new__(cls, name, bases, attrs):
    # overwrite __module__ so django translation utils will
    # check the correct location for translation files
    attrs['__module__'] = 'django.conf'
    return super(SettingsMeta, cls).__new__(cls, name, bases, attrs)

class LazySettings(six.with_metaclass(SettingsMeta, LazyObject)):
  def _setup(self, name=None):
    settings_module = os.environ.get(ENVIRONMENT_VARIABLE)
    if not settings_module:
      desc = ("setting %s" % name) if name else "settings"
      raise ImproperlyConfigured(
        "Requested %s, but settings are not configured. "
        "You must either define the environment variable %s "
        "or call settings.configure() before accessing settings."
        % (desc, ENVIRONMENT_VARIABLE))
    self._wrapped = Settings(settings_module)

  def __repr__(self):
    # Hardcode the class name as otherwise it yields 'Settings'.
    if self._wrapped is empty:
      return '<LazySettings [Unevaluated]>'
    return '<LazySettings "%(settings_module)s">' % {
      'settings_module': self._wrapped.SETTINGS_MODULE,
    }

  def __getattr__(self, name):
    """Return the value of a setting and cache it in self.__dict__."""
    if self._wrapped is empty:
        self._setup(name)
    val = getattr(self._wrapped, name)
    self.__dict__[name] = val
    return val

  def __setattr__(self, name, value):
    """
    Set the value of setting. Clear all cached values if _wrapped changes
    (@override_settings does this) or clear single values when set.
    """
    if name == '_wrapped':
      self.__dict__.clear()
    else:
      self.__dict__.pop(name, None)
    super(LazySettings, self).__setattr__(name, value)

  def __delattr__(self, name):
    """Delete a setting and clear it from cache if needed."""
    super(LazySettings, self).__delattr__(name)
    self.__dict__.pop(name, None)

  def configure(self, default_settings=global_settings, **options):
    """
    Called to manually configure the settings. The 'default_settings'
    parameter sets where to retrieve any unspecified values from (its
    argument must support attribute access (__getattr__)).
    """
    if self._wrapped is not empty:
      raise RuntimeError('Settings already configured.')
    holder = UserSettingsHolder(default_settings)
    for name, value in options.items():
      setattr(holder, name, value)
    self._wrapped = holder

  @property
  def configured(self):
    """
    Returns True if the settings have already been configured.
    """
    return self._wrapped is not empty

class Settings:
  actions = ('SET', 'APPEND', 'PREPEND', 'UPDATE', 'REPLACE')

  def set(self, key, value):
    " sets a value for a setting. raises an exception if already present "
    if key in self._explicit_settings:
      raise Exception('Setting %r is already set' % key)
    setattr(self, key, value)

  def prepend(self, key, value):
    " prepends the given values to the existing values "
    current = getattr(self, key, NOT_SET)
    if current is not NOT_SET:
      value = value + current
    setattr(self, key, value)

  def append(self, key, value):
    " appends the given values to the existing values "
    current = getattr(self, key, NOT_SET)
    if current is not NOT_SET:
      value = current + value
    setattr(self, key, value)

  def update(self, key, value):
    " updates a mapping with new values "
    current = getattr(self, key, NOT_SET)
    if current is not NOT_SET:
      current.update(value)
      value = current
    setattr(self, key, value)

  def replace(self, key, value):
    " replaces an existing value. if not present, sets the value "
    setattr(self, key, value)

  def get_action(self, key):
    " returns the appropriate action to use when processing the setting "
    if key in self.actions:
      return self.actions[key]
    else:
      return self.actions['*']


  def load_settings_module(self, module, explicit=True):
    msg = '  %s' % module.__name__
    actions = getattr(module, 'actions', {})
    self.actions = self.actions.new_child(actions)
    for setting in dir(module):
      if setting.isupper():
        setting_value = getattr(module, setting)
        self.apply_setting(setting, setting_value, explicit)
    self.actions = self.actions.parents
    logger.info(msg.ljust(64) + 'SUCCESS')

  def set_core_settings(self, **settings):
    logger.info('Setting core settings from preconfiguration')
    for k, v in settings.items():
      logger.info('  %s %s' % (k.ljust(32), v))
      self.apply_setting(k, v)
      self.locked.add(k)

  def apply_setting(self, key, value, explicit=True):
    pieces = key.rsplit('__', 1)
    if len(pieces) == 2 and pieces[-1] in self.actions:
      key, action = pieces
    else:
      action = self.get_action(key)

    if key in self.locked:
      return
      #raise Exception('Setting %r is locked' % key)
    if (key in TUPLE_SETTINGS and not isinstance(value, (list, tuple))):
      raise ImproperlyConfigured(
        "The %s setting must be a list or a tuple. " % key)

    func = getattr(self, action.lower())
    func(key, value)

    if explicit:
      self._explicit_settings.add(key)

  def get_package_path(self, package):
    if package not in self.package_paths:
      loader = pkgutil.find_loader(package)
      if not loader:
        return None
      if not loader.is_package(package):
        raise ValueError('%r is not a package' % package)
      fullpath = loader.get_filename()
      path, filename = fullpath.rsplit('/', 1)
      self.package_paths[package] = path
    return self.package_paths[package]

  @staticmethod
  def create_module(fullname, **kwargs):
    """
    create a new module and install it into sys.modules, then return it
    """
    module = imp.new_module(fullname)
    for k, v in kwargs.items():
      setattr(module, k, v)
    sys.modules[fullname] = module
    return module

  @staticmethod
  def compile_module(module):
    path = module.__file__
    with open(path, 'rb') as fp:
      content = fp.read()
    node = ast.parse(content, path)
    code = compile(node, path, 'exec')
    exec(code, module.__dict__)

  def load_module_settings(self, module_name):
    msg = '  %s' % module_name
    package, mod = module_name.rsplit('.', 1)
    path = self.get_package_path(package)
    module_path = '%s/%s.py' % (path, mod)
    if not os.path.exists(module_path):
      logger.debug(msg.ljust(64) + 'NOT FOUND')
      return
    
    if module_name not in sys.modules:
      kwargs = {
        '__file__': module_path,
      }
      module = self.create_module(module_name, **kwargs)
      try:
        self.compile_module(module)
      except Exception as e:
        logger.error(msg.ljust(64) + 'ERROR')
        raise
    else:
      module = sys.modules[module_name]

    self.load_settings_module(module)

  def load_package_settings(self, package):
    msg = 'loading settings from package: %s' % package
    path = self.get_package_path(package)
    if not path:
      status = 'NOT FOUND'
    else:
      status = 'FOUND'
    logger.info(msg.ljust(64) + status)
    if not path:
      return

    if self.preconfig.no_init_settings:
      # to prevent running the code in __init__.py, we create a module
      # and install it in the required location
      kwargs = {
        '__file__': '%s/__init__.py' % path,
        '__path__': [path],
      }
      module = self.create_module(package, **kwargs)

    for mod in self.preconfig.modules:
      module = '%s.%s' % (package, mod)
      self.load_module_settings(module)

  def load_dynamic_settings(self):
    " loads settings from modules with name permutations generated using "
    " a preconfiguration file "
    for pkg in self.preconfig.packages:
      self.load_package_settings(pkg)

  def load_static_settings(self):
    " loads settings from the module provided by the --settings CLI arg "
    mod = importlib.import_module(self.SETTINGS_MODULE)
    self.load_settings_module(mod)

  def load_global_settings(self):
    " loads global settings "
    logger.info('Loading global settings')
    self.load_settings_module(global_settings, explicit=False)

  def load_local_settings(self):
    " loads local settings "
    logger.info('Loading local settings')
    with local_path():
      try:
        import settings as local_settings
        self.load_settings_module(local_settings)
      except:
        pass

  def __init__(self, settings_module):
    mode = 'dynamic' if settings_module == '__dynamic__' else 'static'
    logger.info('\n*** Initializing Settings (%s mode) ***' % mode)

    # store the settings module in case someone later cares
    self.SETTINGS_MODULE = settings_module

    self.messages = []
    self.locked = set()
    self._explicit_settings = set()
    self.package_paths = {}

    if mode == 'dynamic':
      self.preconfig = PreconfigLoader.load()
      if not self.preconfig:
        raise Exception('Dynamic settings require a preconfig file')
      self.actions = ChainMap(self.preconfig.settings_actions, DEFAULT_ACTIONS)
      self.set_core_settings(**self.preconfig.context)
    else:
      self.actions = ChainMap(DEFAULT_ACTIONS)

    self.load_global_settings()
    if mode == 'dynamic':
      self.load_dynamic_settings()
    else:
      self.load_static_settings()
    self.load_local_settings()

    if not self.SECRET_KEY:
      raise ImproperlyConfigured("The SECRET_KEY setting must not be empty.")

    '''
    if hasattr(time, 'tzset') and self.TIME_ZONE:
      # When we can, attempt to validate the timezone. If we can't find
      # this file, no check happens and it's harmless.
      zoneinfo_root = '/usr/share/zoneinfo'
      if (os.path.exists(zoneinfo_root) and not
          os.path.exists(os.path.join(zoneinfo_root, *(self.TIME_ZONE.split('/'))))):
        raise ValueError("Incorrect timezone setting: %s" % self.TIME_ZONE)
      # Move the time zone info into os.environ. See ticket #2315 for why
      # we don't do this unconditionally (breaks Windows).
      os.environ['TZ'] = self.TIME_ZONE
      time.tzset()
    '''

  def is_overridden(self, setting):
    return setting in self._explicit_settings

  def __repr__(self):
    return '<%(cls)s "%(settings_module)s">' % {
      'cls': self.__class__.__name__,
      'settings_module': self.SETTINGS_MODULE,
    }

class UserSettingsHolder:
  """Holder for user configured settings."""
  # SETTINGS_MODULE doesn't make much sense in the manually configured
  # (standalone) case.
  SETTINGS_MODULE = None

  def __init__(self, default_settings):
    """
    Requests for configuration variables not in this class are satisfied
    from the module specified in default_settings (if possible).
    """
    self.__dict__['_deleted'] = set()
    self.default_settings = default_settings

  def __getattr__(self, name):
    if name in self._deleted:
      raise AttributeError
    return getattr(self.default_settings, name)

  def __setattr__(self, name, value):
    self._deleted.discard(name)
    '''
    if name == 'DEFAULT_CONTENT_TYPE':
      warnings.warn('The DEFAULT_CONTENT_TYPE setting is deprecated.', RemovedInDjango30Warning)
    '''
    super().__setattr__(name, value)

  def __delattr__(self, name):
    self._deleted.add(name)
    if hasattr(self, name):
      super().__delattr__(name)

  def __dir__(self):
    return sorted(
      s for s in list(self.__dict__) + dir(self.default_settings)
      if s not in self._deleted
    )

  def is_overridden(self, setting):
    deleted = (setting in self._deleted)
    set_locally = (setting in self.__dict__)
    set_on_default = getattr(self.default_settings, 'is_overridden', lambda s: False)(setting)
    return deleted or set_locally or set_on_default

  def __repr__(self):
    return '<%(cls)s>' % {
      'cls': self.__class__.__name__,
    }

settings = LazySettings()