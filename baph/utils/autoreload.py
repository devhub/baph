# Autoreloading launcher.
# Borrowed from Peter Hunt and the CherryPy project (http://www.cherrypy.org).
# Some taken from Ian Bicking's Paste (http://pythonpaste.org/).
#
# Portions copyright (c) 2004, CherryPy Team (team@cherrypy.org)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#     * Neither the name of the CherryPy Team nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from collections import OrderedDict
from functools import partial
from itertools import chain, ifilter, ifilterfalse, imap
import os
import signal
import sys
import time
import traceback

from django.conf import settings
from django.core.signals import request_finished

from django.contrib.staticfiles.utils import matches_patterns
from django.utils import six
from django.utils._os import npath
from django.utils.six.moves import _thread as thread
from watchdog.events import PatternMatchingEventHandler, FileSystemEventHandler
from watchdog.observers import Observer


from baph.utils.module_loading import import_string

# This import does nothing, but it's necessary to avoid some race conditions
# in the threading module. See http://code.djangoproject.com/ticket/2330 .
try:
    import threading  # NOQA
except ImportError:
    pass

try:
    import termios
except ImportError:
    termios = None

RUN_RELOADER = True

FILE_MODIFIED = 1
I18N_MODIFIED = 2
STATIC_MODIFIED = 3

_exception = None
_error_files = []
_cached_modules = set()
_cached_filenames = []
_cached_folders = set()
_cached_static_folders = None


class BlockingObserver(Observer):
  last_event = None


  def run(self):
    print 'observer.run'
    pass

  def process_next_event(self):
    print 'process next event:'
    done = False
    while not done:
      print '  not done'
      event, watch = self.event_queue.get(block=True, timeout=None)
      print '  event:', event
      print '  watch:', watch
      event.root = watch.path
      with self._lock:
        # To allow unschedule/stop and safe removal of event handlers
        # within event handlers itself, check if the handler is still
        # registered after every dispatch.
        for handler in list(self._handlers.get(watch, [])):
          print '    ', handler
          if handler in self._handlers.get(watch, []):
            if handler.should_handle(event):
              handler.dispatch(event)
              done = True
      self.event_queue.task_done()


class CodeHandler(FileSystemEventHandler):

  @staticmethod
  def should_handle(event):
    if event.is_directory:
      return event.event_type in ('moved', 'deleted')
    else:
      return event.src_path in _cached_filenames

  def on_any_event(self, event):
    BlockingObserver.last_event = event

class StaticHandler(PatternMatchingEventHandler):
  default_patterns = (
    '**/*.css',
    '**/*.less',
    '**/*.sass',
    '**/*.scss',
    '**/*.coffee',
    '**/*.js',
    '**/*.json',
    '**/*.html',
    '**/*.xml',
    '**/*.jpg',
    '**/*.jpeg',
    '**/*.png',
    '**/*.gif',
  )

  def __init__(self, patterns=None, **kwargs):
    patterns = patterns or self.default_patterns
    super(StaticHandler, self).__init__(patterns, **kwargs)

  @staticmethod
  def should_handle(event):
    if event.is_directory:
      return event.event_type in ('moved', 'deleted', 'created')
    else:
      if event.event_type not in ('created', 'modified'):
        return False
      print event
      print '  root:', event.root
      path = event.src_path.replace(event.root, '').lstrip('/')
      print '  path:', path
      from baph.contrib.staticfiles.finders import find
      match = find(path)
      print '  match:', match

      if match is None:
        # file is not being watched
        return False
      elif match != event.src_path:
        # file is watched, but another file with the same name is
        # overriding it when collectstatic is called
        return False
      else:
        return True

  def on_any_event(self, event):
    BlockingObserver.last_event = event

def get_static_folders():
  global _cached_static_folders
  if _cached_static_folders is None:
    from django.contrib.staticfiles.finders import get_finders
    folders = {}
    for finder in get_finders():
      for storage in finder.storages.values():
        if storage.location not in folders:
          folders[storage.location] = storage
    _cached_static_folders = folders
  return _cached_static_folders

def get_storage_for_root(root):
  print 'get storage for root:', root
  folders = get_static_folders()
  return folders[root]

