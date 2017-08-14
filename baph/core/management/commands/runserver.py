from cStringIO import StringIO
import mimetools
#import pyinotify

from django.contrib.staticfiles.management.commands import runserver
from django.core.servers.basehttp import WSGIRequestHandler

from baph.core.management.new_base import BaseCommand
from baph.core.management.validation import get_validation_errors
from baph.utils import autoreload


class Message(mimetools.Message):

  def __init__(self, *args, **kwargs):
    self.raw_header_names = set()
    mimetools.Message.__init__(self, *args, **kwargs)

  def isheader(self, line):
    i = line.find(':')
    if i > 0:
      self.raw_header_names.add(line[:i])
      return line[:i].lower()
    return None

def get_environ(self):
  for k, v in self.headers.items():
    if '_' in k:
      del self.headers[k]

  environ = super(WSGIRequestHandler, self).get_environ()
  environ['RAW_URI'] = self.path
  environ['RAW_HEADER_NAMES'] = self.headers.raw_header_names
  return environ

WSGIRequestHandler.get_environ = get_environ
WSGIRequestHandler.MessageClass = Message


class Command(BaseCommand, runserver.Command):
  pass

  '''
  def run(self, *args, **options):
    """
    Runs the server, using the autoreloader if needed
    """
    use_reloader = options.get('use_reloader')

    if use_reloader:
      autoreload.main(self.inner_run, args, options)
    else:
      self.inner_run(*args, **options)
  '''