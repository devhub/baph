from cStringIO import StringIO
import pyinotify

from django.contrib.staticfiles.management.commands import runserver

from baph.core.management.validation import get_validation_errors
from baph.utils import autoreload


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

  def run(self, *args, **options):
    """
    Runs the server, using the autoreloader if needed
    """
    use_reloader = options.get('use_reloader')

    if use_reloader:
      autoreload.main(self.inner_run, args, options)
    else:
      self.inner_run(*args, **options)