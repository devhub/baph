import inspect
import os
import sys
from argparse import ArgumentParser
from operator import attrgetter

from django.core.management import base
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import handle_default_options
from django.utils.six import StringIO

#from baph.conf.preconfigure import Preconfigurator
from baph.core.preconfig.loader import PreconfigLoader
from .base import CommandError


LEGACY_OPT_KWARGS = ('nargs', 'help', 'action', 'dest', 'default',
                     'metavar', 'type', 'choices', 'const')
LEGACY_OPT_TYPES = {
  'string': str,
  'choice': None,
}

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
  required_args = []
  optional_args = []

  def __init__(self, *args, **kwargs):
    super(BaseCommand, self).__init__(*args, **kwargs)
    self.preconfig = PreconfigLoader.load()
    #self.preconf = Preconfigurator()

  @property
  def ignored_args(self):
    " returns a list of preconfiguration args which are used for loading "
    " settings, but should not be passed on to the actual command "
    return (set(self.preconfig.core_settings)
            .difference(self.required_args)
            .difference(self.optional_args)
          )

  def add_preconf_argument(self, parser, name, required=False):
    option = self.preconfig.arg_map[name]
    args, kwargs = option.arg_params
    kwargs = dict(kwargs, required=required)
    parser.add_argument(*args, **kwargs)

  def add_preconf_arguments(self, parser):
    for name in self.required_args:
      self.add_preconf_argument(parser, name, required=True)
    for name in self.optional_args:
      self.add_preconf_argument(parser, name, required=False)
    for name in self.ignored_args:
      self.add_preconf_argument(parser, name, required=False)

  def get_legacy_args(self):
    handle = super(BaseCommand, self).handle
    spec = inspect.getargspec(handle)
    defaults = list(spec.defaults) if spec.defaults else None

    argstring = self.args.strip()
    helps = []
    while argstring:
      if argstring.startswith('['):
        head, _, tail = argstring[1:].partition(']')
        head = head.rstrip('.').strip()
        helps.append((head, True))
        argstring = tail.strip()
      else:
        head, _, tail = argstring.partition(' ')
        helps.append((head, False))
        argstring = tail.strip()

    rsp = []
    for name in spec.args[1:]: # ignore 'self'
      help, optional = helps.pop(0)
      kw = {
        'nargs': '?' if optional else 1,
        'help': help,
      }
      if defaults:
        kw['default'] = defaults.pop(0)
      rsp.append(([name], kw))

    if spec.varargs and helps:
      name = 'args'
      help, optional = helps.pop(0)
      if helps and not optional and helps[0] == (help, True):
        nargs = '+'
      else:
        nargs = '*'
      kw = {
        'nargs': nargs,
        'help': spec.varargs.replace('_', ' '),
        'metavar': help,
      }
      rsp.append(([name], kw))
    return rsp

  def get_legacy_kwargs(self):
    rsp = []
    for option in self.option_list:
      args = option._long_opts + option._short_opts
      getter = attrgetter(*LEGACY_OPT_KWARGS)
      kwargs = dict(zip(LEGACY_OPT_KWARGS, getter(option)))
      if kwargs.get('type', None):
        kwargs['type'] = LEGACY_OPT_TYPES[kwargs['type']]
      kwargs = {k: v for k, v in kwargs.items() if v is not None}
      rsp.append((args, kwargs))
    return rsp

  def add_legacy_arguments(self, parser):
    " adds old-style (optparse) arguments to new style (argparse) parsers "
    " this can be used to subclass django 1.6 commands while maintaining "
    " the newer backported base command class interface "
    parser_opts = set(parser._option_string_actions.keys())

    for (args, kwargs) in self.get_legacy_args():
      if parser_opts.intersection(args):
        # already present on parser
        continue
      parser.add_argument(*args, **kwargs)

    for (args, kwargs) in self.get_legacy_kwargs():
      if parser_opts.intersection(args):
        # already present on parser
        continue
      parser.add_argument(*args, **kwargs)

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
    if self.preconfig:
      self.add_preconf_arguments(parser)
    self.add_legacy_arguments(parser)
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

    # strip ignored args before passing them on to the command
    if self.preconfig:
      for key in self.ignored_args.intersection(cmd_options.keys()):
        del cmd_options[key]

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
