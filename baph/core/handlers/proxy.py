from __future__ import absolute_import
from django.core.urlresolvers import set_urlconf, RegexURLPattern

from baph.utils.module_loading import import_string

from .base import BaseHandler
from .utils import get_resolver


def get_proxy_resolver(urlconf, default_view):
  from django.conf import settings
  set_urlconf(urlconf)
  resolver = get_resolver(urlconf)
  callback = import_string(default_view)
  if callback not in resolver.reverse_dict:
    pattern = RegexURLPattern(r'', callback)
    resolver.url_patterns.append(pattern)
  return resolver

class ProxyHandler(BaseHandler):
  middleware_setting_key = 'PROXY_MIDDLEWARE'
  urlconf_setting_key = 'PROXY_URLCONF'

  def __init__(self, *args, **kwargs):
    super(ProxyHandler, self).__init__(*args, **kwargs)
    self.load_middleware()

  def get_resolver(self, urlconf=None):
    """
    Loads the urlresolver with the given urlconf, then appends the default
    proxy view as a catchall at the end of the pattern list
    """
    if urlconf is None:
      from django.conf import settings
      urlconf = getattr(settings, self.urlconf_setting_key)
    callback_name = settings.PROXY_DEFAULT_VIEW
    return get_proxy_resolver(urlconf, callback_name)

proxy_handler = ProxyHandler()