def gen_filenames(only_new=False, folders=False):
    """
    Returns a list of filenames referenced in sys.modules and translation
    files.
    """
    # N.B. ``list(...)`` is needed, because this runs in parallel with
    # application code which might be mutating ``sys.modules``, and this will
    # fail with RuntimeError: cannot mutate dictionary while iterating
    global _cached_modules, _cached_filenames, _cached_folders
    module_values = set(sys.modules.values())
    _cached_filenames = clean_files(_cached_filenames)
    if _cached_modules == module_values:
        # No changes in module list, short-circuit the function
        print 'no changes, not reloading'
        if only_new:
            return []
        else:
            return _cached_filenames + clean_files(_error_files)

    new_modules = module_values - _cached_modules
    new_filenames = clean_files(
        [filename.__file__ for filename in new_modules
         if hasattr(filename, '__file__')])
    
    if not _cached_filenames and settings.USE_I18N:
        # Add the names of the .mo files that can be generated
        # by compilemessages management command to the list of files watched.
        basedirs = [os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                 'conf', 'locale'),
                    'locale']
        #for app_config in reversed(list(apps.get_app_configs())):
        #    basedirs.append(os.path.join(npath(app_config.path), 'locale'))
        basedirs.extend(settings.LOCALE_PATHS)
        basedirs = [os.path.abspath(basedir) for basedir in basedirs
                    if os.path.isdir(basedir)]
        for basedir in basedirs:
            for dirpath, dirnames, locale_filenames in os.walk(basedir):
                for filename in locale_filenames:
                    if filename.endswith('.mo'):
                        new_filenames.append(os.path.join(dirpath, filename))

    new_folders = set(map(os.path.dirname, new_filenames))
    new_folders.discard('')

    _cached_modules = _cached_modules.union(new_modules)
    _cached_filenames += new_filenames
    _cached_folders = _cached_folders.union(new_folders)
    if only_new:
      if folders:
        return new_folders
      else:
        return new_filenames + clean_files(_error_files)
    else:
      if only_new:
        return _cached_folders
      else:
        return _cached_filenames + clean_files(_error_files)

def clean_files(filelist):
  filenames = []
  for filename in filelist:
    if not filename:
      continue
    if filename.endswith(".pyc") or filename.endswith(".pyo"):
      filename = filename[:-1]
    if filename.endswith("$py.class"):
      filename = filename[:-9] + ".py"
    if os.path.exists(filename):
      filenames.append(filename)
  return filenames

def reset_translations():
  import gettext
  from django.utils.translation import trans_real
  gettext._translations = {}
  trans_real._translations = {}
  trans_real._default = None
  trans_real._active = threading.local()

def get_modified_code(path):
  """
  Returns the appropriate code for a modified file based on extension
  """
  _, ext = os.path.splitext(path)
  if ext == '.mo':
    return I18N_MODIFIED
  elif ext in ('.py',):
    return FILE_MODIFIED
  else:
    return STATIC_MODIFIED

def watchdog_file_changed():
  print 'watchdog file changed:'
  observer = BlockingObserver(timeout=None)

  code_handler = CodeHandler()

  def update_watch(sender=None, **kwargs):
    if sender and getattr(sender, 'handles_files', False):
      # No need to update watches when request serves files.
      # (sender is supposed to be a django.core.handlers.BaseHandler subclass)
      return
    for path in gen_filenames(only_new=True, folders=True):
      observer.schedule(code_handler, path)

  # New modules may get imported when a request is processed.
  request_finished.connect(update_watch)

  # add the static files handler
  
  static_handler = StaticHandler()
  for path in get_static_folders():
    watch = observer.schedule(static_handler, path, recursive=True)
    
  # Block until an event happens.
  update_watch()
  print 'observer.start'
  observer.start()
  observer.process_next_event()
  observer.stop()
  print 'observer.stop'
  observer.join()
  print 'observer.join'


  # If we are here the code must have changed.
  event = BlockingObserver.last_event
  return (get_modified_code(event.src_path), event.src_path)

def collect_static():
  from baph.core.management import call_command
  options = {
    'interactive': False,
    'no_color': True,
    'link': False,
    'clear': False,
    'dry_run': False,
    'ignore_patterns': [],
    'use_default_ignore_patterns': True,
    'post_process': False,
    'verbosity': 0,
  }
  call_command('collectstatic', **options)

def reloader_thread():
  print 'reloader thread:'
  ensure_echo_on()
  fn = watchdog_file_changed
  while RUN_RELOADER:
    print 'change monitor start'
    change = fn()
    print 'change:', change
    if isinstance(change, tuple):
      # fn() returned (code, path)
      change, filename = change

    if change == FILE_MODIFIED:
      sys.exit(3)  # force reload
    elif change == I18N_MODIFIED:
      reset_translations()
    elif change == STATIC_MODIFIED:
      collect_static()
    time.sleep(1)
  print 'reloader end'

def restart_with_reloader():
  print 'restart with reloader:'
  while True:
    print '  restart tick'
    args = [sys.executable] + ['-W%s' % o for o in sys.warnoptions] + sys.argv
    if sys.platform == "win32":
      args = ['"%s"' % arg for arg in args]
    new_environ = os.environ.copy()
    new_environ["RUN_MAIN"] = 'true'
    exit_code = os.spawnve(os.P_WAIT, sys.executable, args, new_environ)
    if exit_code != 3:
      return exit_code

