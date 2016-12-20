from collections import defaultdict
import json
import time

from django.conf import settings
from django.core.cache import get_cache
from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS, connections, transaction
from django import test
from django.test.testcases import connections_support_transactions
from sqlalchemy import create_engine
from sqlalchemy.orm.session import Session
from sqlalchemy.orm import sessionmaker

from baph.db.orm import ORM
from .signals import add_timing


PRINT_TEST_TIMINGS = getattr(settings, 'PRINT_TEST_TIMINGS', False)

#Session = sessionmaker()
orm = ORM.get()

class BaphFixtureMixin(object):
    reset_sequences = False
    test_start_time = None
    test_end_time = None
    tests_run = 0
    timings = None

    '''
    @classmethod
    def _databases_names(cls, include_mirrors=True):
        # If the test case has a multi_db=True flag, act on all databases,
        # including mirrors or not. Otherwise, just on the default DB.
        if getattr(cls, 'multi_db', False):
            return [alias for alias in connections
                    if include_mirrors or not connections[alias].settings_dict['TEST']['MIRROR']]
        else:
            return [DEFAULT_DB_ALIAS]

    @classmethod
    def _enter_atomics(cls):
        """Helper method to open atomic blocks for multiple databases"""
        print '    _enter atomics', cls
        atomics = {}
        for db_name in cls._databases_names():
            atomics[db_name] = transaction.atomic(using=db_name)
            atomics[db_name].__enter__()
        return atomics

    @classmethod
    def _rollback_atomics(cls, atomics):
        """Rollback atomic blocks opened through the previous method"""
        print '    _rollback atomics', cls
        for db_name in reversed(cls._databases_names()):
            transaction.set_rollback(True, using=db_name)
            atomics[db_name].__exit__(None, None, None)

    def _should_reload_connections(self):
        return False

    def _pre_setup(self):
        print '\npre setup', connections['default'].connection
        """Performs any pre-test setup. This includes:
        * If the class has an 'available_apps' attribute, restricting the app
          registry to these applications, then firing post_migrate -- it must
          run with the correct set of applications for the test case.
        * If the class has a 'fixtures' attribute, installing these fixtures.
        """
        #print 'pre super setup'
        #super(BaphFixtureMixin, self)._pre_setup()
        #print 'post super setup'
        if self.available_apps is not None:
            apps.set_available_apps(self.available_apps)
            setting_changed.send(sender=settings._wrapped.__class__,
                                 setting='INSTALLED_APPS',
                                 value=self.available_apps,
                                 enter=True)
            for db_name in self._databases_names(include_mirrors=False):
                emit_post_migrate_signal(verbosity=0, interactive=False, db=db_name)
        try:
            self._fixture_setup()
        except Exception:
            if self.available_apps is not None:
                apps.unset_available_apps()
                setting_changed.send(sender=settings._wrapped.__class__,
                                     setting='INSTALLED_APPS',
                                     value=settings.INSTALLED_APPS,
                                     enter=False)

            raise

    def _post_teardown(self):
        """Performs any post-test things. This includes:
        * Flushing the contents of the database, to leave a clean slate. If
          the class has an 'available_apps' attribute, post_migrate isn't fired.
        * Force-closing the connection, so the next test gets a clean cursor.
        """
        print '\npost teardown', connections['default'].connection
        try:
            self._fixture_teardown()
            #super(BaphFixtureMixin, self)._post_teardown()
            if self._should_reload_connections():
                # Some DB cursors include SQL statements as part of cursor
                # creation. If you have a test that does a rollback, the effect
                # of these statements is lost, which can affect the operation of
                # tests (e.g., losing a timezone setting causing objects to be
                # created with the wrong time). To make sure this doesn't
                # happen, get a clean connection at the start of every test.
                for conn in connections.all():
                    print 'closing:', conn
                    conn.close()
        finally:
            if self.available_apps is not None:
                apps.unset_available_apps()
                setting_changed.send(sender=settings._wrapped.__class__,
                                     setting='INSTALLED_APPS',
                                     value=settings.INSTALLED_APPS,
                                     enter=False)

    @classmethod
    def setUpClass(cls):
        print 'setupclass start', cls
        #super(BaphFixtureMixin, cls).setUpClass()
        cls.test_start_time = time.time()
        cls.timings = defaultdict(list)
        if PRINT_TEST_TIMINGS:
            add_timing.connect(cls.add_timing)

        if not connections_support_transactions():
            return
        print '  enter atomics'
        cls.cls_atomics = cls._enter_atomics()
        print '  enter atomics done'

        if cls.fixtures:
            for db_name in cls._databases_names(include_mirrors=False):
                print 'loaddata start', db_name
                try:
                    call_command('loaddata', *cls.fixtures, **{
                        'verbosity': 0,
                        'commit': False,
                        'database': db_name,
                    })
                    print 'loaddata end', db_name
                except Exception as e:
                    print 'loaddata failed', db_name
                    cls._rollback_atomics(cls.cls_atomics)
                    raise

        try:
            cls.setUpTestData()
        except Exception:
            cls._rollback_atomics(cls.cls_atomics)
            raise

    @classmethod
    def tearDownClass(cls):
        print 'teardownclass', cls
        if connections_support_transactions():
            cls._rollback_atomics(cls.cls_atomics)
            for conn in connections.all():
                conn.close()
        #super(BaphFixtureMixin, cls).tearDownClass()
        if PRINT_TEST_TIMINGS:
            add_timing.disconnect(cls.add_timing)
        cls.test_end_time = time.time()
        if PRINT_TEST_TIMINGS:
            cls.print_timings()

    @classmethod
    def setUpTestData(cls):
        """Load initial data for the TestCase"""
        pass

    def _fixture_setup(self):
        if not connections_support_transactions():
            self.setUpTestData()
            if hasattr(self, 'fixtures'):
                self.load_fixtures(*self.fixtures)
            #return super(BaphFixtureMixin, self)._fixture_setup()

        assert not self.reset_sequences, \
            'reset_sequences cannot be used on TestCase instances'
        self.atomics = self._enter_atomics()
        #if hasattr(self, 'fixtures'):
        #    self.load_fixtures(*self.fixtures)

    def _fixture_teardown(self):
        if not connections_support_transactions():
            if hasattr(self, 'fixtures'):
                self.purge_fixtures(*self.fixtures)
            #return super(BaphFixtureMixin, self)._fixture_teardown()
        self._rollback_atomics(self.atomics)
        #if hasattr(self, 'fixtures'):
        #    self.purge_fixtures(*self.fixtures)
    '''

    @classmethod
    def add_timing(cls, sender, key, time, **kwargs):
        cls.timings[key].append(time)

    def run(self, *args, **kwargs):
        type(self).tests_run += 1
        super(BaphFixtureMixin, self).run(*args, **kwargs)

    @classmethod
    def print_timings(cls):
        total = cls.test_end_time - cls.test_start_time
        print '\n%s timings:' % cls.__name__
        print '  %d test(s) run, totalling %.03fs' % (cls.tests_run, total)
        if not cls.timings:
            return
        items = sorted(cls.timings.items())
        keys = [item[0] for item in items]
        for i, key in enumerate(keys):
            if ':' not in key:
                continue
            start, end = key.split(':', 1)
            if start in keys:
                keys[i] = '  %s' % end
        max_key_len = max(len(k) for k in keys)
        for i, (k, v) in enumerate(items):
            print '  %s: %d calls, totalling %.03fs (%.02f%%)' % (
                keys[i].ljust(max_key_len), len(v), sum(v), 100.0*sum(v)/total)

    @classmethod
    def load_fixtures(cls, *fixtures):
        params = {
            'verbosity': 0,
            'database': None,
            'skip_validation': True,
            'commit': False,
            }
        start = time.time()
        call_command('loaddata', *fixtures, **params)
        if PRINT_TEST_TIMINGS:
            add_timing.send(None, key='loaddata', time=time.time()-start)

    @classmethod
    def purge_fixtures(cls, *fixtures):
        params = {
            'verbosity': 0,
            'interactive': False,
            }
        start = time.time()
        call_command('flush', **params)
        if PRINT_TEST_TIMINGS:
            add_timing.send(None, key='flush', time=time.time()-start)

    @classmethod
    def setUpClass(cls):
        cls.test_start_time = time.time()
        cls.timings = defaultdict(list)
        super(BaphFixtureMixin, cls).setUpClass()
        if PRINT_TEST_TIMINGS:
            add_timing.connect(cls.add_timing)
        cls.session = orm.session_factory()
        if hasattr(cls, 'persistent_fixtures'):
            cls.load_fixtures(*cls.persistent_fixtures)
        '''
        cls.connection = orm.engine.connect()
        cls.session = Session(bind=cls.connection, autoflush=False)
        orm.sessionmaker.registry.set(cls.session)
        cls.savepoint = cls.connection.begin()
        if hasattr(cls, 'fixtures'):
            cls.load_fixtures(*cls.fixtures)
        '''

    @classmethod
    def tearDownClass(cls):
        super(BaphFixtureMixin, cls).tearDownClass()
        cls.session.close()
        '''
        cls.savepoint.rollback()
        cls.connection.close()
        '''
        if hasattr(cls, 'persistent_fixtures'):
            cls.purge_fixtures(*cls.persistent_fixtures)
        if PRINT_TEST_TIMINGS:
            add_timing.disconnect(cls.add_timing)
        cls.test_end_time = time.time()
        if PRINT_TEST_TIMINGS:
            cls.print_timings()
    '''
    def setUp(self):
        super(BaphFixtureMixin, self).setUp()
        self.savepoint2 = self.connection.begin_nested()
        self.savepoint3 = self.connection.begin_nested()
        self.backup_bind = orm.session_factory.kw['bind']
        orm.session_factory.configure(bind=self.connection)

    def tearDown(self):
        orm.session_factory.configure(bind=self.backup_bind)
        self.savepoint2.rollback()
        self.session.close()
        super(BaphFixtureMixin, self).tearDown()
    '''
    def _fixture_setup(self):
        if hasattr(self, 'fixtures'):
            self.load_fixtures(*self.fixtures)

    def _fixture_teardown(self):
        if hasattr(self, 'fixtures'):
            self.purge_fixtures(*self.fixtures)

    def assertItemsOrderedBy(self, items, field):
        if not items:
            # no items, no ordering to check
            return
        if isinstance(items[0], dict):
            key = lambda x: x[field]
        else:
            key = lambda x: getattr(x, field)
        ordered = sorted(items, key=key)
        self.assertEqual(items, ordered)

    def assertItemsReverseOrderedBy(self, items, field):
        if not items:
            # no items, no ordering to check
            return
        if isinstance(items[0], dict):
            key = lambda x: x[field]
        else:
            key = lambda x: getattr(x, field)
        ordered = sorted(items, key=key)[::-1]
        self.assertEqual(items, ordered)


