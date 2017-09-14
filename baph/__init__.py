def setup():
  print 'setup'
  from baph.apps import apps
  from baph.conf import settings

  apps.populate(settings.INSTALLED_APPS)