def python_reloader(main_func, args, kwargs):
  print 'python reloader:'
  if os.environ.get("RUN_MAIN") == "true":
    print 'main is true'
    thread.start_new_thread(main_func, args, kwargs)
    try:
      reloader_thread()
    except KeyboardInterrupt:
      pass
  else:
    print 'main is false'
    try:
      exit_code = restart_with_reloader()
      if exit_code < 0:
        os.kill(os.getpid(), -exit_code)
      else:
        sys.exit(exit_code)
    except KeyboardInterrupt:
      pass

def jython_reloader(main_func, args, kwargs):
  from _systemrestart import SystemRestart
  thread.start_new_thread(main_func, args)
  while True:
    if code_changed():
      raise SystemRestart
    time.sleep(1)

def main(main_func, args=None, kwargs=None):
  if args is None:
    args = ()
  if kwargs is None:
    kwargs = {}
  if sys.platform.startswith('java'):
    reloader = jython_reloader
  else:
    reloader = python_reloader

  wrapped_main_func = check_errors(main_func)
  reloader(wrapped_main_func, args, kwargs)

def check_errors(fn):
  def wrapper(*args, **kwargs):
    global _exception
    try:
      fn(*args, **kwargs)
    except Exception:
      _exception = sys.exc_info()

      et, ev, tb = _exception

      if getattr(ev, 'filename', None) is None:
        # get the filename from the last item in the stack
        filename = traceback.extract_tb(tb)[-1][0]
      else:
        filename = ev.filename

      if filename not in _error_files:
        _error_files.append(filename)

      raise

  return wrapper

def raise_last_exception():
  global _exception
  if _exception is not None:
    six.reraise(*_exception)

def ensure_echo_on():
  if termios:
    fd = sys.stdin
    if fd.isatty():
      attr_list = termios.tcgetattr(fd)
      if not attr_list[3] & termios.ECHO:
        attr_list[3] |= termios.ECHO
        if hasattr(signal, 'SIGTTOU'):
          old_handler = signal.signal(signal.SIGTTOU, signal.SIG_IGN)
        else:
          old_handler = None
        termios.tcsetattr(fd, termios.TCSANOW, attr_list)
        if old_handler is not None:
          signal.signal(signal.SIGTTOU, old_handler)

# old stuff below, might want to refer to it later

def get_static_files():
  handlers = getattr(settings, 'WATCHLIST_HANDLERS', {})
  excludes = getattr(settings, 'WATCHLIST_EXCLUDES', [])
  excludes = [os.path.join(settings.PROJECT_ROOT, ex) for ex in excludes]
  include = partial(matches_patterns, patterns=handlers.keys())
  exclude = partial(matches_patterns, patterns=excludes)

  def fullpath(entry):
    """ converts (filename, storage) tuples into full paths """
    return os.path.join(entry[1].location, entry[0])    

  def finder_files(finder):
    files = imap(fullpath, finder.list([]))
    files = ifilter(include, files)
    files = ifilterfalse(exclude, files)
    return files
  from django.contrib.staticfiles.finders import get_finders
  return chain(*imap(finder_files, get_finders()))

def get_handlers(filename):
  """
  Returns applicable handlers for a given filename
  """
  print 'get_handlers for %s' % filename
  handlers = getattr(settings, 'WATCHLIST_HANDLERS', {})

  # build the list of handlers, and track ordering in relation to
  # other handlers
  items = {}
  for key in handlers.keys():
    if matches_patterns(filename, [key]):
      group = handlers[key]
      for i in range(len(group)):
        handler = group[i]
        if handler not in items:
          items[handler] = {
            'comes_before': set(),
            'comes_after': set(),
          }
        items[handler]['comes_after'].update(group[:i])
        items[handler]['comes_before'].update(group[i+1:])

  # reorder the handlers so all individual ordering rules are maintained
  handlers = []
  while True:
    if not items:
      break
    remaining = len(items)
    for handler in items.keys():
      comes_before = items[handler]['comes_before']
      comes_after = items[handler]['comes_after']
      conflicts = comes_before & comes_after
      if conflicts:
        raise Exception('Error while processing handler %r: The following '
                        'handlers come both before AND after the target '
                        'handler: %s' % (handler, ', '.join(conflicts)))

      if comes_after & set(handlers) == comes_after:
        handlers.append(handler)
        del items[handler]
        continue
    if len(items) == remaining:
      # no items were processed, maybe an ordering issue?
      raise Exception('could not determine absolute ordering for handlers')
  return imap(import_string, handlers)

def run_handlers(filename):
  """
  Runs handlers based on the filename of the modified file
  """
  print '\nrun_handlers:', filename
  handlers = get_handlers(filename)
  for handler in handlers:
    print '  handler:', handler
    handler(filename)