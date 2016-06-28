from copy import deepcopy
import sys
import unittest as real_unittest

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.test import _doctest as doctest, runner
from django.test.simple import OutputChecker, DocTestRunner, get_tests #, build_suite #, build_test
from django.test.utils import setup_test_environment, teardown_test_environment
from django.utils import unittest
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule
from sqlalchemy import inspect, create_engine
from sqlalchemy.orm.session import Session
from sqlalchemy.schema import CreateSchema, DropSchema

from baph.db.models import get_app, get_apps
from baph.db.orm import ORM, Base
from baph.utils.importing import import_any_module


orm = ORM.get()

__all__ = ('BaphTestSuiteRunner',)

# The module name for tests outside models.py
TEST_MODULE = 'tests'

doctestOutputChecker = OutputChecker()


def extract_app_name(app_label):
    " determine the relevant entry in settings.INSTALLED_APPS "
    " which corresponds to this string-based module import "
    for app_name in sorted(settings.INSTALLED_APPS, key=lambda x: -1*len(x)):
        # we go from longest to shortest, so earlier matches are longer
        if len(app_name) > len(app_label):
            continue
        if app_label.startswith(app_name):
            return app_name
            
    # no result yet, try matching the short name
    short = app_label.split('.',1)[0]
    for app_name in settings.INSTALLED_APPS:
        if app_name.rsplit('.',1)[-1] == short:
            return short

    raise Exception(
        'App name could not be determined from label %s' 
        % app_label)

def make_doctest(module):
    return doctest.DocTestSuite(module,
       checker=doctestOutputChecker,
       runner=DocTestRunner,
    )

def build_suite(app_module):
    """
    Create a complete Django test suite for the provided application module.
    """
    suite = unittest.TestSuite()

    # Load unit and doctests in the models.py module. If module has
    # a suite() method, use it. Otherwise build the test suite ourselves.
    if hasattr(app_module, 'suite'):
        test = app_module.suite()
        if len(test._tests) > 0:
            suite.addTests(test._tests)
    else:
        test = unittest.TestLoader().loadTestsFromModule(app_module)
        if len(test._tests) > 0:
            suite.addTests(test._tests)
        try:
            test = doctest.DocTestSuite(app_module,
                checker=doctestOutputChecker, runner=DocTestRunner)
            if len(test._tests) > 0:
                suite.addTests(test._tests)
        except ValueError:
            # No doc tests in models.py
            pass

    # Check to see if a separate 'tests' module exists parallel to the
    # models module
    test_module = get_tests(app_module)
    if test_module:
        # Load unit and doctests in the tests.py module. If module has
        # a suite() method, use it. Otherwise build the test suite ourselves.
        if hasattr(test_module, 'suite'):
            test = test_module.suite()
            if len(test._tests) > 0:
                suite.addTests(test._tests)
        else:
            test = unittest.defaultTestLoader.loadTestsFromModule(test_module)
            if len(test._tests) > 0:
                suite.addTests(test._tests)
            try:
                test = doctest.DocTestSuite(test_module,
                    checker=doctestOutputChecker, runner=DocTestRunner)
                if len(test._tests) > 0:
                    suite.addTests(test._tests)
            except ValueError:
                # No doc tests in tests.py
                pass
    return suite


