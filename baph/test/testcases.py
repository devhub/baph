try:
    import json
except:
    import simplejson as json
import time

from django.core.management import call_command
from tastypie.test import ResourceTestCase

from baph.db.orm import ORM


orm = ORM.get()

def generate_debug_cache(count=0):
    return json.dumps({
        'meta': {'total_count': count},
        'objects': count * '*',
        })

class TestCase(ResourceTestCase):

    reset_sequences = False

    def create_oauth(self, key):
        """
        Creates & returns the HTTP ``Authorization`` header for use with Oauth.
        """
        oauth_data = {
            'oauth_consumer_key': key,
            'oauth_nonce': 'abc',
            'oauth_signature': '&',
            'oauth_signature_method': 'PLAINTEXT',
            'oauth_timestamp': str(int(time.time())),
        }
        return 'OAuth %s' % ','.join([key+'='+value for key, value in \
            oauth_data.items()])

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
            #session = orm.sessionmaker()
            #session.rollback() #requires transactional db
            params = {
                'verbosity': 0,
                'interactive': False,
                }
            call_command('flush', **params)
            
class MemcacheTestCase(TestCase):
    
    def _fixture_setup(self):
        super(MemcacheTestCase, self)._fixture_setup()
        self.cache.flush_all()

    def populate_aliases(self):
        for name, obj in self.objs.items():
            for name2, cache_key in obj.cache_pointers().items():
                alias = '%s_%s' % (name, name2)
                self.aliases[alias] = cache_key
            
            if obj._meta.cache_detail_keys:
                cache_key = obj.cache_detail_key
                alias = '%s_detail' % name
                self.aliases[alias] = cache_key

            if obj._meta.cache_list_keys:
                version_key = obj.cache_list_version_key
                alias = '%s_list_version' % name
                self.aliases[alias] = version_key
                
                cache_key = obj.cache_list_key()
                alias = '%s_list' % name
                self.aliases[alias] = cache_key

    def populate_cache(self, objs=[]):
        cache_values = {}

        for name in objs:
            obj = self.objs[name]

            for key in obj.cache_version_keys:
                cache_values[key] = 1

            for name2, key in obj.cache_pointers().items():
                alias = '%s_%s' % (name, name2)
                cache_values[alias] = obj.id

            if obj._meta.cache_detail_keys:
                alias = '%s_detail' % name
                cache_values[alias] = '"TEST"'

            if obj._meta.cache_list_keys:
                alias = '%s_list_version' % name
                cache_values[alias] = 1
                
                alias = '%s_list' % name
                cache_values[alias] = generate_debug_cache(self.counts[name])

        initial_data = dict((self.aliases.get(k,k),v) 
            for k,v in cache_values.items())
        for key, value in initial_data.items():
            self.cache.set(key, value)

        self.initial_cache = dict((k, self.cache.get(k)) \
            for k in self.cache.get_all_keys())

    def setUp(self, objs={}, counts={}):
        self.aliases = {}
        self.initial_cache = {}
        self.objs = objs
        self.counts = counts
        self.populate_aliases()
        super(MemcacheTestCase, self).setUp()

    def assertCacheKeyEqual(self, alias, value):
        cache_key = self.aliases[alias]
        self.assertEqual(self.cache.get(cache_key), value)

    def assertCacheRawKeyEqual(self, cache_key, value):
        self.assertEqual(self.cache.get(cache_key), value)

    def assertCacheKeyCreated(self, alias):
        cache_key = self.aliases[alias]
        self.assertNotIn(cache_key, self.initial_cache)
        self.assertIn(cache_key, self.cache.get_all_keys())

    def assertCacheKeyIncremented(self, alias):
        cache_key = self.aliases[alias]
        old = self.initial_cache[cache_key]
        new = self.cache.get(cache_key)
        self.assertEqual(new, old+1)
        
    def assertCacheKeyInvalidated(self, alias):
        cache_key = self.aliases[alias]
        self.assertIn(cache_key, self.initial_cache)
        self.assertEqual(self.cache.get(cache_key), None)

    def assertCacheKeyNotInvalidated(self, alias):
        cache_key = self.aliases[alias]
        self.assertIn(cache_key, self.initial_cache)
        self.assertNotEqual(self.cache.get(cache_key), None)

    def assertCachedDetailResponse(self, data):
        self.assertEqual(data, 'TEST')

    def assertCachedListResponse(self, data):
        self.assertTrue(isinstance(data['objects'], basestring))
        
    def assertNotCachedDetailResponse(self, data):
        self.assertTrue(isinstance(data, dict))
        
    def assertNotCachedListResponse(self, data):
        self.assertFalse(isinstance(data['objects'], basestring))
