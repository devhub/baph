def setup():
  from baph.apps import apps
  from baph.conf import settings
  from baph.utils.log import configure_logging

  configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)

  #apps.populate(settings.INSTALLED_APPS)

def replace_settings_class():
  from django import conf
  from baph.conf import settings
  conf.settings = settings

replace_settings_class()