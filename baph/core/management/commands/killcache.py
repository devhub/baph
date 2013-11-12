import json
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

def get_cacheable_models():
    for k,v in Base._decl_class_registry.items():
        if k.startswith('_'):
            # skip internal SA attrs
            continue
        if v._meta.cache_detail_keys:
            yield k

def lookup_model():
    name = raw_input('Enter model name ("L" to list): ')
    name = name.lower()
    for k,v in Base._decl_class_registry.items():
        if k.startswith('_'):
            continue
        if name == 'l':
            print '\t%s' % k, v._meta.cache_detail_keys
        if name == k.lower():
            return v
    if name != 'l':
        print 'Invalid choice: %s' % name

class Command(NoArgsCommand):
    requires_model_validation = True

    def handle_noargs(self, **options):
        while True:
            cmd = raw_input('\nKill cache for which model? (ENTER to list, Q to quit): ')
            if not cmd:
                for name in get_cacheable_models():
                    print '    %s' % name
                continue
            if cmd in ('q', 'Q'):
                break
            if not cmd in Base._decl_class_registry:
                print 'Invalid model name: %s' % cmd
                continue
            cls = Base._decl_class_registry[cmd]

            print 'Enter the primary key components:'
            pk = []
            for col in class_mapper(cls).primary_key:
                v = raw_input('    %s: ' % col.name)
                pk.append(v)
            pk = tuple(pk)

            session = orm.sessionmaker()
            obj = session.query(cls).get(pk)
            if not obj:
                print 'No %s found with PK %s' % (cmd, pk)
                continue

            print 'found object:', obj
            cache_keys, version_keys = obj.get_cache_keys(child_updated=True,
                                                  force_expire_pointers=True)

            cache = get_cache('objects')
            if cache_keys:
                print 'Killing cache keys:'
                for k in cache_keys:
                    print '    %s' % k
                cache.delete_many(cache_keys)

            if version_keys:
                print 'incrementing version keys:'
                for k in version_keys:
                    print '    %s' % k
                    cache.incr(k)
