import datetime

from django.conf import settings
from django.core.cache import get_cache
from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.attributes import get_history, instance_dict
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.util import has_identity, identity_key

from baph.db import Session


# these keys auto-update, so should be ignored when comparing old/new values
IGNORABLE_KEYS = (
    'modified',
    'last_modified',
    'added',
    )

class TimestampMixin(object):

    @declared_attr
    def added(cls):
        return Column(DateTime, default=datetime.datetime.now,
            info={'readonly': True})

    @declared_attr
    def modified(cls):
        return Column(DateTime, default=datetime.datetime.now,
            onupdate=datetime.datetime.now, info={'readonly': True})

class CacheMixin(object):

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
        #print 'getting keys from', self
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
        deleted = self.is_deleted or self in session.deleted
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

        #print '\nself:', self
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

    def kill_cache(self, force=False):
        cache_keys, version_keys = self.get_cache_keys(child_updated=force)
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
