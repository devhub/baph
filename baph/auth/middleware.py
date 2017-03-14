from django.utils.functional import SimpleLazyObject

from . import get_user as _get_user


def get_user(request):
  if not hasattr(request, '_cached_user'):
    request._cached_user = _get_user(request)
  return request._cached_user

def set_lazy_user(request):
  request.user = SimpleLazyObject(lambda: get_user(request))

class AuthenticationMiddleware(object):
  def process_request(self, request):
    assert hasattr(request, 'session'), '''\
The Django authentication middleware requires session middleware to be
installed. Edit your MIDDLEWARE_CLASSES setting to insert
"django.contrib.sessions.middleware.SessionMiddleware".'''
    set_lazy_user(request)

