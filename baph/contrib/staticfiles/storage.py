from __future__ import absolute_import
from django.conf import settings
from django.contrib.staticfiles.utils import check_settings
from django.core.exceptions import ImproperlyConfigured

from baph.core.files.storage import FileSystemStorage


class StaticFilesStorage(FileSystemStorage):
  """
  Standard file system storage for static files.
  The defaults for ``location`` and ``base_url`` are
  ``STATIC_ROOT`` and ``STATIC_URL``.
  """
  def __init__(self, location=None, base_url=None, *args, **kwargs):
    if location is None:
      location = settings.STATIC_ROOT
    if base_url is None:
      base_url = settings.STATIC_URL
    check_settings(base_url)
    super(StaticFilesStorage, self).__init__(location, base_url,
                                             *args, **kwargs)
    # FileSystemStorage fallbacks to MEDIA_ROOT when location
    # is empty, so we restore the empty value.
    if not location:
      self.base_location = None
      self.location = None

  def path(self, name):
    if not self.location:
      raise ImproperlyConfigured("You're using the staticfiles app "
                                 "without having set the STATIC_ROOT "
                                 "setting to a filesystem path.")
    return super(StaticFilesStorage, self).path(name)

