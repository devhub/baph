from django.conf import settings
from django.core.files import storage
from django.utils import timezone


class FileSystemStorage(storage.FileSystemStorage):
  def get_modified_time(self, name):
    dt = self.modified_time(name)
    return _possibly_make_aware(dt)

def _possibly_make_aware(dt):
  """
  Convert a datetime object in the local timezone to aware
  in UTC, if USE_TZ is True.
  """
  # This function is only needed to help with the deprecations above and can
  # be removed in Django 2.0, RemovedInDjango20Warning.
  if settings.USE_TZ:
    tz = timezone.get_default_timezone()
    return timezone.make_aware(dt, tz).astimezone(timezone.utc)
  else:
    return dt
