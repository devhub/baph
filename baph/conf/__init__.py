import imp
import importlib
import itertools
import os
import pkgutil
import sys
import time
import warnings

from baph.conf import global_settings
from baph.conf.preconfigure import Preconfigurator
from baph.core.exceptions import ImproperlyConfigured
from django.utils.functional import LazyObject, empty, cached_property
from baph.utils.termcolors import make_style


GLOBAL_SETTINGS = 'baph.conf.global_settings'
ENVIRONMENT_VARIABLE = "DJANGO_SETTINGS_MODULE"
APPEND_SETTINGS = (
  'TEMPLATE_CONTEXT_PROCESSORS',
  'MIDDLEWARE_CLASSES',
  'JINJA2_FILTERS',
)
PREPEND_SETTINGS = (
  'INSTALLED_APPS',
  'TEMPLATE_DIRS',
)
TUPLE_SETTINGS = (
  "INSTALLED_APPS",
  "TEMPLATE_DIRS",
  "LOCALE_PATHS",
)

success_msg = make_style(fg='green')
notice_msg = make_style(fg='yellow')
error_msg = make_style(fg='red')
info_msg = make_style(fg='blue')

class LazySettings(LazyObject):
  """
  A lazy proxy for either global Django settings or a custom settings object.
  The user can manually configure settings prior to using them. Otherwise,
  Django uses the settings module pointed to by DJANGO_SETTINGS_MODULE.
  """
  def _setup(self, name=None):
    """
    Load the settings module pointed to by the environment variable. This
    is used the first time we need any settings at all, if the user has not
    previously configured the settings manually.
    """
    print 'yay'
    settings_module = os.environ.get(ENVIRONMENT_VARIABLE)
    print 'settings_module:', settings_module
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
    if self._wrapped is empty:
      self._setup(name)
    return getattr(self._wrapped, name)

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

class BaseSettings(object):
  """
  Common logic for settings whether set by a module or by the user.
  """
  def __setattr__(self, name, value):
    if name in ("MEDIA_URL", "STATIC_URL") and value \
            and not value.endswith('/'):
      raise ImproperlyConfigured("If set, %s must end with a slash"
            % name)
    object.__setattr__(self, name, value)

