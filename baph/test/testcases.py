from __future__ import absolute_import
from __future__ import print_function
from collections import defaultdict
import timeit

from django.conf import settings
from django.core.cache import get_cache
from django.db import DEFAULT_DB_ALIAS, connections, transaction
from django import test
from django.test.testcases import connections_support_transactions
from sqlalchemy import create_engine, event
from sqlalchemy.orm.session import Session
from sqlalchemy.orm import sessionmaker

from baph.core.management import call_command
from baph.db.orm import ORM
from .signals import add_timing


if not hasattr(test.SimpleTestCase, 'assertItemsEqual'):
    test.SimpleTestCase.assertItemsEqual = test.SimpleTestCase.assertCountEqual

from contextlib import contextmanager


@contextmanager
def timer(key):
    start = timeit.default_timer()
    try:
        yield
    finally:
        elapsed = timeit.default_timer() - start
        add_timing.send(None, key=key, time=elapsed)

use_transactions = getattr(settings, 'USE_TRANSACTIONS', False)

PRINT_TEST_TIMINGS = getattr(settings, 'PRINT_TEST_TIMINGS', False)

#Session = sessionmaker()
orm = ORM.get()

def db_debug(msg):
    "SELECTs a debug message so it appears in the db log"
    session = orm.sessionmaker()
    session.execute("/* %s */" % msg)


class TransactionTestCase(test.TransactionTestCase):
    test_start_time = None
    test_end_time = None
    tests_run = 0
    timings = None

    @classmethod
    def setUpClass(cls):
        #print('BaphTTest.setupClass start')
        super(TransactionTestCase, cls).setUpClass()
        cls.session = orm.sessionmaker()
        if PRINT_TEST_TIMINGS:
            cls.timings = defaultdict(list)
            cls.test_start_time = timeit.default_timer()
            add_timing.connect(cls.add_timing)
        #print('BaphTTest.setupClass end')

    @classmethod
    def tearDownClass(cls):
        #print('BaphTTest.teardownClass start')
        
        if not use_transactions:
            cls.session.close()
        if PRINT_TEST_TIMINGS:
            add_timing.disconnect(cls.add_timing)
            cls.test_end_time = timeit.default_timer()
            cls.print_timings()
        super(TransactionTestCase, cls).tearDownClass()
        #print('BaphTTest.teardownClass end')

    def run(self, *args, **kwargs):
        #print('\nBaphTest.run:', self)
        #db_debug(str(self))
        type(self).tests_run += 1
        super(TransactionTestCase, self).run(*args, **kwargs)
        #print('BaphTest.run end:\n')

    @classmethod
    def add_timing(cls, sender, key, time, **kwargs):
        cls.timings[key].append(time)

    @classmethod
    def print_timings(cls):
        total = cls.test_end_time - cls.test_start_time
        print('\n%s timings:' % cls.__name__)
        print('  %d test(s) run, totalling %.03fs' % (cls.tests_run, total))
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
            print('  %s: %d calls, totalling %.03fs (%.02f%%)' % (
                keys[i].ljust(max_key_len), len(v), sum(v), 100.0*sum(v)/total))

    @classmethod
    def load_fixtures(cls, *fixtures):
        params = {
            'verbosity': 0,
            'database': None,
        }
        with timer('loaddata'):
            call_command('loaddata', *fixtures, **params)
        cls.session.commit()

    @classmethod
    def purge_fixtures(cls, *fixtures):
        params = {
            'verbosity': 0,
            'interactive': False,
        }
        with timer('flush'):
            call_command('flush', **params)
        if not use_transactions:
            cls.session.flush()
            cls.session.close()

    def _fixture_setup(self):
        fixtures = getattr(self, 'persistent_fixtures', getattr(self, 'fixtures', None))
        if fixtures:
            self.load_fixtures(*fixtures)

    def _fixture_teardown(self):
        fixtures = getattr(self, 'persistent_fixtures', getattr(self, 'fixtures', None))
        if fixtures:
            self.purge_fixtures()

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


def dwelte_instrument(session):
    def close():
        raise Exception("whoops")
    session.close = close

class TestCase(TransactionTestCase):
    @classmethod
    def end_fixture_tx(cls, session, transaction):
        if not cls.fixture_tx.is_active:
            cls.fixture_tx = cls.session.begin_nested()

    @classmethod
    def end_test_tx(cls, session, transaction):
        if not cls.test_tx.is_active:
            cls.test_tx = cls.session.begin_nested()

    @classmethod
    def setUpClass(cls):
        super(TestCase, cls).setUpClass()
        if use_transactions:
            cls.fixture_tx = cls.session.begin_nested()
            cls.test_tx = cls.session.begin_nested()

            event.listen(cls.session, "after_transaction_end", cls.end_test_tx, cls)

    @classmethod
    def tearDownClass(cls):
        if use_transactions:
            event.remove(cls.session, "after_transaction_end", cls.end_test_tx)

            if cls.test_tx.is_active:
                cls.test_tx.rollback()
            if cls.fixture_tx.is_active:
                cls.fixture_tx.rollback()

            cls.session.rollback()
        super(TestCase, cls).tearDownClass()

    @classmethod
    def setUpTestData(cls):
        """Load initial data for the TestCase"""
        pass

    def tearDown(self):
        if use_transactions:
            self.test_tx.rollback()
        super(TestCase, self).tearDown()

    def _fixture_setup(self):
        if use_transactions:
            event.listen(self.session, "after_transaction_end", self.end_fixture_tx, type(self))
        super(TestCase, self)._fixture_setup()
        self.setUpTestData()
        self.session.flush()
        self.session.expunge_all()
        if use_transactions:
            event.remove(self.session, "after_transaction_end", self.end_fixture_tx)

    def _fixture_teardown(self):
        super(TestCase, self)._fixture_teardown()


