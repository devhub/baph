import datetime
import logging
import time
import types

from django.conf import settings
from django.core.cache import get_cache
from sqlalchemy import Column, DateTime, func, inspect
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.declarative.clsregistry import _class_resolver
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.attributes import get_history, instance_dict
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.util import has_identity, identity_key

from baph.db import ORM
from .utils import column_to_attr, class_resolver


cache_logger = logging.getLogger('cache')

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

class GlobalMixin(object):

    def globalize(self, commit=True):
        """
        Converts object into a global by creating an instance of 
        Meta.global_class with the same identity key.
        """
        from baph.db.orm import ORM
        orm = ORM.get()

        if not self._meta.global_column:
            raise Exception('You cannot globalize a class with no value '
                'for Meta.global_column')

        # TODO: delete polymorphic extension, leave only the base

        setattr(self, self._meta.global_column, True)

        # handle meta.global_cascades
        for field in self._meta.global_cascades:
            value = getattr(self, field, None)
            if not value:
                continue
            if isinstance(value, orm.Base):
                # single object
                value.globalize(commit=False)
            elif hasattr(value, 'iteritems'):
                # dict-like collection
                for obj in value.values():
                    obj.globalize(commit=False)
            elif hasattr(value, '__iter__'):
                # list-like collection
                for obj in value:
                    obj.globalize(commit=False)
       
        if commit:
            session = orm.sessionmaker()
            session.add(self)
            session.commit()

    def is_globalized(self):
        if self._meta.global_column == 'is_globalized':
            raise Exception('global_column name conflicts with existing '
                'attribute "is_globalized()"')
        return getattr(self, self._meta.global_column)

class CacheMixin(object):

    @classmethod
    def get_cache(cls):
        """
        Returns the cache associated with this model, based on the value
        of meta.cache_alias
        """
        return get_cache(cls._meta.cache_alias)

    @classmethod
    def get_cache_namespaces(cls, instance=None):
        return []

    @property
    def cache_namespaces(self):
        return self.get_cache_namespaces(instance=self)

    @classmethod
    def build_cache_key(cls, mode, **kwargs):
        """
        Generates a cache key for the provided mode and the given kwargs
        mode is one of ['list', 'detail', or 'list_version']
        if mode is detail, cache_detail_fields must be defined in the cls meta
        if mode is list or list_version, cache_list_fields must be in the cls meta
        the associated fields must all be present in kwargs
        """
        if mode not in ('detail', 'list', 'list_version'):
            raise Exception('Invalid mode "%s" for build_cache_key. '
                'Valid modes are "detail", "list", and "list_version")')

        _mode = 'list' if mode == 'list_version' else mode
        fields = getattr(cls._meta, 'cache_%s_fields' % _mode, None)
        if not fields:
            raise Exception('cache_%s_fields is empty or undefined' % _mode)

        cache = cls.get_cache()
        cache_pieces = []
        cache_pieces.append(cls._meta.base_model_name_plural)
        cache_pieces.append(_mode)

        for key in sorted(fields):
            # all associated fields must be present in kwargs
            if not key in kwargs:
                raise Exception('%s is undefined' % key)
            cache_pieces.append('%s=%s' % (key, kwargs.pop(key)))

        version_key = ':'.join(cache_pieces)

        if mode == 'list_version':
            return version_key

        ns_pieces = []
        for key, value in sorted(cls.get_cache_namespaces()):
            ns_key = '%s_%s' % (key, value)
            version = cache.get(ns_key)
            if version is None:
                version = int(time.time())
                cache.set(ns_key, version)
            ns_pieces.append('%s_%s' % (ns_key, version))

            #cache_pieces.insert(0, '%s_%s' % (ns_key, version))

        if mode == 'detail':
            cache_key = ':'.join(ns_pieces + cache_pieces)
            return cache_key

        # treat list keys as version keys, so we can invalidate
        # multiple subsets (filters, pagination, etc) at once
        version = cache.get(version_key)
        if version is None:
            version = int(time.time())
            cache.set(version_key, version)
        cache_key = '%s_%s' % (version_key, version)

        filters = []
        for key, value in sorted(kwargs.items()):
            filters.append('%s=%s' % (key, value))

        cache_key = ':'.join(ns_pieces + [cache_key] + filters)

        return cache_key

    @property
    def cache_key(self):
        """
        Instance property which returns the cache key for a single object
        """
        if not has_identity(self):
            raise Exception('This instance has no identity')
        if not hasattr(self._meta, 'cache_detail_fields'):
            raise Exception('Meta.cache_detail_fields is undefined')
        data = dict((k, getattr(self, k)) for k in self._meta.cache_detail_fields)
        return self.build_cache_key('detail', **data)

    @property
    def cache_list_version_key(self):
        """
        Instance property which returns the cache list version key for a single object
        """
        if not hasattr(self._meta, 'cache_list_fields'):
            raise Exception('Meta.cache_list_fields is undefined')
        data = dict((k, getattr(self, k)) for k in self._meta.cache_list_fields)
        return self.build_cache_key('list_version', **data)

    @property
    def cache_list_key(self):
        """
        Instance property which returns the cache list key for a single object
        """
        if not hasattr(self._meta, 'cache_list_fields'):
            raise Exception('Meta.cache_list_fields is undefined')
        data = dict((k, getattr(self, k)) for k in self._meta.cache_list_fields)
        return self.build_cache_key('list', **data)

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
    def cache_pointer_keys(self):
        if not hasattr(self._meta, 'cache_pointers'):
            raise Exception('Meta.cache_pointers is undefined')
        return self.cache_pointers()

    def get_cache_keys(self, child_updated=False, force_expire_pointers=False):
        #print 'getting cache keys for:', self, 'child_updated=', child_updated
        cache_keys = set()
        version_keys = set()

        if not any(getattr(self._meta, k) for k in [
            'cache_detail_fields',
            'cache_list_fields',
            'cache_pointers',
            'cache_cascades',
            'cache_relations',
            ]):
            return cache_keys, version_keys

        orm = ORM.get()
        session = orm.sessionmaker()
        deleted = self.is_deleted or self in session.deleted
        data = instance_dict(self)
        cache = self.get_cache()

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

        if not self_updated and not child_updated:
            return (cache_keys, version_keys)

        if self._meta.cache_detail_fields:
            if has_identity(self):
                # we only kill primary cache keys if the object exists
                # this key won't exist during CREATE
                cache_key = self.cache_key
                cache_keys.add(cache_key)

        if self._meta.cache_list_fields:
            # collections will be altered by any action, so we always
            # kill these keys
            cache_key = self.cache_list_version_key
            version_keys.add(cache_key)

        # pointer records contain only the id of the parent resource
        # if changed, we set the old key to False, and set the new key
        pointers = []
        for raw_key, attrs, name in self._meta.cache_pointers:
            if attrs and not any(key in changed_keys for key in attrs) \
                     and not force_expire_pointers:
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
            if force_expire_pointers:
                cache_keys.add(cache_key)

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
        cache_logger.debug('kill_cache called for %s' % self)
        cache_keys, version_keys = self.get_cache_keys(child_updated=force)
        if not cache_keys and not version_keys:
            cache_logger.debug('%s has no cache keys' % self)
            return

        cache_logger.debug('%s has the following cache keys:' % self)
        for key in cache_keys:
            cache_logger.debug('\t%s' % key)
        cache_logger.debug('%s has the following version keys:' % self)
        for key in version_keys:
            cache_logger.debug('\t%s' % key)

        cache = self.get_cache()
        cache.delete_many(cache_keys)
        for key in version_keys:
            v = cache.get(key)
            if not v:
                cache.set(key, int(time.time()))
            else:
                cache.incr(key)

