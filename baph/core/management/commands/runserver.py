from cStringIO import StringIO
import mimetools

from django.contrib.staticfiles.management.commands import runserver
from django.core.servers.basehttp import WSGIRequestHandler
from django.utils import autoreload

from baph.core.management.new_base import BaseCommand
from baph.core.management.validation import get_validation_errors


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
  def inner_run(self, *args, **kwargs):
    autoreload.raise_last_exception()
    super(BaseCommand, self).inner_run(*args, **kwargs)
