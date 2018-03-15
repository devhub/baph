import inspect
import os
import sys
from argparse import ArgumentParser
from io import TextIOBase
from operator import attrgetter

from django.core.management import base
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import handle_default_options
from django.core.management.color import color_style, no_style
from django.utils.six import StringIO

from baph.core.preconfig.loader import PreconfigLoader
from baph.core.management.utils import get_command_options, get_parser_options
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

class OutputWrapper(TextIOBase):
  """
  Wrapper around stdout/stderr
  """
  @property
  def style_func(self):
    return self._style_func

  @style_func.setter
  def style_func(self, style_func):
    if style_func and self.isatty():
      self._style_func = style_func
    else:
      self._style_func = lambda x: x

  def __init__(self, out, style_func=None, ending='\n'):
    self._out = out
    self.style_func = None
    self.ending = ending

  def __getattr__(self, name):
    return getattr(self._out, name)

  def isatty(self):
    return hasattr(self._out, 'isatty') and self._out.isatty()

  def write(self, msg, style_func=None, ending=None):
    ending = self.ending if ending is None else ending
    if ending and not msg.endswith(ending):
      msg += ending
    style_func = style_func or self.style_func
    self._out.write(style_func(msg))

class BaseCommand(base.BaseCommand):
  _called_from_command_line = False
  allow_unknown_args = False

  def __init__(self, stdout=None, stderr=None, no_color=False, *args, **kwargs):
    self.preconfig = PreconfigLoader.load()
    self.stdout = OutputWrapper(stdout or sys.stdout)
    self.stderr = OutputWrapper(stderr or sys.stderr)
    if no_color:
      self.style = no_style()
    else:
      self.style = color_style()
      self.stderr.style_func = self.style.ERROR
    super(BaseCommand, self).__init__(*args, **kwargs)

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
    self.add_legacy_arguments(parser)
    self.add_arguments(parser)
    return parser

  def add_arguments(self, parser):
    """
    Entry point for subclassed commands to add custom arguments.
    """
    pass

  def normalize_argv(self, argv):
    " ensure the subcommand is always at arg[1] or django dies "
    subcommand = type(self).__module__.rsplit('.')[-1]
    pos = argv.index(subcommand)
    return [argv[0], subcommand] + argv[1:pos] + argv[pos+1:]

  @staticmethod
  def strip_ignorable_args(args, ignorable):
    _args = []
    for arg in args:
      if arg[0] == '-':
        name = arg.split('=', 1)[0]
        if name in ignorable:
          continue
      _args.append(arg)
    return _args

  def run_from_argv(self, argv):
    """
    Set up any environment changes requested (e.g., Python path
    and Django settings), then run this command. If the
    command raises a ``CommandError``, intercept it and print it sensibly
    to stderr. If the ``--traceback`` option is present or the raised
    ``Exception`` is not ``CommandError``, raise it.
    """
    #print 'run from argv:', argv
    argv = self.normalize_argv(argv)
    
    self._called_from_command_line = True
    parser = self.create_parser(argv[0], argv[1])
    options, args = parser.parse_known_args(argv[2:])
    cmd_options = vars(options)

    if self.preconfig:
      supported_opts = get_parser_options(parser)
      preconfig_opts = self.preconfig.all_flags
      ignorable_opts = preconfig_opts - supported_opts
      args = self.strip_ignorable_args(args, ignorable_opts)

    if self.allow_unknown_args:
      # pass unknown args to the subcommand
      args = list(args)
    elif args:
      # unknown args - reparse normally so it fails
      options = parser.parse_args(argv[2:])
    else:
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

  def execute(self, *args, **options):
    """
    Try to execute this command, performing system checks if needed (as
    controlled by the ``requires_system_checks`` attribute, except if
    force-skipped).
    """
    if 'no_color' in options and options['no_color']:
      self.style = no_style()
      self.stderr.style_func = None
    if options.get('stdout'):
      self.stdout = OutputWrapper(options['stdout'])
    if options.get('stderr'):
      self.stderr = OutputWrapper(options['stderr'], self.stderr.style_func)
    '''
    saved_locale = None
    if not self.leave_locale_alone:
      # Deactivate translations, because django-admin creates database
      # content like permissions, and those shouldn't contain any
      # translations.
      from django.utils import translation
      saved_locale = translation.get_language()
      translation.deactivate_all()
    '''
    try:
      all_output = ''
      funcs = (self.pre_handle, self.handle, self.post_handle)
      for func in funcs:
        output = func(*args, **options)
        if output:
          self.stdout.write(output)
          all_output += output
    finally:
      pass
      '''
      if saved_locale is not None:
        translation.activate(saved_locale)
      '''
    return all_output

  def pre_handle(self, *args, **options):
    """
    Optional hook to be run just before self.handle is executed
    """
    pass

  def handle(self, *args, **options):
    """
    The actual logic of the command. Subclasses must implement
    this method.
    """
    super_func = super(BaseCommand, self).handle
    if super_func:
      return super_func(*args, **options)
    raise NotImplementedError('subclasses of BaseCommand must provide a '
                              'handle() method')

  def post_handle(self, *args, **options):
    """
    Optional hook to be run just after self.handle is executed
    """
    pass

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

class LabelCommand(BaseCommand):
  """
  A management command which takes one or more arbitrary arguments
  (labels) on the command line, and does something with each of
  them.
  Rather than implementing ``handle()``, subclasses must implement
  ``handle_label()``, which will be called once for each label.
  If the arguments should be names of installed applications, use
  ``AppCommand`` instead.
  """
  label = 'label'
  missing_args_message = "Enter at least one %s." % label

  def add_arguments(self, parser):
    parser.add_argument('args', metavar=self.label, nargs='+')

  def handle(self, *labels, **options):
    output = []
    for label in labels:
      label_output = self.handle_label(label, **options)
      if label_output:
        output.append(label_output)
    return '\n'.join(output)

  def handle_label(self, label, **options):
    """
    Perform the command's actions for ``label``, which will be the
    string as given on the command line.
    """
    raise NotImplementedError('subclasses of LabelCommand must provide a handle_label() method')