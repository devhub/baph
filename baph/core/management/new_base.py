import os
import sys
from argparse import ArgumentParser

from django.core.management import base
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import handle_default_options
from django.utils.six import StringIO


class CommandParser(ArgumentParser):
  """
  Customized ArgumentParser class to improve some error messages and prevent
  SystemExit in several occasions, as SystemExit is unacceptable when a
  command is called programmatically.
  """
  def __init__(self, cmd, **kwargs):
    self.cmd = cmd
    super(CommandParser, self).__init__(**kwargs)

  def parse_args(self, args=None, namespace=None):
    # Catch missing argument for a better error message
    if (hasattr(self.cmd, 'missing_args_message') and
        not (args or any(not arg.startswith('-') for arg in args))):
      self.error(self.cmd.missing_args_message)
    return super(CommandParser, self).parse_args(args, namespace)

  def error(self, message):
    if self.cmd._called_from_command_line:
      super(CommandParser, self).error(message)
    else:
      raise base.CommandError("Error: %s" % message)

class BaseCommand(base.BaseCommand):
  is_subcommand = False

  def create_parser(self, prog_name, subcommand):
    """
    Create and return the ``ArgumentParser`` which will be used to
    parse the arguments to this command.
    """
    parser = CommandParser(
      self, prog="%s %s" % (os.path.basename(prog_name), subcommand),
      description=self.help or None,
    )
    parser.add_argument('--version', action='version',
      version=self.get_version())
    parser.add_argument(
      '-v', '--verbosity', action='store', dest='verbosity', default=1,
      type=int, choices=[0, 1, 2, 3],
      help=(
        'Verbosity level; 0=minimal output, 1=normal output, 2=verbose '
        'output, 3=very verbose output'
      ),
    )
    parser.add_argument(
      '--settings',
      help=(
        'The Python path to a settings module, e.g. '
        '"myproject.settings.main". If this isn\'t provided, the '
        'DJANGO_SETTINGS_MODULE environment variable will be used.'
      ),
    )
    parser.add_argument(
      '--pythonpath',
      help=(
        'A directory to add to the Python path, e.g. '
        '"/home/djangoprojects/myproject".'
      ),
    )
    parser.add_argument('--traceback', action='store_true',
      help='Raise on CommandError exceptions')
    parser.add_argument(
      '--no-color', action='store_true', dest='no_color', default=False,
      help="Don't colorize the command output.",
    )
    self.add_arguments(parser)
    return parser

  def add_arguments(self, parser):
    """
    Entry point for subclassed commands to add custom arguments.
    """
    pass

  def run_from_argv(self, argv):
    """
    Set up any environment changes requested (e.g., Python path
    and Django settings), then run this command. If the
    command raises a ``CommandError``, intercept it and print it sensibly
    to stderr. If the ``--traceback`` option is present or the raised
    ``Exception`` is not ``CommandError``, raise it.
    """
    self._called_from_command_line = True
    parser = self.create_parser(argv[0], argv[1])

    if self.is_subcommand:
      options, args = parser.parse_known_args(argv[2:])
      cmd_options = vars(options)
      # pass unknown args to the subcommand
      args = list(args)
    else:
      options = parser.parse_args(argv[2:])
      cmd_options = vars(options)
      # Move positional args out of options to mimic legacy optparse
      args = cmd_options.pop('args', ())
    base.handle_default_options(options)
    try:
      self.execute(*args, **cmd_options)
    except Exception as e:
      if options.traceback or not isinstance(e, base.CommandError):
        raise

      self.stderr.write('%s: %s' % (e.__class__.__name__, e))
      sys.exit(1)

  def validate(self, app=None, display_num_errors=False):
    """
    Validates the given app, raising CommandError for any errors.

    If app is None, then this will validate all installed apps.
    """
    from baph.core.management.validation import get_validation_errors
    s = StringIO()
    num_errors = get_validation_errors(s, app)
    if num_errors:
      s.seek(0)
      error_text = s.read()
      raise base.CommandError("One or more models did not validate:\n%s" 
        % error_text)
    if display_num_errors:
      self.stdout.write("%s error%s found" 
        % (num_errors, num_errors != 1 and 's' or ''))
