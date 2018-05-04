from collections import defaultdict
import json
import os
import sys

from django.core.cache import get_cache
from django.utils.termcolors import make_style
from MySQLdb.converters import conversions, escape
from sqlalchemy import inspect
from sqlalchemy import *
from sqlalchemy.exc import ResourceClosedError
from sqlalchemy.orm import lazyload, contains_eager, class_mapper
from sqlalchemy.sql import compiler

from baph.core.management.base import BaseCommand #NoArgsCommand
from baph.db.orm import ORM


success_msg = make_style(fg='green')
notice_msg = make_style(fg='yellow')
error_msg = make_style(fg='red')
info_msg = make_style(fg='blue')

orm = ORM.get()
Base = orm.Base

def get_cacheable_models():
    for k,v in sorted(Base._decl_class_registry.items()):
        if k.startswith('_'):
            # skip internal SA attrs
            continue
        if v._meta.cache_detail_fields:
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

def prompt_for_model_name():
    while True:
        cmd = raw_input('\nKill cache for which model? '
                        '(ENTER to list, Q to quit): ')
        if cmd in ('q', 'Q'):
            return None
        if not cmd:
            for name in get_cacheable_models():
                print '    %s' % name
            continue
        return cmd

def prompt_for_pk(model):
    print 'Enter the primary key components:'
    pk = []
    for col in class_mapper(model).primary_key:
        v = raw_input('    %s: ' % col.name)
        pk.append(v)
    return tuple(pk)

class Command(BaseCommand):
    requires_model_validation = True
    help = "Kills cache keys for baph models"
    args = "modelname [id id ...]"

    def handle(self, *args, **options):
        if len(args) > 0:
            model_name = args[0]
        else:
            model_name = None
        
        if len(args) > 1:
            pks = args[1:]
        else:
            pks = None

        print ''
        while True:
            if not model_name:
                model_name = prompt_for_model_name()
            if not model_name:
                # quit
                break
            if not model_name in Base._decl_class_registry:
                print error_msg('Invalid model name: %s' % model_name)
                model_name = None
                continue
            model = Base._decl_class_registry[model_name]

            if not pks:
                pk = prompt_for_pk(model)
                pks = [pk]
            
            session = orm.sessionmaker()
            for pk in pks:
                print info_msg('\nLooking up %r with pk=%s' % (model_name, pk))
                obj = session.query(model).get(pk)
                if not obj:
                    print error_msg('  No %s found with PK %s' % (model_name, pk))
                    continue

                print success_msg('  Found object: %r' % obj)

                caches = defaultdict(lambda: {
                    'cache_keys': set(),
                    'version_keys': set(),
                })
                cache_keys, version_keys = obj.get_cache_keys(
                    child_updated=True, force_expire_pointers=True)

                if cache_keys:
                    for alias, cache_key in cache_keys:
                        caches[alias]['cache_keys'].add(cache_key)

                if version_keys:
                    for alias, version_key in version_keys:
                        caches[alias]['version_keys'].add(version_key)

                for alias, keys in caches.items():
                    print info_msg('Processing keys on cache %r' % alias)
                    cache = get_cache(alias)
                    for key in keys['cache_keys']:
                        print '  Killing cache key: %r' % key
                    cache.delete_many(keys['cache_keys'])
                    for key in keys['version_keys']:
                        print '  Incrementing version key: %r' % key
                        cache.incr(key)

            model_name = None
            pks = None
