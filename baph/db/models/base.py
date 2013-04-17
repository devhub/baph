from collections import defaultdict
import re

from django.conf import settings
from django.core.cache import get_cache
from sqlalchemy import event, Column, inspect
from sqlalchemy.ext.associationproxy import AssociationProxy, ASSOCIATION_PROXY
from sqlalchemy.ext.declarative import (declarative_base, declared_attr,
    DeclarativeMeta)
from sqlalchemy.ext.hybrid import HYBRID_PROPERTY, HYBRID_METHOD, hybrid_property
from sqlalchemy.orm import mapper, object_session, configure_mappers
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.attributes import instance_dict, get_history
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.util import has_identity, identity_key
from sqlalchemy.util import OrderedDict

from .options import Options

# these keys auto-update, so should be ignored when comparing old/new values
IGNORABLE_KEYS = (
    'modified',
    'last_modified',
    )

def creator_factory(merge_class, key):
    def creator(x):
        return merge_class(**{key:x})
    return creator

def constructor(self, **kwargs):
    cls = type(self)
    # auto-populate default values on init
    for col in cls.__table__.c:
        if col.default is not None:
            if callable(col.default.arg):
                setattr(self, col.key, col.default.arg({}))
            else:
                setattr(self, col.key, col.default.arg)
    # now load in the kwargs values
    for k in kwargs:
        if not hasattr(cls, k):
            raise TypeError('%r is an invalid keyword argument for %s' %
                (k, cls.__name__))
        setattr(self, k, kwargs[k])

@event.listens_for(mapper, 'mapper_configured')
def set_polymorphic_base_mapper(mapper_, class_):
    if mapper_.polymorphic_on is not None:
        polymorphic_map = defaultdict(lambda: mapper_)
        polymorphic_map.update(mapper_.polymorphic_map)
        mapper_.polymorphic_map = polymorphic_map

