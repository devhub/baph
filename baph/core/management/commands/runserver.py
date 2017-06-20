from cStringIO import StringIO
import mimetools
#import pyinotify

from django.contrib.staticfiles.management.commands import runserver
from django.core.servers.basehttp import WSGIRequestHandler

from baph.core.management.validation import get_validation_errors
from baph.utils import autoreload


class Message(mimetools.Message):

  def isheader(self, line):
    i = line.find(':')
    if i > 0:
      return line[:i]
    return None

def get_environ(self):
  #print 'read headers:', self.headers.readheaders()

  for k, v in self.headers.items():
    if '_' in k:
      del self.headers[k]

  environ = super(WSGIRequestHandler, self).get_environ()
  environ['RAW_URI'] = self.path
  environ['RAW_HEADER_NAMES'] = self.headers.keys()
  return environ

WSGIRequestHandler.get_environ = get_environ
WSGIRequestHandler.MessageClass = Message

class Command(runserver.Command):

  def validate(self, app=None, display_num_errors=False):
    s = StringIO()
    num_errors = get_validation_errors(s, app)
    if num_errors:
      s.seek(0)
      error_text = s.read()
      raise CommandError("One or more models did not validate:\n%s" % error_text)
    if display_num_errors:
      self.stdout.write("%s error%s found\n" 
        % (num_errors, num_errors != 1 and 's' or ''))

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