def build_test(label):
    """
    Construct a test case with the specified label. Label should be of the
    form model.TestClass or model.TestClass.test_method. Returns an
    instantiated test or test suite corresponding to the label provided.

    """
    app_name = extract_app_name(label)
    if not app_name:
        raise Exception('App name could not be determined from label %s' % label)

    remainder = label[len(app_name)+1:]
    if not remainder:
        " this is an app, not a specific test case "
        pass

    parts = [app_name] + remainder.split('.')
    if len(parts) < 2 or len(parts) > 3:
        raise ValueError("Test label '%s' should be of the form app.TestCase "
                         "or app.TestCase.test_method" % label)

    #
    # First, look for TestCase instances with a name that matches
    #
    app_module = get_app(parts[0])
    test_module = get_tests(app_module)
    TestClass = getattr(app_module, parts[1], None)

    # Couldn't find the test class in models.py; look in tests.py
    if TestClass is None:
        if test_module:
            TestClass = getattr(test_module, parts[1], None)

    try:
        if issubclass(TestClass, (unittest.TestCase, real_unittest.TestCase)):
            if len(parts) == 2: # label is app.TestClass
                try:
                    return unittest.TestLoader() \
                        .loadTestsFromTestCase(TestClass)
                except TypeError:
                    raise ValueError(
                        "Test label '%s' does not refer to a test class"
                        % label)
            else: # label is app.TestClass.test_method
                return TestClass(parts[2])
    except TypeError:
        # TestClass isn't a TestClass - it must be a method or normal class
        pass

    #
    # If there isn't a TestCase, look for a doctest that matches
    #
    tests = []
    for module in app_module, test_module:
        try:
            doctests = make_doctest(module)
            # Now iterate over the suite, looking for doctests whose name
            # matches the pattern that was given
            for test in doctests:
                if test._dt_test.name in (
                        '%s.%s' % (module.__name__, '.'.join(parts[1:])),
                        '%s.__test__.%s' % (
                            module.__name__, '.'.join(parts[1:]))):
                    tests.append(test)
        except ValueError:
            # No doctests found.
            pass

    # If no tests were found, then we were given a bad test label.
    if not tests:
        raise ValueError("Test label '%s' does not refer to a test" % label)

    # Construct a suite out of the tests that matched.
    return unittest.TestSuite(tests)


class BaphTestSuiteRunner(runner.DiscoverRunner):

    def build_suite(self, test_labels, extra_tests=None, **kwargs):
        suite = unittest.TestSuite()

        if test_labels:
            for label in test_labels:
                app_name = extract_app_name(label)
                if app_name == label:
                    app = get_app(label)
                    suite.addTest(build_suite(app))
                else:
                    suite.addTest(build_test(label))
        else:
            for app in get_apps():
                if app.__name__.startswith('django.'):
                    continue
                test = build_suite(app)
                suite.addTest(test)

        if extra_tests:
            for test in extra_tests:
                suite.addTest(test)

        return suite

    def setup_databases(self, **kwargs):
        # import all models to populate orm.metadata
        for app in settings.INSTALLED_APPS:
            import_any_module(['%s.models' % app], raise_error=False)

        # determine which schemas we need
        default_schema = orm.engine.url.database
        schemas = set(t.schema or default_schema \
            for t in Base.metadata.tables.values())

        url = deepcopy(orm.engine.url)
        url.database = None
        self.engine = create_engine(url)
        insp = inspect(self.engine)

        # get a list of already-existing schemas
        existing_schemas = set(insp.get_schema_names())

        # if any of the needed schemas exist, do not proceed
        conflicts = schemas.intersection(existing_schemas)
        if conflicts:
            for c in conflicts:
                print 'drop schema %s;' % c
            sys.exit('The following schemas are already present: %s. ' \
                'TestRunner cannot proceeed' % ','.join(conflicts))
        
        # create schemas
        session = Session(bind=self.engine)
        for schema in schemas:
            session.execute(CreateSchema(schema))
        session.commit()
        session.bind.dispose()

        # create tables
        if len(orm.Base.metadata.tables) > 0:
            orm.Base.metadata.create_all(checkfirst=False)

        # generate permissions
        call_command('createpermissions')

        return schemas

    def run_suite(self, suite, **kwargs):
        return unittest.TextTestRunner(verbosity=self.verbosity, 
                               failfast=self.failfast) \
            .run(suite)

    def teardown_databases(self, old_config, **kwargs):
        call_command('purge', interactive=False)
        pass

    def teardown_test_environment(self, **kwargs):
        unittest.removeHandler()
        teardown_test_environment()

    def suite_result(self, suite, result, **kwargs):
        return len(result.failures) + len(result.errors)

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        """
        Run the unit tests for all the test labels in the provided list.
        Labels must be of the form:
         - app.TestClass.test_method
            Run a single specific test method
         - app.TestClass
            Run all the test methods in a given class
         - app
            Search for doctests and unittests in the named application.

        When looking for tests, the test runner will look in the models and
        tests modules for the application.

        A list of 'extra' tests may also be provided; these tests
        will be added to the test suite.

        Returns the number of tests that failed.
        """
        self.setup_test_environment()
        suite = self.build_suite(test_labels, extra_tests)
        old_config = self.setup_databases()
        result = self.run_suite(suite)
        self.teardown_databases(old_config)
        self.teardown_test_environment()
        return self.suite_result(suite, result)
