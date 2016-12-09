from contextlib import contextmanager
import time

from django.core.cache import get_cache
try:
  # django 1.7 - current
  from django.utils.module_loading import import_string
except:
  # django 1.5 - 1.6
  from django.utils.module_loading import import_by_path as import_string


class CacheNamespace(object):
  def __init__(self, name, attr, cache_alias='default', default_value=None,
               default_func=None):
    self.name = name
    self.attr = attr
    self.cache_alias = cache_alias
    self.default_value = default_value
    self.default_func = default_func
    self._caches = None
    self._models = None
    self._partitions = None
    self._override = None

  def __call__(self, value=None):
    value = self.resolve_value(value)
    return self.key_prefix(value)

  def resolve_value(self, value):
    if self._override is not None:
      return self._override
    if value is None:
      value = self.get_default()
    if value is None:
      raise ValueError('CacheNamespace requires a default when called with no '
                       'value')
    return value      

  @contextmanager
  def override_value(self, value):
    self._override = value
    yield self
    self._override = None

  @classmethod
  def get_cache_namespaces(cls):
    """
    Returns a list of CacheNamespace instances that are currently in use
    """
    from django.conf import settings
    namespaces = set()
    for cache, params in settings.CACHES.items():
      prefix = params.get('KEY_PREFIX', None)
      if isinstance(prefix, cls):
        namespaces.add(prefix)
    return namespaces

  @property
  def affected_caches(self):
    """
    Returns a list of caches which use this namespace as KEY_PREFIX
    """
    if self._caches is None:
      from django.conf import settings
      self._caches = []
      for alias, config in settings.CACHES.items():
        prefix = config.get('KEY_PREFIX', None)
        if prefix is self:
          self._caches.append(alias)
    return self._caches

  @property
  def affected_models(self):
    """
    Returns a list of models which are cached in self.affected_caches
    """
    if self._models is None:
      from baph.db.models import get_models
      self._models = []
      for model in get_models():
        cache_alias = model._meta.cache_alias
        if cache_alias not in self.affected_caches:
          continue
        self._models.append(model)
    return self._models

  @property
  def partitions(self):
    """
    Returns a list of available subpartitions that can be invalidated
    """
    if self._partitions is None:
      self._partitions = []
      for model in self.affected_models:
        partitions = model._meta.cache_partitions
        if partitions:
          self._partitions.append( (model, partitions) )
    return self._partitions

  @property
  def cache(self):
    return get_cache(self.cache_alias)

  def get_default(self):
    if self.default_value is not None:
      return self.default_value
    if self.default_func is None:
      return None
    if isinstance(self.default_func, basestring):
      self.default_func = import_string(self.default_func)
    if not callable(self.default_func):
      raise Exception('default_func %r is not callable')
    return self.default_func()

  def version_key(self, value):
    return '%s_%s' % (self.name.lower(), value)

  def key_prefix(self, value):
    version_key = self.version_key(value)
    version = self.cache.get(version_key)
    if version is None:
      version = int(time.time())
      self.cache.set(version_key, version)
    return '%s_%s' % (version_key, version)
