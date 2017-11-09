from collections import OrderedDict
from glob import iglob
from importlib import import_module
import os

from django.conf import settings
from django.contrib.staticfiles import finders

from baph.core.files.storage import FileSystemStorage


searched_locations = []

class FileSystemFinder(finders.FileSystemFinder):
  storage_class = FileSystemStorage

  def __init__(self, app_names=None, *args, **kwargs):
    self.locations = []
    self.storages = OrderedDict()
    for root in getattr(settings, 'STATICFILES_DIRS', []):
      if isinstance(root, (list, tuple)):
        prefix, root = root
      else:
        prefix = ''
      for _root in iglob(root):
        if (prefix, _root) not in self.locations:
          self.locations.append((prefix, _root))

    for prefix, root in self.locations:
      filesystem_storage = self.storage_class(location=root)
      filesystem_storage.prefix = prefix
      self.storages[root] = filesystem_storage

  def find(self, path, all=False, allinfo=False):
    if all and allinfo:
      raise ValueError('all and allinfo are incompatible')
    matches = []
    for prefix, root in self.locations:
      if root not in searched_locations:
        searched_locations.append(root)
      matched_path = self.find_location(root, path, prefix)
      if matched_path:
        if not all:
          return matched_path
        matches.append(matched_path)
    return matches

class AppDirectoriesFinder(finders.AppDirectoriesFinder):
  storage_class = FileSystemStorage
  source_dir = 'static'

  def __init__(self, apps=None, *args, **kwargs):
    self.apps = []
    self.storages = OrderedDict()
    if apps is None:
      apps = settings.INSTALLED_APPS
    for app in apps:
      mod = import_module(app)
      mod_path = os.path.dirname(mod.__file__)
      location = os.path.join(mod_path, self.source_dir)
      app_storage = self.storage_class(location)
      if os.path.isdir(app_storage.location):
        self.storages[app] = app_storage
        if app not in self.apps:
          self.apps.append(app)

  def find(self, path, all=False, allinfo=False):
    if all and allinfo:
      raise ValueError('all and allinfo are incompatible')
    matches = []
    for app in self.apps:
      app_location = self.storages[app].location
      if app_location not in searched_locations:
        searched_locations.append(app_location)
      match = self.find_in_app(app, path)
      if match:
        if not all:
          return match
        matches.append(match)
    return matches

  def find_in_app(self, app, path):
    """
    Find a requested static file in an app's static locations.
    """
    storage = self.storages.get(app)
    if storage:
      # only try to find a file if the source dir actually exists
      if storage.exists(path):
        matched_path = storage.path(path)
        if matched_path:
          return matched_path

def find(path, all=False):
  """
  Find a static file with the given path using all enabled finders.
  If ``all`` is ``False`` (default), return the first matching
  absolute path (or ``None`` if no match). Otherwise return a list.
  """
  searched_locations[:] = []
  matches = []
  for finder in finders.get_finders():
    result = finder.find(path, all=all)
    if not all and result:
      return result
    if not isinstance(result, (list, tuple)):
      result = [result]
    for r in result:
      if r not in matches:
        matches.append(r)
  if matches:
    return matches
  # No match.
  return [] if all else None