import json
import os
import sys

from MySQLdb.converters import conversions, escape
from sqlalchemy import inspect
from sqlalchemy import *
from sqlalchemy.exc import ResourceClosedError
from sqlalchemy.orm import lazyload, contains_eager, class_mapper
from sqlalchemy.orm.util import identity_key
from sqlalchemy.sql import compiler

from baph.core.management.base import BaseCommand #NoArgsCommand
from baph.db.orm import ORM


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

        while True:
            if not model_name:
                model_name = prompt_for_model_name()
            if not model_name:
                # quit
                break
            if not model_name in Base._decl_class_registry:
                print 'Invalid model name: %s' % model_name
                model_name = None
                continue
            model = Base._decl_class_registry[model_name]

            if not pks:
                pk = prompt_for_pk(model)
                pks = [pk]
            
            session = orm.sessionmaker()
            for pk in pks:
                obj = session.query(model).get(pk)
                if not obj:
                    print '\nNo %s found with PK %s' % (model_name, pk)
                    continue

                print '\nFound object:', obj
                cache = obj.get_cache()
                cache_keys, version_keys = obj.get_cache_keys(
                    child_updated=True, force_expire_pointers=True)

                if cache_keys:
                    print '  Killing cache keys:'
                    for k in cache_keys:
                        print '    %s' % k
                    cache.delete_many(cache_keys)

                if version_keys:
                    print '  Incrementing version keys:'
                    for k in version_keys:
                        print '    %s' % k
                        cache.incr(k)

            model_name = None
            pks = None
