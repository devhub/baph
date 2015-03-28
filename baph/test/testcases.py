try:
    import json
except:
    import simplejson as json
import time

from django.core.management import call_command
from django.test import TestCase as DjangoTestCase
from django.test import LiveServerTestCase as DjangoLSTestCase

from baph.db.orm import ORM

orm = ORM.get()


class BaphFixtureMixin(object):

    reset_sequences = False

    def _fixture_setup(self):
        if hasattr(self, 'fixtures'):
            params = {
                'verbosity': 0,
                'database': None, 
                'skip_validation': True,
                'commit': False,
                }
            call_command('loaddata', *self.fixtures, **params)
        session = orm.sessionmaker()
        session.expunge_all()

    def _fixture_teardown(self):
        if hasattr(self, 'fixtures'):
            session = orm.sessionmaker()
            session.expunge_all()
            #session.rollback() #requires transactional db
            params = {
                'verbosity': 0,
                'interactive': False,
                }
                
            call_command('flush', **params)

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

    def assertCacheKeyEqual(self, key, value):
        self.assertEqual(self.cache.get(key), value)

    def assertCacheKeyCreated(self, key):
        raw_key = self.cache.make_key(key)
        self.assertNotIn(raw_key, self.initial_cache)
        self.assertIn(raw_key, self.cache.get_all_keys())

    def assertCacheKeyIncremented(self, key):
        raw_key = self.cache.make_key(key)
        old = self.initial_cache.get(raw_key, 0)
        new = self.cache.get(key)
        self.assertEqual(new, old+1)

    def assertCacheKeyIncrementedMulti(self, key):
        raw_key = self.cache.make_key(key)
        old = self.initial_cache[raw_key]
        new = self.cache.get(key)
        self.assertTrue(new > old)
        
    def assertCacheKeyInvalidated(self, key):
        raw_key = self.cache.make_key(key)
        self.assertIn(raw_key, self.initial_cache)
        self.assertEqual(self.cache.get(key), None)

    def assertCacheKeyNotInvalidated(self, key):
        raw_key = self.cache.make_key(key)
        self.assertIn(raw_key, self.initial_cache)
        self.assertNotEqual(self.cache.get(key), None)

class TestCase(BaphFixtureMixin, DjangoTestCase):
    pass


class LiveServerTestCase(BaphFixtureMixin, DjangoLSTestCase):
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