class Model(object):

    @classmethod
    def create(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    def permission_context(self, request):
        return {
            'user_id': request.user.id,
            'user_whitelabel': request.user.whitelabel,
            }

    def update(self, data):
        for key, value in data.iteritems():
            if hasattr(self, key) and getattr(self, key) != value:
                setattr(self, key, value)       

    def format_key(self, key):
        # if we need to coerce the key for insertion, do it here
        key = key.replace('/','_')
            
        cache = get_cache('objects')
        ns = []
        for k,v in self.get_cache_namespaces():
            version_key = '%s_%s' % (k,v)
            version = cache.get(version_key)
            if version is None:
                version = 1
                cache.set(version_key, version)
            ns.append('%s_%s' % (version_key, version))
        if not ns:
            return key
        #print '%s:%s' % (':'.join(ns), key)
        return '%s:%s' % (':'.join(ns), key)

    def get_cache_namespaces(self):
        return []

    @property
    def is_deleted(self):
        return False

    @property
    def cache_version_keys(self):
        keys = []
        for ns in self.get_cache_namespaces():
            keys.append('%s_%s' % ns)
        return keys

    @property
    def cache_detail_key(self, data=None):
        if not hasattr(self._meta, 'cache_detail_keys'):
            raise Exception('Class meta has no cache_detail_keys')
        if not has_identity(self):
            raise Exception('Cannot generate detail cache key for instance ' \
                'with no identity')
        data = data or instance_dict(self)
        raw_key, attrs = self._meta.cache_detail_keys[0]
        return self.format_key(raw_key % data)

    def cache_pointers(self, data=None, columns=[]):
        if not hasattr(self._meta, 'cache_pointers'):
            return {}
        data = data or instance_dict(self)
        keys = {}
        for raw_key, attrs, name in self._meta.cache_pointers:
            if columns and not any(c in attrs for c in columns):
                continue
            keys[name] = raw_key % data
        return keys

    @property
    def cache_list_version_key(self, data=None):
        if not self._meta.cache_list_keys:
            raise Exception('Class._meta has no cache_list_keys')
        if not has_identity(self):
            raise Exception('Cannot generate list cache key for instance ' \
                'with no identity')
        data = data or instance_dict(self)
        raw_key, attrs = self._meta.cache_list_keys[0]
        return raw_key % data

    def cache_list_key(self, **kwargs):
        cache = get_cache('objects')
        version_key = self.cache_list_version_key
        version = cache.get(version_key)
        if not version:
            version = 1
            cache.set(version_key, version)
        cache_key = '%s_%s' % (version_key, version)
        if not 'limit' in kwargs:
            kwargs['limit'] = self._meta.limit
        if not 'offset' in kwargs:
            kwargs['offset'] = 0
        filters = []
        for key, value in sorted(kwargs.items()):
            filters.append("%s=%s" % (key, value))
        cache_key = '%s:%s' % (cache_key, ':'.join(filters))
        return self.format_key(cache_key)
        

    def get_cache_keys(self, child_updated=False):
        cache_keys = set()
        version_keys = set()

        if not any(getattr(self._meta, k) for k in [
            'cache_detail_keys',
            'cache_list_keys',
            'cache_pointers',
            'cache_cascades',
            'cache_relations',
            ]):
            return cache_keys, version_keys
            
        session = Session.object_session(self)
        deleted = self in session.deleted
        data = instance_dict(self)
        cache = get_cache('objects')

        # get a list of all fields which changed
        changed_keys = []
        for attr in self.__mapper__.iterate_properties:
            if not isinstance(attr, ColumnProperty) and \
               attr.key not in self._meta.cache_relations:
                continue
            if attr.key in IGNORABLE_KEYS:
                continue
            ins, eq, rm = get_history(self, attr.key)
            if ins or rm:
                changed_keys.append(attr.key)
        self_updated = bool(changed_keys) or deleted

        #print '\tself_updated:', self_updated, changed_keys
        #print '\tchild_updated:', child_updated

        if not self_updated and not child_updated:
            return (cache_keys, version_keys)

        if has_identity(self):
            # we only kill primary cache keys if the object exists
            # this key won't exist during CREATE
            for raw_key, attrs in self._meta.cache_detail_keys:
                if attrs and not any(key in changed_keys for key in attrs):
                    # the fields which trigger this key were not changed
                    continue
                cache_key = self.format_key(raw_key % data)
                cache_keys.add(cache_key)

        # collections will be altered by any action, so we always
        # kill these keys
        for raw_key, attrs in self._meta.cache_list_keys:
            if attrs and not any(key in changed_keys for key in attrs):
                # the fields which trigger this key were not changed
                continue
            cache_key = raw_key % data
            version_keys.add(cache_key)

        # pointer records contain only the id of the parent resource
        # if changed, we set the old key to False, and set the new key
        for raw_key, attrs, name in self._meta.cache_pointers:
            if attrs and not any(key in changed_keys for key in attrs):
                # the fields which trigger this key were not changed
                continue
            cache_key = raw_key % data
            c, idkey = identity_key(instance=self)
            if len(idkey) > 1:
                idkey = ','.join(str(i) for i in idkey)
            else:
                idkey = idkey[0]
            if not self.is_deleted:
                cache.set(cache_key, idkey)

            # if this is an existing object, we need to handle the old key
            if not has_identity(self):
                continue

            old_data = {}
            for attr in attrs:
                ins,eq,rm = get_history(self, attr)
                old_data[attr] = rm[0] if rm else eq[0]
            old_key = raw_key % old_data
            if old_key == cache_key and not self.is_deleted:
                continue
            old_idkey = cache.get(old_key)
            if old_idkey == idkey:
                # this object is the current owner of the key
                #print 'setting %s to False' % old_key, old_idkey, idkey
                cache.set(old_key, False)

        # cascade the cache kill operation to related objects, so parents
        # know if children have changed, in order to rebuild the cache
        for cascade in self._meta.cache_cascades:
            objs = getattr(self, cascade)
            if not objs:
                continue
            if not isinstance(objs, list):
                objs = [objs]
            for obj in objs:
                k1,k2 = obj.get_cache_keys(child_updated=True)
                cache_keys.update(k1)
                version_keys.update(k2)

        return (cache_keys, version_keys)

    def kill_cache(self):
        cache_keys, version_keys = self.get_cache_keys()
        if not cache_keys and not version_keys:
            return

        if settings.DEBUG:
            print '\nkill_cache called for', self
            for key in cache_keys:
                print '\tcache_key:', key
            for key in version_keys:
                print '\tversion_key:', key

        cache = get_cache('objects')
        cache.delete_many(cache_keys)
        for key in version_keys:
            v = cache.get(key)
            if not v:
                cache.set(key, 1)
            else:
                cache.incr(key)

class ModelBase(DeclarativeMeta):

    def __new__(cls, name, bases, attrs):
        super_new = super(ModelBase, cls).__new__
        new_class = super_new(cls, name, bases, attrs)
        attr_meta = attrs.pop('Meta', None)
        if not attr_meta:
            meta = getattr(new_class, 'Meta', None)
        else:
            meta = attr_meta
        base_meta = getattr(new_class, '_meta', None)
        new_class.add_to_class('_meta', Options(meta))
        return new_class

    def add_to_class(cls, name, value):
        if hasattr(value, 'contribute_to_class'):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)

    def get_prop_from_proxy(cls, proxy):
        if proxy.scalar:
            # column
            col = proxy.remote_attr.property.columns
            data_type = type(col[0].type)
            prop = proxy.remote_attr.property
        elif proxy.remote_attr.extension_type == ASSOCIATION_PROXY:
            prop = cls.get_prop_from_proxy(proxy.remote_attr)
        elif isinstance(proxy.remote_attr.property, RelationshipProperty):
            data_type = proxy.remote_attr.property.collection_class or object
            readonly = proxy.remote_attr.info.get('readonly', False)
            prop = proxy.remote_attr.property
        else:
            col = proxy.remote_attr.property.columns
            data_type = type(col[0].type)
            prop = proxy.remote_attr.property
        return prop

    @property
    def all_properties(cls):
        if not cls.__mapper__.configured:
            configure_mappers()
        for key, attr in inspect(cls).all_orm_descriptors.items():
            if attr.is_mapper:
                continue
            elif attr.extension_type == HYBRID_METHOD:
                # not a property
                continue
            elif attr.extension_type == HYBRID_PROPERTY:
                data_type = type(attr.expr(cls).type)
                readonly = not attr.fset
                prop = attr
            elif attr.extension_type == ASSOCIATION_PROXY:
                proxy = getattr(cls, key)
                prop = cls.get_prop_from_proxy(proxy)
            elif isinstance(attr.property, ColumnProperty):
                data_type = type(attr.property.columns[0].type)
                readonly = attr.info.get('readonly', False)
                prop = attr.property
            elif isinstance(attr.property, RelationshipProperty):
                data_type = attr.property.collection_class or object
                readonly = attr.info.get('readonly', False)
                prop = attr.property
            yield (key, prop)


Base = declarative_base(cls=Model, 
    metaclass=ModelBase,
    constructor=constructor)


if getattr(settings, 'CACHE_ENABLED', False):
    @event.listens_for(mapper, 'after_insert')
    @event.listens_for(mapper, 'after_update')
    @event.listens_for(mapper, 'after_delete')
    def kill_cache(mapper, connection, target):
        target.kill_cache()