class ModelPermissionMixin(object):

    def get_context(self, depth=0):
        ctx = {}
        for key,attr in inspect(self.__class__).all_orm_descriptors.items():
            if not attr.is_attribute:
                continue
            if type(attr.property) == ColumnProperty:
                cls_name = self.__class__.__name__.lower()
                ctx_key = '%s.%s' % (cls_name, key)
                ctx[ctx_key] = getattr(self, key)
                continue
            if type(attr.property) != RelationshipProperty:
                continue
            if attr.property.direction.name != 'MANYTOONE':
                continue
            if len(attr.property.local_remote_pairs) != 1:
                continue            
            parent = getattr(self, key)
            if parent and depth == 0:
                ctx.update(parent.get_context(depth=1))
        return ctx

    @classmethod
    def get_fks(cls, include_parents=True, remote_key=None):
        #print 'get fks:', cls, remote_key
        keys = []
        cls_name = cls.__name__

        if len(cls.__mapper__.primary_key) == 1:
            primary_key = cls.__mapper__.primary_key[0].key
        else:
            primary_key = None

        # add permission for unrestricted access
        keys.append( ('any', None, None, None, cls_name) )

        # add permission for single instance access (single-col pk only)
        if primary_key:
            col_key = '%s_%s' % (cls._meta.model_name, primary_key)
            value = '%%(%s)s' % col_key
            keys.append( ('single', primary_key, value, col_key, cls_name) )

        # iterate through limiters and create a list of local permissions
        for limiter, pairs in cls._meta.permission_limiters.items():
            col_key = None
            new_key = remote_key or primary_key
            if new_key in pairs:
                value = pairs[new_key]
            else:
                primary_key, value = pairs.items()[0]
            keys.append( (limiter, primary_key, value, col_key, cls_name) )

        if not include_parents:
            return keys

        # using this node as a base, grab the keys from parent objects
        # and create expressions to grant child access via parents
        fks = []
        for key in cls._meta.permission_parents + cls._meta.permission_full_parents:
            # 'key' is the name of the parent relation attribute
            attr = getattr(cls, key)
            if not attr.is_attribute:
                continue
            prop = attr.property
            if type(prop) != RelationshipProperty:
                continue
            if prop.direction.name != 'MANYTOONE':
                continue
            if len(prop.local_remote_pairs) != 1:
                continue

            sub_cls = cls.get_related_class(key)
            col = prop.local_remote_pairs[0][0]
            col_attr = column_to_attr(cls, col)
            remote_col = prop.local_remote_pairs[0][1]

            inc_par = sub_cls._meta.permission_terminator == False or \
                      key in cls._meta.permission_full_parents
            sub_fks = sub_cls.get_fks(include_parents=inc_par,
                                      remote_key=remote_col.key)

            for limiter, key_, value, col_key, base_cls in sub_fks:
                if not key_:
                    # do not extend the 'any' permission
                    continue

                # prepend the current node string to each filter in the 
                # limiter expression
                frags = key_.split(',')
                frags = ['%s.%s' % (key, frag) for frag in frags]
                key_ = ','.join(frags)

                frags = value.split(',')
                if len(frags) > 1:
                    frags = [f for f in frags if f.find('.') == -1]
                    if len(frags) == 1:
                        new_col_key = frags[0][2:-2]

                if limiter == 'single' or not col_key:
                    col_key = col_attr.key
                    attr = getattr(cls, col_attr.key, None)
                    if not isinstance(attr, RelationshipProperty):
                        # the column is named differently from the attr
                        for k,v in cls.__mapper__.all_orm_descriptors.items():
                            if not hasattr(v, 'property'):
                                continue
                            if not isinstance(v.property, ColumnProperty):
                                continue
                            if v.property.columns[0] == col:
                                col_key = k
                                break

                if limiter == 'single':
                    # for single limiters, we can eliminate the final join
                    # and just use the value of the fk instead
                    limiter = key_.split('.')[-2]
                    value = '%%(%s)s' % col_key

                keys.append( (limiter, key_, value, col_key, cls_name) )
        return keys

    @classmethod
    def get_related_class(cls, rel_name):
        attr = getattr(cls, rel_name)
        prop = attr.property
        related_cls = prop.argument
        if isinstance(related_cls, types.FunctionType):
            # lazy-loaded Model
            related_cls = related_cls()
        if isinstance(related_cls, _class_resolver):
            # lazy-loaded Model
            related_cls = related_cls()
        if hasattr(related_cls, 'is_mapper') and related_cls.is_mapper:
            # we found a mapper, grab the class from it
            related_cls = related_cls.class_
        return related_cls

    def get_parent(self, attr_name):
        # first, try grabbing it directly
        parent = getattr(self, attr_name)
        if parent:
            return parent
            
        # if nothing was found, grab the fk and lookup manually
        attr = getattr(type(self), attr_name)
        prop = attr.property
        local_col, remote_col = prop.local_remote_pairs[0]
        local_key = local_col.key
        if hasattr(self, local_key):
            value = getattr(self, local_key)
        else:
            # model is missing this key, maybe an aliased column?
            for k,v in type(self).__mapper__.c.items():
                if v is local_col:
                    value = getattr(self, k)
       
        if not value:
            # no relation and no fk
            return None

        filters = {remote_col.key: value}
        parent_cls = type(self).get_related_class(attr_name)
        orm = ORM.get()
        session = orm.sessionmaker()
        parent = session.query(parent_cls).filter_by(**filters).first()
        return parent

    @classmethod
    def normalize_key(cls, key):
        limiter = ''
        frags = key.split('.')
        if len(frags) > 1:
            # expression contains multiple relations
            col_name = frags.pop()
            rel_name = frags.pop()

            current_cls = base_cls = cls
            for f in frags:
                current_cls = current_cls.get_related_class(f)
            prev_cls = current_cls
            current_rel = getattr(current_cls, rel_name)
            current_cls = current_cls.get_related_class(rel_name)

            col = getattr(current_cls, col_name)

            attr = None
            for loc, rem in current_rel.property.local_remote_pairs:
                if rem in col.property.columns:
                    attr = loc.name
                    for c in inspect(prev_cls).all_orm_descriptors:
                        try:
                            cols = c.property.columns
                            assert len(cols) == 1
                            if cols[0] == loc:
                                attr = c.key
                                break
                        except:
                            pass
                    break
            if attr:
                if frags:
                    limiter = ' ' + ' '.join(reversed(frags))
                frags.append(attr)
                key = '.'.join(frags)
            else:
                frags.append(rel_name)
                limiter = ' ' + ' '.join(reversed(frags))

        return (key, limiter)
