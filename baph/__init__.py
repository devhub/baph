def setup():
  from baph.apps import apps
  from baph.conf import settings
  from baph.utils.log import configure_logging

  configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)
  apps.populate(settings.INSTALLED_APPS)

def replace_settings_class():
  from django import conf
  from baph.conf import settings
  conf.settings = settings

def apply_patches():
  import os
  from importlib import import_module

  patch_dir = os.path.join(os.path.dirname(__file__), 'patches')
  for mod_name in os.listdir(patch_dir):
    filename = os.path.join(patch_dir, mod_name)
    with open(filename, 'rt') as fp:
      src = fp.read()
    code = compile(src, filename, 'exec')
    mod = import_module(mod_name)
    exec(code, mod.__dict__)

replace_settings_class()
apply_patches()