import os
import sys

from django.core.cache import get_cache
from MySQLdb.converters import conversions, escape
from sqlalchemy import inspect
from sqlalchemy import *
from sqlalchemy.exc import ResourceClosedError
from sqlalchemy.orm import lazyload, contains_eager, class_mapper
from sqlalchemy.orm.util import identity_key
from sqlalchemy.sql import compiler

from baph.core.management.base import NoArgsCommand
from baph.db.orm import ORM


orm = ORM.get()
Base = orm.Base

def get_namespaced_models():
    nsmap = {}
    for k,v in Base._decl_class_registry.items():
        if k.startswith('_'):
            # skip internal SA attrs
            continue
        ns = v().get_cache_namespaces()
        if not ns:
            continue
        for k2, v2 in ns:
            # prefix with the cache name
            k2 = '%s:%s' % (v._meta.cache_alias, k2)
            if k2 not in nsmap:
                nsmap[k2] = set()
            nsmap[k2].add(k)
    return nsmap

def print_ns_keys(ns_models):
    """ prints available namespace keys to the terminal """
    print '\nidx\tcache_alias:nskey'
    for i, (key, models) in enumerate(ns_models.items()):
        print '%d\t%s (triggers reloads on %s)' % (i, key, ', '.join(models))


class Command(NoArgsCommand):
    requires_model_validation = True

    def handle_noargs(self, **options):
        ns_models = get_namespaced_models()
        print_ns_keys(ns_models)
        while True:
            cmd = raw_input('\nIncrement which ns key? (ENTER to list, Q to quit): ').strip()
            if cmd in ('q', 'Q'):
                # quit
                break

            if not cmd:
                # list ns keys
                print_ns_keys(ns_models)
                continue            

            if cmd.isdigit():
                # numeric index
                if int(cmd) >= len(ns_models):
                    print 'Invalid index: %s' % cmd
                    continue
                cmd, models = ns_models.items()[int(cmd)]
            elif not cmd in ns_models:
                print 'Invalid ns key: %s' % cmd
                continue

            cache_alias, key = cmd.split(':', 1)
            cache = get_cache(cache_alias)

            while True:
                cmd = raw_input('Enter the value for "%s" (ENTER to cancel): ' % key).strip()
                if not cmd:
                    break
               
                version_key = '%s_%s' % (key, cmd)
                version = cache.get(version_key)
                print '\tcurrent value of %s: %s' % (version_key, version)
                if version is None:
                    version = 0
                version += 1
                cache.set(version_key, version)
                version = cache.get(version_key)
                print '\tnew value of %s: %s' % (version_key, version)

