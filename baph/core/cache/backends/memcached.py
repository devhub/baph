from collections import defaultdict
from functools import partial
import operator
import time

from django.core.cache.backends.memcached import MemcachedCache
from six.moves import map, reduce
from six.moves.urllib.parse import unquote


def parse_stats_line(line):
    # line format: STAT <key> <value>
    return (line[1], line[2])

def parse_metadump_line(line):
    # line format: <key>=<value>*
    split = operator.methodcaller('split', '=', 1)

    data = dict(list(map(split, line)))
    data['key'] = unquote(data['key'])
    return data

def parse_cachedump_line(line, **kwargs):
    data = dict(kwargs)
    key, metadata = line
    data['key'] = key #.encode('utf8')
    metadata = metadata[1:-1] # strip brackets
    for key in ('size', 'exp'):
        stat, sep, metadata = metadata.partition(';')
        value, unit = stat.strip().split(' ', 1)
        data[key] = int(value)
    return data

def parse_stats(response):
    """ parse the response of a stats command """
    return list(map(parse_stats_line, response))

def parse_slabs(response):
    slabs = defaultdict(dict)
    for key, value in response:
        # key format: items:<slab_id>:<key>
        _, slab_id, key = key.split(':', 2)
        slabs[slab_id][key] = value
    return slabs

def parse_slab_stats(response):
    slab_stats = defaultdict(dict)
    for key, value in parse_stats(response):
        # key format 1: <slab_id>:<key>
        # key format 2: <total_key>
        if ':' in key:
            slab_id, key = key.split(':')
        else:
            slab_id = 'totals'
        slab_stats[slab_id][key] = value
    return slab_stats

def parse_cachedump(response):
    return list(map(parse_cachedump_line, response))

def parse_metadump(response):
    return list(map(parse_metadump_line, response))


class MemcacheServer(object):
    def __init__(self, server):
        self.server = server
        self.settings = dict(self.get_stats('settings'))
        if self.settings.get('lru_crawler') == 'yes':
            self._get_keys = self.get_keys_from_metadump
        else:
            self._get_keys = self.get_keys_from_cachedump

    @property
    def slabs(self):
        return self.get_slabs()

    def send_command(self, cmd, row_len=0, expect=None):
        """
        send a command to the server, and returns a parsed response

        the response is a list of lines
        each line in the list is a list of space-delimited strings
        """
        if not self.server.connect():
            return
        self.server.send_cmd(cmd)
        if expect:
            self.server.expect(expect)
            return None
        lines = []
        while True:
            line = self.server.readline()
            if not line:
                break
            line = line.decode('ascii').strip()
            while line:
                # readline splits on '\r\n', we still need to split on '\n'
                item, sep, line = line.partition('\n')
                if item == 'END':
                    return lines
                else:
                    lines.append(item.split(' ', row_len-1))
        return lines

    # base commands

    def get_stats(self, *args):
        """ returns a list of (key, value) tuples for a stats command """
        cmd = ' '.join(('stats',) + args)
        rsp = self.send_command(cmd, 3)
        return parse_stats(rsp)

    def get_metadump(self, slab_id, limit):
        # metadump doesn't support a limit param, so we need to handle it
        limit = limit or None
        cmd = 'lru_crawler metadump %s' % slab_id
        rsp = self.send_command(cmd)
        return parse_metadump(rsp)[:limit]

    # STATS command variants

    def get_slabs(self):
        """ gets configuration settings for active slabs """
        rsp = self.get_stats('items')
        return parse_slabs(rsp)

    def get_slab_stats(self):
        """ gets statistics for active slabs """
        rsp = self.get_stats('slabs')
        return parse_slab_stats(rsp)

    def get_cachedump(self, slab_id, limit):
        limit = limit or 0
        cmd = 'cachedump %s %s' % (slab_id, limit)
        rsp = self.get_stats(cmd)
        return parse_cachedump(rsp)

    # other commands

    def get_keys_from_metadump(self, limit=None):
        """ returns all keys on the server using 'lru_crawler metadump' """
        return self.get_metadump('all', limit)

    def get_keys_from_cachedump(self, limit=None):
        """ returns all keys on the server using 'stats cachedump' """
        func = partial(self.get_cachedump, limit=limit)
        if self.slabs:
            return reduce(operator.concat, list(map(func, self.slabs)))
        return []

    def get_keys(self, limit=None, include_expired=False):
        """ returns all keys on the server, as a list of strings """
        getter = operator.itemgetter('key')
        ts = time.time()
        items = self._get_keys(limit)
        if not include_expired:
            items = filter(lambda x: float(x['exp']) > ts, items)
        return list(map(getter, items))


class BaphMemcachedCache(MemcachedCache):
    """ An extension of the django memcached Cache class """
    def __init__(self, server, params):
        super(BaphMemcachedCache, self).__init__(server, params)
        self.version = params.get('VERSION', 0)
        self.alias = params.get('ALIAS', None)
        self.servers = [MemcacheServer(s) for s in self._cache.servers]

    def get_all_keys(self):
        keys = set()
        for server in self.servers:
            try:
                del server.slabs
            except AttributeError:
                pass
            keys.update(server.get_keys())
        return keys

    def flush_all(self):
        self.clear()
