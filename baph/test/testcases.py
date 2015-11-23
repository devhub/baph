import json
import time

from django.core.management import call_command
from django import test
from sqlalchemy import create_engine

from baph.db.orm import ORM


orm = ORM.get()

class BaphFixtureMixin(object):

    reset_sequences = False

    @classmethod
    def load_fixtures(cls, *fixtures):
        params = {
            'verbosity': 0,
            'database': None,
            'skip_validation': True,
            'commit': False,
            }
        call_command('loaddata', *fixtures, **params)
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
        call_command('flush', **params)

    @classmethod
    def setUpClass(cls):
        super(BaphFixtureMixin, cls).setUpClass()
        cls.session = orm.session_factory()
        if hasattr(cls, 'persistent_fixtures'):
            cls.load_fixtures(*cls.persistent_fixtures)

    @classmethod
    def tearDownClass(cls):
        super(BaphFixtureMixin, cls).tearDownClass()
        cls.session.close()
        if hasattr(cls, 'persistent_fixtures'):
            cls.purge_fixtures(*cls.persistent_fixtures)

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