class MemcacheMixin(object):

    def _fixture_setup(self):
        # clear all caches before loading fixtures
        super(MemcacheMixin, self)._fixture_setup()
        for c in settings.CACHES:
            cache = get_cache(c)
            cache.clear()
            cache.close()
            del cache

    def setUp(self):
        super(MemcacheMixin, self).setUp()
        self.initial = {}

    def populate_cache(self, asset_aliases=None):
        """
        reads the current key/value pairs from the cache and
        stores it in self.initial_data, for comparison with post-test results
        """
        self.initial = {}
        keys = list(self.cache.get_all_keys())
        self.initial[None] = {k: self.cache._cache.get(k) for k in keys}
        self.initial[None] = {k: v for k, v in self.initial[None].items() if v is not None}

        for alias in asset_aliases or ():
            cache = get_cache(alias)
            self.initial[alias] = {k: cache._cache.get(k)
                for k in cache.get_all_keys()}

    def _initial(self, cache_alias):
        """
        Return the initial contents of the cache with the specified alias
        for the special case where cache_alias is None, an empty dict will
        be returned if the 'None' key isn't present
        This is to solve issues where test assertions are called but
        populate_cache was never called (which implies the test has no
        initial keys), so initial_cache[None] was never set up
        """
        if cache_alias is None:
            return self.initial.get(cache_alias, {})
        return self.initial[cache_alias]

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
        initial_value = self._initial(cache_alias).get(raw_key, 0)
        current_value = cache.get(key, version=version)
        self.assertEqual(current_value, initial_value)

    def assertCacheKeyCreated(self, key, version=None, cache_alias=None):
        cache = get_cache(cache_alias) if cache_alias else self.cache
        raw_key = cache.make_key(key, version=version)
        self.assertNotIn(raw_key, list(self._initial(cache_alias).keys()))
        self.assertIn(raw_key, cache.get_all_keys())

    def assertCacheKeyNotCreated(self, key, version=None, cache_alias=None):
        cache = get_cache(cache_alias) if cache_alias else self.cache
        raw_key = cache.make_key(key, version=version)
        self.assertNotIn(raw_key, list(self._initial(cache_alias).keys()))
        self.assertNotIn(raw_key, cache.get_all_keys())

    def assertCacheKeyIncremented(self, key, version=None, cache_alias=None):
        cache = get_cache(cache_alias) if cache_alias else self.cache
        raw_key = cache.make_key(key, version=version)
        initial_value = self._initial(cache_alias).get(raw_key, 0)
        current_value = cache.get(key, version=version)
        self.assertEqual(current_value, initial_value+1)

    def assertCacheKeyIncrementedMulti(self, key, version=None, cache_alias=None):
        cache = get_cache(cache_alias) if cache_alias else self.cache
        raw_key = cache.make_key(key, version=version)
        initial_value = self._initial(cache_alias)[raw_key]
        current_value = cache.get(key, version=version)
        self.assertGreater(current_value, initial_value)

    def assertCacheKeyInvalidated(self, key, version=None, cache_alias=None):
        cache = get_cache(cache_alias) if cache_alias else self.cache
        raw_key = cache.make_key(key, version=version)
        current_value = cache.get(key, version=version)
        self.assertIn(raw_key, list(self._initial(cache_alias).keys()))
        self.assertEqual(current_value, None)

    def assertCacheKeyNotInvalidated(self, key, version=None, cache_alias=None):
        cache = get_cache(cache_alias) if cache_alias else self.cache
        raw_key = cache.make_key(key, version=version)
        current_value = cache.get(key, version=version)
        self.assertIn(raw_key, list(self._initial(cache_alias).keys()))
        self.assertNotEqual(current_value, None)

    def assertPointerKeyInvalidated(self, key, version=None, cache_alias=None):
        cache = get_cache(cache_alias) if cache_alias else self.cache
        raw_key = cache.make_key(key, version=version)
        current_value = cache.get(key, version=version)
        self.assertIn(raw_key, list(self._initial(cache_alias).keys()))
        self.assertEqual(current_value, 0)

    def assertPointerKeyNotInvalidated(self, key, version=None, cache_alias=None):
        cache = get_cache(cache_alias) if cache_alias else self.cache
        raw_key = cache.make_key(key, version=version)
        current_value = cache.get(key, version=version)
        self.assertIn(raw_key, list(self._initial(cache_alias).keys()))
        self.assertNotEqual(current_value, 0)


class LiveServerTestCase(test.LiveServerTestCase, TestCase):
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