class Settings(BaseSettings):

  def __init__(self, settings_module):
    print 'Settings.__init__:', settings_module
    # store the settings module in case someone later cares
    self.SETTINGS_MODULE = settings_module
    self.preconfig = Preconfigurator()
    self._explicit_settings = set()
    self.sources = {}
    self.messages = []
    self.process_environment_vars()

    self.load_settings(GLOBAL_SETTINGS)
    self.load_settings(settings_module, expand=True)
    for opt in self.preconfig.packages:
      setting = opt.name
      value = getattr(self, setting, None)
      if value:
        self.load_package_settings(value, base=opt.base, prefix=opt.prefix)

    if not self.SECRET_KEY:
      raise ImproperlyConfigured("The SECRET_KEY setting must not be empty.")

    if hasattr(time, 'tzset') and self.TIME_ZONE:
      # When we can, attempt to validate the timezone. If we can't find
      # this file, no check happens and it's harmless.
      zoneinfo_root = '/usr/share/zoneinfo'
      if (os.path.exists(zoneinfo_root) and not
          os.path.exists(os.path.join(zoneinfo_root,
            *(self.TIME_ZONE.split('/'))))):
        raise ValueError("Incorrect timezone setting: %s" % self.TIME_ZONE)
      # Move the time zone info into os.environ. See ticket #2315 for why
      # we don't do this unconditionally (breaks Windows).
      os.environ['TZ'] = self.TIME_ZONE
      time.tzset()

  def __repr__(self):
    return '<%(cls)s "%(settings_module)s">' % {
      'cls': self.__class__.__name__,
      'settings_module': self.SETTINGS_MODULE,
    }

  def load_settings(self, module, expand=False):
    loader = pkgutil.get_loader(module)
    if loader and loader.is_package(module):
      # import all defined settings files in a package
      self.load_package_settings(module)
    elif expand:
      # import all defined settings files based off a main file
      self.load_expanded_module_settings(module)
    else:
      # import a single settings file
      self.load_single_module_settings(module)

  def load_package_settings(self, package, base='settings', prefix=None):
    """
    Attempts to load each module from SETTINGS_MODULES from the given package
    """
    print info_msg('\n*** Loading settings from %s ***' % package)
    modules = self.settings_files(base, prefix=prefix, suffixes=['_local'])
    modules = map('.'.join, itertools.product([package], modules))
    for mod in modules:
      self.load_module_settings(mod)

  def load_expanded_module_settings(self, module):
    """
    Loads settings files based off permutations of a base filename
    """
    print info_msg('\n*** Loading settings from %s ***' % module)
    modules = self.settings_files(module, prefix=module, suffixes=['_local'])
    for mod in modules:
      self.load_module_settings(mod)

  def load_single_module_settings(self, module):
    """
    Loads settings from a single module
    """
    print info_msg('\n*** Loading settings from %s ***' % module)
    self.load_module_settings(module)

  def load_module_settings(self, module):
    """
    Loads settings from a module
    """
    msg = ('loading %s' % module).ljust(64)
    e = None

    try:
      if module in sys.modules:
        mod = sys.modules[module]
      else:
        mod = importlib.import_module(module)
      self.merge_settings(mod)
      msg += success_msg('LOADED')
    except ImportError:
      msg += notice_msg('NOT FOUND')
    except Exception as e:
      msg += error_msg('FAILED')
    print msg
    self.flush_messages()
    if e:
      raise e

  def is_overridden(self, setting):
    return setting in self._explicit_settings

  def settings_files(self, base, prefix=None, suffixes=None):
    keys = [key for key in self.preconfig.module_settings
            if getattr(self, key, None)]
    ctx = {key: getattr(self, key) for key in keys}

    filenames = [base]
    for filename in self.preconfig.get_settings_variants(keys):
      if prefix:
        filename = '_'.join([prefix, filename])
      filenames.append(filename)

    filenames = [filename.format(**ctx) for filename in filenames]
    if suffixes is not None:
      filenames = itertools.product(filenames, [''] + list(suffixes))
      filenames = map(''.join, filenames)
    return filenames

  def add_message(self, msg):
    """
    Pushes a message onto the stack.
    """
    self.messages.append(msg)

  def flush_messages(self):
    """
    Flushes accumulated messages to the screen
    """
    while self.messages:
      print(self.messages.pop(0))

  def set_setting(self, setting, value, source):
    """
    Handles the setting and overriding of settings
    """
    if setting in self.preconfig.core_settings:
      # special handling for core vars
      if hasattr(self, setting):
        # warn on overriding of existing values
        previous = getattr(self, setting)
        #if previous:
        #  warnings.warn('Overwriting value for %s (previous value of %r '
        #    'declared in %s. New value is %r' 
        #    % (setting, previous, self.sources[setting], value))
      # track where this came from so we can display the source
      self.sources[setting] = source
      self.add_message('    %s set to %s' % (setting, value))

    if (setting in TUPLE_SETTINGS and
            not isinstance(value, (list, tuple))):
      raise ImproperlyConfigured(
        "The %s setting must be a list or a tuple. " % setting)

    if not hasattr(self, setting):
      # first occurence - set the current value as-is
      pass
    elif setting in APPEND_SETTINGS:
      # append the value to the existing value
      value = getattr(self, setting) + value
    elif setting in PREPEND_SETTINGS:
      # prepent the value to the existing value
      value = value + getattr(self, setting)
    else:
      # override the existing value
      pass

    setattr(self, setting, value)
    if source != GLOBAL_SETTINGS:
      self._explicit_settings.add(setting)

  def process_environment_vars(self):
    print info_msg('\n*** Initializing settings environment ***')
    for setting in self.preconfig.core_settings:
      if os.environ.get(setting, None):
        # found a valid value in the environment, save to settings
        setting_value = os.environ[setting]
        self.set_setting(setting, setting_value, 'os.environ')
    
    # ensure required params were set in manage.py/wsgi.py
    '''
    for setting in self.preconfig.module_settings:
      if not getattr(self, setting, None):
        sys.tracebacklimit = 0 # no traceback needed for this error
        raise ImproperlyConfigured(
          'setting "%s" not found in environment' % setting)
    '''

    self.flush_messages()

  def merge_settings(self, mod):
    """
    Merges specified module's settings into current settings
    """
    for setting in dir(mod):
      if setting != setting.upper():
        # ignore anything that isn't uppercase
        continue
      setting_value = getattr(mod, setting)
      self.set_setting(setting, setting_value, mod.__name__)



class UserSettingsHolder(BaseSettings):
  """
  Holder for user configured settings.
  """
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
    super(UserSettingsHolder, self).__setattr__(name, value)

  def __delattr__(self, name):
    self._deleted.add(name)
    if hasattr(self, name):
      super(UserSettingsHolder, self).__delattr__(name)

  def __dir__(self):
    return list(self.__dict__) + dir(self.default_settings)

  def is_overridden(self, setting):
    deleted = (setting in self._deleted)
    set_locally = (setting in self.__dict__)
    set_on_default = getattr(self.default_settings, 'is_overridden', lambda s: False)(setting)
    return (deleted or set_locally or set_on_default)

  def __repr__(self):
    return '<%(cls)s>' % {
      'cls': self.__class__.__name__,
    }

settings = LazySettings()
