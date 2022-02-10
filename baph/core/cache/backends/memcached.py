from __future__ import absolute_import
import time

from django.core.cache.backends.memcached import MemcachedCache


class BaphMemcachedCache(MemcachedCache):
    """
    An extension of the django memcached Cache class
    """
    def __init__(self, server, params):
        super(BaphMemcachedCache, self).__init__(server, params)
        self.version = params.get('VERSION', 0)

    def delete_many_raw(self, keys):
        """
        Deletes the specified keys (does not run them through make_key)
        """
        self._cache.delete_multi(keys)

    def flush_all(self):
        for s in self._cache.servers:
            if not s.connect(): continue
            s.send_cmd('flush_all')
            s.expect("OK")
            self.delete_many_raw(self.get_server_keys(s))

    def get_all_keys(self):
        keys = set()
        for s in self._cache.servers:
            keys.update(self.get_server_keys(s))
        return keys

    def get_server_keys(self, s):
        keys = set()
        slab_ids = self.get_server_slab_ids(s)
        for slab_id in slab_ids:
            keys.update(self.get_slab_keys(s, slab_id))
        return keys

    def get_slab_keys(self, s, slab_id):
        keys = set()
        s.send_cmd('stats cachedump %s 100' % slab_id)
        readline = s.readline
        ts = time.time()
        while 1:
            line = readline()
            if not line or line.strip() == 'END': break
            frags = line.split(' ')
            key = frags[1]
            expire = int(frags[4])
            if expire > ts:
                keys.add(key)
        return keys

    def get_server_slab_ids(self, s):
        if not s.connect():
            return set()
        slab_ids = set()
        s.send_cmd('stats items')
        readline = s.readline
        while 1:
            line = readline()
            if not line or line.strip() == 'END': break
            frags = line.split(':')
            slab_ids.add(frags[1])
        return slab_ids