class MemcacheMixin(object):

    def populate_cache(self, asset_aliases=None):
        """
        reads the current key/value pairs from the cache and
        stores it in self.initial_data, for comparison with post-test results
        """
        self.initial = {}
        self.initial[None] = {k: self.cache._cache.get(k)
            for k in self.cache.get_all_keys()}
        for alias in asset_aliases or ():
            cache = get_cache(alias)
            self.initial[alias] = {k: cache._cache.get(k)
                for k in cache.get_all_keys()}

    def assertCacheHit(self, rsp):
        self.assertEqual(rsp['x-from-cache'], 'True')

    def assertCacheMiss(self, rsp):
        self.assertEqual(rsp['x-from-cache'], 'False')

    def assertCacheKeyEqual(self, key, value, version=None, cache_alias=None):
        cache = get_cache(cache_alias) if cache_alias else self.cache
        current_value = cache.get(key, version=version)
        self.assertEqual(current_value, value)

    def assertCacheKeyUnchanged(self, key, version=None, cache_alias=None):
        cache = get_cache(cache_alias) if cache_alias else self.cache
        raw_key = cache.make_key(key, version=version)
        initial_value = self.initial[cache_alias].get(raw_key, 0)
        current_value = cache.get(key, version=version)
        self.assertEqual(current_value, initial_value)

    def assertCacheKeyCreated(self, key, version=None, cache_alias=None):
        cache = get_cache(cache_alias) if cache_alias else self.cache
        raw_key = cache.make_key(key, version=version)
        self.assertNotIn(raw_key, self.initial[cache_alias].keys())
        self.assertIn(raw_key, cache.get_all_keys())

    def assertCacheKeyNotCreated(self, key, version=None, cache_alias=None):
        cache = get_cache(cache_alias) if cache_alias else self.cache
        raw_key = cache.make_key(key, version=version)
        self.assertNotIn(raw_key, self.initial[cache_alias].keys())
        self.assertNotIn(raw_key, cache.get_all_keys())

    def assertCacheKeyIncremented(self, key, version=None, cache_alias=None):
        cache = get_cache(cache_alias) if cache_alias else self.cache
        raw_key = cache.make_key(key, version=version)
        initial_value = self.initial[cache_alias].get(raw_key, 0)
        current_value = cache.get(key, version=version)
        self.assertEqual(current_value, initial_value+1)

    def assertCacheKeyIncrementedMulti(self, key, version=None, cache_alias=None):
        cache = get_cache(cache_alias) if cache_alias else self.cache
        raw_key = cache.make_key(key, version=version)
        initial_value = self.initial[cache_alias][raw_key]
        current_value = cache.get(key, version=version)
        self.assertGreater(current_value, initial_value)
        
    def assertCacheKeyInvalidated(self, key, version=None, cache_alias=None):
        cache = get_cache(cache_alias) if cache_alias else self.cache
        raw_key = cache.make_key(key, version=version)
        current_value = cache.get(key, version=version)
        self.assertIn(raw_key, self.initial[cache_alias].keys())
        self.assertEqual(current_value, None)

    def assertCacheKeyNotInvalidated(self, key, version=None, cache_alias=None):
        cache = get_cache(cache_alias) if cache_alias else self.cache
        raw_key = cache.make_key(key, version=version)
        current_value = cache.get(key, version=version)
        self.assertIn(raw_key, self.initial[cache_alias].keys())
        self.assertNotEqual(current_value, None)

    def assertPointerKeyInvalidated(self, key, version=None, cache_alias=None):
        cache = get_cache(cache_alias) if cache_alias else self.cache
        raw_key = cache.make_key(key, version=version)
        current_value = cache.get(key, version=version)
        self.assertIn(raw_key, self.initial[cache_alias].keys())
        self.assertEqual(current_value, 0)

    def assertPointerKeyNotInvalidated(self, key, version=None, cache_alias=None):
        cache = get_cache(cache_alias) if cache_alias else self.cache
        raw_key = cache.make_key(key, version=version)
        current_value = cache.get(key, version=version)
        self.assertIn(raw_key, self.initial[cache_alias].keys())
        self.assertNotEqual(current_value, 0)


class TestCase(BaphFixtureMixin, test.TestCase):
    pass


class LiveServerTestCase(BaphFixtureMixin, test.LiveServerTestCase):
    pass


class MemcacheTestCase(MemcacheMixin, TestCase):
    def _fixture_setup(self):
        super(MemcacheTestCase, self)._fixture_setup()
        self.cache.flush_all()

    def setUp(self, objs={}, counts={}):
        self.initial = {}
        super(MemcacheTestCase, self).setUp()

class MemcacheLSTestCase(MemcacheMixin, LiveServerTestCase):
    def _fixture_setup(self):
        super(MemcacheLSTestCase, self)._fixture_setup()
        self.cache.flush_all()

    def setUp(self, objs={}, counts={}):
        self.initial = {}
        super(MemcacheLSTestCase, self).setUp()


