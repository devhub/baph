from collections import defaultdict
import json
import time

from django.conf import settings
from django.core.management import call_command
from django import test
from sqlalchemy import create_engine

from baph.db.orm import ORM
from .signals import add_timing


PRINT_TEST_TIMINGS = getattr(settings, 'PRINT_TEST_TIMINGS', False)

orm = ORM.get()

class BaphFixtureMixin(object):
    reset_sequences = False
    test_start_time = None
    test_end_time = None
    tests_run = 0
    timings = None

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
        orm.sessionmaker().expunge_all()
        cls.session.expunge_all()

    @classmethod
    def purge_fixtures(cls, *fixtures):
        orm.sessionmaker().expunge_all()
        cls.session.expunge_all()
        cls.session.rollback()
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

    @classmethod
    def tearDownClass(cls):
        super(BaphFixtureMixin, cls).tearDownClass()
        cls.session.close()
        if hasattr(cls, 'persistent_fixtures'):
            cls.purge_fixtures(*cls.persistent_fixtures)
        if PRINT_TEST_TIMINGS:
            add_timing.disconnect(cls.add_timing)
        cls.test_end_time = time.time()
        if PRINT_TEST_TIMINGS:
            cls.print_timings()

    def _fixture_setup(self):
        if hasattr(self, 'fixtures'):
            self.load_fixtures(*self.fixtures)

    def _fixture_teardown(self):
        if hasattr(self, 'fixtures'):
            self.purge_fixtures(*self.fixtures)

class MemcacheMixin(object):

    def populate_cache(self, objs=[]):
        """
        reads the current key/value pairs from the cache and
        stores it in self.initial_data, for comparison with post-test results
        """
        self.initial_cache = dict((k, self.cache.get(k)) \
            for k in self.cache.get_all_keys())

    def assertCacheHit(self, rsp):
        self.assertEqual(rsp['x-from-cache'], 'True')

    def assertCacheMiss(self, rsp):
        self.assertEqual(rsp['x-from-cache'], 'False')

    def assertCacheKeyEqual(self, key, value, version=None):
        self.assertEqual(self.cache.get(key, version=version), value)

    def assertCacheKeyCreated(self, key, version=None):
        raw_key = self.cache.make_key(key, version=version)
        self.assertNotIn(raw_key, self.initial_cache)
        self.assertIn(raw_key, self.cache.get_all_keys())

    def assertCacheKeyIncremented(self, key, version=None):
        raw_key = self.cache.make_key(key, version=version)
        old = self.initial_cache.get(raw_key, 0)
        new = self.cache.get(key)
        self.assertEqual(new, old+1)

    def assertCacheKeyIncrementedMulti(self, key, version=None):
        raw_key = self.cache.make_key(key, version=version)
        old = self.initial_cache[raw_key]
        new = self.cache.get(key)
        self.assertTrue(new > old)
        
    def assertCacheKeyInvalidated(self, key, version=None):
        raw_key = self.cache.make_key(key, version=version)
        self.assertIn(raw_key, self.initial_cache)
        self.assertEqual(self.cache.get(key), None)

    def assertCacheKeyNotInvalidated(self, key, version=None):
        raw_key = self.cache.make_key(key, version=version)
        self.assertIn(raw_key, self.initial_cache)
        self.assertNotEqual(self.cache.get(key), None)

class TestCase(BaphFixtureMixin, test.TestCase):
    pass


class LiveServerTestCase(BaphFixtureMixin, test.LiveServerTestCase):
    pass


class MemcacheTestCase(MemcacheMixin, TestCase):
    def _fixture_setup(self):
        super(MemcacheTestCase, self)._fixture_setup()
        self.cache.flush_all()

    def setUp(self, objs={}, counts={}):
        self.initial_cache = {}
        super(MemcacheTestCase, self).setUp()

class MemcacheLSTestCase(MemcacheMixin, LiveServerTestCase):
    def _fixture_setup(self):
        super(MemcacheLSTestCase, self)._fixture_setup()
        self.cache.flush_all()

    def setUp(self, objs={}, counts={}):
        self.initial_cache = {}
        super(MemcacheLSTestCase, self).setUp()


