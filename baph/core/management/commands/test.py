from __future__ import absolute_import
import logging
import sys
import os
from optparse import make_option, OptionParser

from django.conf import settings
from django.test.utils import get_runner

from baph.core.management.new_base import BaseCommand


class Command(BaseCommand):
    help = ('Discover and run tests in the specified modules or the '
            'current directory.')
    test_runner = None
    '''
    option_list = BaseCommand.option_list + (
        make_option('--noinput',
            action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),
        make_option('--failfast',
            action='store_true', dest='failfast', default=False,
            help='Tells Django to stop running the test suite after first '
                 'failed test.'),
        make_option('--testrunner',
            action='store', dest='testrunner',
            help='Tells Django to use specified test runner class instead of '
                 'the one specified by the TEST_RUNNER setting.'),
        make_option('--liveserver',
            action='store', dest='liveserver', default=None,
            help='Overrides the default address where the live server (used '
                 'with LiveServerTestCase) is expected to run from. The '
                 'default value is localhost:8081.'),
    )
    args = '[appname ...]'
    '''

    def run_from_argv(self, argv):
      """
      Pre-parse the command line to extract the value of the --testrunner
      option. This allows a test runner to define additional command line
      arguments.
      """
      option = '--testrunner='
      for arg in argv[2:]:
        if arg.startswith(option):
          self.test_runner = arg[len(option):]
          break
      super(Command, self).run_from_argv(argv)

    def add_arguments(self, parser):
      parser.add_argument(
        'args', metavar='test_label', nargs='*',
        help='Module paths to test; can be modulename, modulename.TestCase or '
             'modulename.TestCase.test_method'
      )
      parser.add_argument(
        '--noinput', '--no-input', action='store_false', dest='interactive',
        help='Tells Django to NOT prompt the user for input of any kind.',
      )
      parser.add_argument(
        '--failfast', action='store_true', dest='failfast',
        help='Tells Django to stop running the test suite after first failed '
             'test.',
      )
      parser.add_argument(
        '--testrunner', action='store', dest='testrunner',
        help='Tells Django to use specified test runner class instead of '
             'the one specified by the TEST_RUNNER setting.',
      )

      test_runner_class = get_runner(settings, self.test_runner)

      if hasattr(test_runner_class, 'add_arguments'):
          test_runner_class.add_arguments(parser)        

    '''
    def create_parser(self, prog_name, subcommand):
        test_runner_class = get_runner(settings)
        options = self.option_list + getattr(
            test_runner_class, 'option_list', ())
        return OptionParser(prog=prog_name,
                            usage=self.usage(subcommand),
                            version=self.get_version(),
                            option_list=options)
    '''
    '''
    def execute(self, *args, **options):
        if int(options['verbosity']) > 0:
            # ensure that deprecation warnings are displayed during testing
            # the following state is assumed:
            # logging.capturewarnings is true
            # a "default" level warnings filter has been added for
            # DeprecationWarning. See django.conf.LazySettings._configure_logging
            logger = logging.getLogger('py.warnings')
            handler = logging.StreamHandler()
            logger.addHandler(handler)
        super(Command, self).execute(*args, **options)
        if int(options['verbosity']) > 0:
            # remove the testing-specific handler
            logger.removeHandler(handler)
    '''
    def handle(self, *test_labels, **options):
      from django.conf import settings
      from django.test.utils import get_runner

      TestRunner = get_runner(settings) #, options.get('testrunner'))
      '''
      options['verbosity'] = int(options.get('verbosity'))

      if options.get('liveserver') is not None:
        os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = options['liveserver']
        del options['liveserver']
      '''
      test_runner = TestRunner(**options)
      failures = test_runner.run_tests(test_labels)

      if failures:
        sys.exit(1)
