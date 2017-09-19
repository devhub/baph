import threading
from collections import Counter, OrderedDict, defaultdict

from baph.utils import lru_cache

from .config import AppConfig


class Apps(object):
  def __init__(self, installed_apps=()):
    self.all_models = defaultdict(OrderedDict)
    self.app_configs = OrderedDict()
    self.stored_app_configs = []
    self.apps_ready = self.models_ready = self.ready = False
    self._lock = threading.Lock()

    if installed_apps is not None:
      self.populate(installed_apps)

  def populate(self, installed_apps=None):
    if self.ready:
      return

    with self._lock:
      if self.ready:
        return

      # app_config should be pristine, otherwise the code below won't
      # guarantee that the order matches the order in INSTALLED_APPS.
      if self.app_configs:
        raise RuntimeError("populate() isn't reentrant")

      # Load app configs and app modules.
      for entry in installed_apps:
        if isinstance(entry, AppConfig):
          app_config = entry
        else:
          app_config = AppConfig.create(entry)
        if app_config.label in self.app_configs:
          raise RuntimeError(
            "Application labels aren't unique, "
            "duplicates: %s" % app_config.label)

        self.app_configs[app_config.label] = app_config

      # Check for duplicate app names.
      counts = Counter(
        app_config.name for app_config in self.app_configs.values())
      duplicates = [
        name for name, count in counts.most_common() if count > 1]
      if duplicates:
        raise RuntimeError(
          "Application names aren't unique, "
          "duplicates: %s" % ", ".join(duplicates))

      self.apps_ready = True

      # Load models.
      for app_config in self.app_configs.values():
        all_models = self.all_models[app_config.label]
        app_config.import_models(all_models)

      self.clear_cache()
      self.models_ready = True

      for app_config in self.get_app_configs():
        app_config.ready()

      self.ready = True

  def check_apps_ready(self):
    """
    Raises an exception if all apps haven't been imported yet.
    """
    if not self.apps_ready:
      raise AppRegistryNotReady("Apps aren't loaded yet.")

  def get_app_configs(self):
    """
    Imports applications and returns an iterable of app configs.
    """
    self.check_apps_ready()
    return self.app_configs.values()

  @lru_cache.lru_cache(maxsize=None)
  def get_models(self, include_auto_created=False,
                 include_deferred=False, include_swapped=False):
    """
    Returns a list of all installed models.
    By default, the following models aren't included:
    - auto-created models for many-to-many relations without
      an explicit intermediate table,
    - models created to satisfy deferred attribute queries,
    - models that have been swapped out.
    Set the corresponding keyword argument to True to include such models.
    """
    self.check_models_ready()

    result = []
    for app_config in self.app_configs.values():
      result.extend(list(app_config.get_models(
        include_auto_created, include_deferred, include_swapped)))
    return result

  def clear_cache(self):
    """
    Clears all internal caches, for methods that alter the app registry.
    This is mostly used in tests.
    """
    # Call expire cache on each model. This will purge
    # the relation tree and the fields cache.
    self.get_models.cache_clear()
    if self.ready:
      # Circumvent self.get_models() to prevent that the cache is refilled.
      # This particularly prevents that an empty value is cached while cloning.
      for app_config in self.app_configs.values():
        for model in app_config.get_models(include_auto_created=True):
          model._meta._expire_cache()

apps = Apps(installed_apps=None)