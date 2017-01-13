from django.core.urlresolvers import RegexURLResolver


def get_resolver(urlconf=None):
  if urlconf is None:
    from django.conf import settings
    urlconf = settings.ROOT_URLCONF
  return RegexURLResolver(r'^/', urlconf)
