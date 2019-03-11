from collections import defaultdict
import datetime
import logging
import math
import time
import types

from django.conf import settings
from django.core.cache import get_cache
from sqlalchemy import *
from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.declarative.clsregistry import _class_resolver
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.orm import class_mapper, object_session
from sqlalchemy.orm.attributes import get_history, instance_dict
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.util import has_identity

from baph.db import ORM
from baph.db.models.utils import identity_key
from .utils import column_to_attr, class_resolver


cache_logger = logging.getLogger('cache')

# these keys auto-update, so should be ignored when comparing old/new values
IGNORABLE_KEYS = (
    'modified',
    'last_modified',
    'added',
    )

CACHE_KEY_MODES = (
  'detail',
  'detail_version',
  'list',
  'list_version',
  'list_partition',
  'list_partition_version',
  'pointer',
  'asset',
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

class GeoMixin(object):

    @property
    def distance(self):
        if not (self._lat and self._lon):
            # this instance isn't geocoded
            return None
        return self._distance(self._lat, self._lon)

    @hybrid_method
    def _distance(self, lat, lon):
        fields = self._meta.latlon_field_names
        _lat = getattr(self, fields[0])
        _lon = getattr(self, fields[1])
        return 3959 * math.acos(
            math.cos(math.radians(self._lat))
            * math.cos(math.radians(_lat))
            * math.cos(math.radians(_lon) - math.radians(self._lon))
            + math.sin(math.radians(self._lat))
            * math.sin(math.radians(_lat))
            )

    @_distance.expression
    def _distance(self, lat, lon):
        fields = self._meta.latlon_field_names
        _lat = getattr(self, fields[0])
        _lon = getattr(self, fields[1])
        self._lat = lat # set these on the instance, for use later
        self._lon = lon
        return 3959 * func.acos(
            func.cos(func.radians(lat))
            * func.cos(func.radians(_lat))
            * func.cos(func.radians(_lon) - func.radians(lon))
            + func.sin(func.radians(lat))
            * func.sin(func.radians(_lat))
            )

    @classmethod
    def get_distance_filters(cls, lat, lon, threshold):
        """ returns a list of sqla filters, to be applied to an existing query
            ie: query.filter(*filters) """
        field_names = cls._meta.latlon_field_names
        lat_field = getattr(cls, field_names[0])
        lon_field = getattr(cls, field_names[1])
        diff = threshold / 69.0 # miles -> degree variance
        filters = [
            lat_field > lat - diff,
            lat_field < lat + diff,
            lon_field > lon - diff,
            lon_field < lon + diff,
            cls._distance(lat,lon) < threshold, # this sets instance state!
            ]
        return filters

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
      if not cls._meta.cache_alias:
        return None
      return get_cache(cls._meta.cache_alias)

    @classmethod
    def cache_fields(cls):
      """
      Returns the names of all fields required to build cache keys
      """
      fields = set()
      for attr in ('cache_detail_fields', 'cache_list_fields',
                   'cache_partitions'):
        fields.update(getattr(cls._meta, attr, []) or [])
      for raw_key, attrs, name in cls._meta.cache_pointers:
        fields.update(attrs)
      return fields      

    @property
    def cache_data(self):
      """
      Returns a dict containing all values needed to build cache keys
      """
      return {field: getattr(self, field) for field in self.cache_fields()}

    @classmethod
    def get_cache_partitions(cls, **kwargs):
      """
      Returns the values to be used in generating partition version keys
      """
      partitions = []
      fields = set(cls._meta.cache_partitions) & set(kwargs.keys())
      for field in sorted(fields):
        value = kwargs.get(field, None)
        partitions.append('%s_%s' % (field, value))
      return partitions

    @classmethod
    def get_cache_partition_version_keys(cls, **kwargs):
      version_keys = []
      for partition in cls.get_cache_partitions(**kwargs):
        version_keys.append('%s:partition:%s' % (
          cls._meta.base_model_name_plural, partition))
      return version_keys

    @classmethod
    def get_required_cache_fields(cls, base_mode):
      """
      Returns a list of fields required for generating a key of the given type
      """
      if '_' in base_mode:
        " This is a full mode, reduce to base_mode "
        base_mode = base_mode.split('_')[0]
      if base_mode == 'asset':
        " asset keys require the same fields as the parent object "
        base_mode = 'detail'
      name = 'cache_%s_fields' % base_mode
      fields = getattr(cls._meta, name, None) or []
      if base_mode == 'detail' and not fields:
        raise Exception('cache_detail_fields is required for building detail '
                        'and asset cache keys')
      return fields

    @classmethod
    def get_cache_root(cls, base_mode, **kwargs):
      pieces = []
      fields = cls.get_required_cache_fields(base_mode)
      for key in sorted(fields):
        # all associated fields must be present in kwargs
        if not key in kwargs:
          raise ValueError('%s is undefined; cannot generate cache key' % key)
        pieces.append('%s=%s' % (key, kwargs[key]))
      return ':'.join(pieces)

    @classmethod
    def get_cache_partition(cls, **kwargs):
      cache = cls.get_cache()
      version_keys = cls.get_cache_partitions(**kwargs)
      pieces = []
      for version_key in version_keys:
        # prepend the resource to the key
        _version_key = '%s:partition:%s' % (
          cls._meta.base_model_name_plural, version_key)
        version = cache.get(_version_key)
        if version is None:
          version = int(time.time())
          cache.set(_version_key, version)
        pieces.append('%s_%s' % (version_key, version))
      return ':'.join(pieces)

    @classmethod
    def get_cache_suffix(cls, **kwargs):
      """
      The cache suffix contains all params that are not used in
      list partitioning, in alphabetical order
      """
      pieces = []
      reserved_fields = (set(cls._meta.cache_partitions) 
                       | set(cls._meta.cache_list_fields))
      for key, value in sorted(kwargs.items()):
        if key in reserved_fields:
          continue
        if key == 'offset' and value == 0:
          # ignore the default value to keep keys shorter
          continue
        pieces.append('%s=%s' % (key, value))
      return ':'.join(pieces)

    @classmethod
    def validate_cache_mode(cls, mode):
      if mode not in CACHE_KEY_MODES:
        raise ValueError('%s is not a valid cache mode. Valid modes are: %s'
                         % (mode, ', '.join(CACHE_KEY_MODES)))
      base_mode = mode.split('_')[0]
      if base_mode == 'asset':
        " validate asset keys as if they were detail keys "
        base_mode = 'detail'
      if base_mode not in cls._meta.cache_modes:
        raise ValueError('%s is not a supported cache mode for this class. '
                         'Supported modes are: %s'
                         % (base_mode, ', '.join(cls._meta.cache_modes)))
      if mode == 'detail' and not cls._meta.cache_detail_fields:
        raise Exception('Meta.cache_detail_fields is required for '
                        'generating cache detail and asset keys')
      if mode in ('list_partition', 'list_partition_version') \
          and not cls._meta.cache_partitions:
        raise Exception('Meta.cache_partitions is required for '
                        'generating list partition keys')


    @classmethod
    def build_cache_key(cls, mode, *args, **kwargs):
      """
      Generates a cache key for the provided mode and the given kwargs
      mode is one of ['asset', 'list', 'detail', 'list_version', or 'pointer']
      if mode is detail, cache_detail_fields must be defined in the cls meta
      if mode is list or list_version, cache_list_fields must be in the cls meta
      the associated fields must all be present in kwargs
      """
      kwargs = {k: int(v) if isinstance(v, bool) else v for k,v in kwargs.items()}
      cache = cls.get_cache()

      def assemble_key(pieces):
        """
        joins all non-empty components and returns a string
        """
        return ':'.join([str(p) for p in pieces if p])

      def getset_version(key):
        """
        gets the version for the given key
        if no version exists, it is set to the current unix timestamp
        """
        version = cache.get(key)
        if not version:
          version = int(time.time())
          cache.set(key, version)
        return version

      cls.validate_cache_mode(mode)
      base_mode = mode.split('_')[0]
      if base_mode == 'asset':
        base_mode = 'detail'

      if mode == 'pointer':
        if len(args) != 1:
          raise Exception('build_cache_key requires one positional arg'
                          '(the pointer name) if mode=="pointer"')
        rows = [x for x in cls._meta.cache_pointers if x[2] == args[0]]
        if len(rows) == 0:
          raise Exception('could not find a cache_pointer with name %r'
                          % args[0])
        raw_key, attrs, name = rows[0]
        return raw_key % kwargs
      elif mode == 'asset':
        if not args:
          raise Exception('build_cache_key requires at least one positional '
                          'arg (the subkey) if mode=="asset"')
        subkey = args[0]
        obj_type = None
        if len(args) > 1:
          " an object type was defined "
          obj_type = args[1]

      pieces = []
      pieces.append(cls._meta.base_model_name_plural)
      pieces.append(base_mode)

      # add core identification fields to the key
      pieces.append(cls.get_cache_root(base_mode, **kwargs))

      if mode in ('detail_version', 'asset'):
        # add the version suffix to the base key
        pieces.append('version')

      if mode in ('list', 'list_partition'):
        # add optional partition fields to the key
        pieces.append(cls.get_cache_partition(**kwargs))

      if mode == 'list':
        # apply filter fields to the key
        version_key = assemble_key(pieces)
        pieces.append(cls.get_cache_suffix(**kwargs))
        pieces.append(getset_version(version_key))

      if mode == 'asset':
        version_key = assemble_key(pieces)
        # remove the 'version' piece from the asset key
        pieces.pop()
        pieces.append(getset_version(version_key))
        pieces.append('asset')
        if obj_type:
          # add obj_type if provided
          pieces.append(obj_type)
        pieces.append(subkey)

      return assemble_key(pieces)

    @property
    def cache_key(self):
      """
      Instance property which returns the cache key for a single object
      """
      self.validate_cache_mode('detail')
      if not has_identity(self):
        raise Exception('This instance has no identity')
      return self.build_cache_key('detail', **self.cache_data)

    @property
    def cache_detail_version_key(self):
      """
      Instance property which returns the cache list version key
      for a single object
      """
      self.validate_cache_mode('detail')
      return self.build_cache_key('detail_version', **self.cache_data)

    @property
    def cache_list_version_key(self):
      """
      Instance property which returns the cache list version key
      for a single object
      """
      self.validate_cache_mode('list')
      return self.build_cache_key('list_version', **self.cache_data)

    @property
    def cache_list_key(self):
      """
      Instance property which returns the cache list key for a single object
      """
      self.validate_cache_mode('list')
      return self.build_cache_key('list', **self.cache_data)

    @property
    def cache_partition_version_keys(self):
      """
      Returns a list of version keys related to the partitions of
      the current instance
      """
      self.validate_cache_mode('list_partition')
      return self.get_cache_partition_version_keys(**self.cache_data)

    @property
    def cache_partition_key(self):
      """
      Instance property which returns the cache list partition key
      for a single object
      """
      self.validate_cache_mode('list_partition')
      return self.build_cache_key('list_partition', **self.cache_data)

    def make_asset_key(self, key, asset_type=None):
      """
      Generates an asset key, which will be invalidated when the
      parent object is invalidated
      """
      self.validate_cache_mode('asset')
      if not has_identity(self):
        raise Exception('This instance has no identity')
      return self.build_cache_key('asset', key, asset_type,
                                  **self.cache_data)      

    def cache_asset(self, key, value, asset_type=None):
      """
      Writes an asset belonging to an instance into the cache
      """
      self.validate_cache_mode('asset')
      asset_key = self.make_asset_key(key, asset_type)
      cache = self.get_asset_cache(asset_type)
      cache.set(asset_key, value)

    def get_asset_cache(self, asset_type=None):
      asset_aliases = self._meta.cache_asset_cache_aliases
      if not asset_type:
        asset_type = 'generic'
        default = self._meta.cache_alias
      else:
        default = None
      alias = asset_aliases.get(asset_type, default)
      if not alias:
        raise Exception("Unable to determine cache alias for "
                        "asset type '%s'" % asset_type)
      return get_cache(alias)

    @classmethod
    def build_cache_pointers(cls, data):
      keys = {}
      for raw_key, attrs, name in cls._meta.cache_pointers:
        try:
          keys[name] = raw_key % data
        except:
          pass
      return keys


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

    @property
    def is_cacheable(self):
      """
      Returns a boolean indicating whether cache operations should
      be executed for this instance
      """
      if self._meta.cache_modes:
        # this class is directly cacheable
        return True
      if self._meta.cache_cascades:
        # this class may or may not use the cache, but it needs to
        # cascade killcache operations to related objects
        return True
      return False

    @classmethod
    def get_checked_fields(cls, ignore=[]):
      """
      Returns a list of field names that should be checked for changes
      when determining if an object cache should be killed
      """
      insp = inspect(cls)
      # include all column attributes by default
      fields = set([attr.key for attr in insp.column_attrs])
      # add any relationships defined in cache_relations
      fields.update(cls._meta.cache_relations)
      # remove any fields in the ignore list
      fields.difference_update(ignore)
      return fields

    def get_changes(self, ignore=[]):
      """
      Returns a dict of pending changes to the current instance
      key: attribute name
      value: tuple in the form (old_value, new_value)
      """
      insp = inspect(self)
      fields = self.get_checked_fields(ignore)
      changes = {}
      for field in fields:
        attr = getattr(insp.attrs, field)
        ins, eq, rm = attr.history
        if ins or rm:
          old_value = rm[0] if rm and has_identity(self) else None
          new_value = ins[0] if ins else None
          changes[field] = (old_value, new_value)
      return changes

    def get_cache_keys(self, child_updated=False, force_expire_pointers=False,
                       force=False):
      cache_alias = self._meta.cache_alias
      cache = self.get_cache()
      cache_keys = set()
      version_keys = set()

      if not self.is_cacheable:
        return (cache_keys, version_keys)

      orm = ORM.get()
      session = object_session(self) or orm.sessionmaker()

      deleted = self.is_deleted or self in session.deleted
      changes = self.get_changes(ignore=IGNORABLE_KEYS)
      self_updated = bool(changes) or deleted

      if not self_updated and not child_updated and not force:
        return (cache_keys, version_keys)

      changed_attrs = set(changes.keys())
      data = self.cache_data

      old_data = {}
      if has_identity(self):
        for attr in self.cache_fields():
          ins, eq, rm = get_history(self, attr)
          old_data[attr] = rm[0] if rm else eq[0]
  
      if 'detail' in self._meta.cache_modes:
        # we only kill primary cache keys if the object exists
        # this key won't exist during CREATE
        if has_identity(self):
          cache_key = self.cache_key
          cache_keys.add((cache_alias, cache_key))

      if 'list' in self._meta.cache_modes:
        # collections will be altered by any action, so we always
        # kill these keys
        version_key = self.cache_list_version_key
        version_keys.add((cache_alias, version_key))
        if self._meta.cache_partitions:  
          # add the partition keys as well
          for pversion_key in self.cache_partition_version_keys:
            version_keys.add((cache_alias, pversion_key))
          if changed_attrs.intersection(self._meta.cache_partitions):
            # if partition field values were changed, we need to
            # increment the version keys for the previous values
            for pversion_key in self.get_cache_partition_version_keys(**old_data):
              version_keys.add((cache_alias, pversion_key))

      if 'asset' in self._meta.cache_modes:
        # models with sub-assets need to increment the version key
        # of the parent detail
        if has_identity(self):
          key = self.cache_detail_version_key
          if deleted:
            # delete the detail version key
            cache_keys.add((cache_alias, key))
          else:
            # for updates, increment the version key
            version_keys.add((cache_alias, key))

      # pointer records contain only the id of the parent resource
      # if changed, we set the old key to False, and set the new key
      for raw_key, attrs, name in self._meta.cache_pointers:
        if not changed_attrs.intersection(attrs) and not force_expire_pointers:
          # the fields which trigger this pointer were not changed
          continue
        cache_key = raw_key % data
        (_, ident) = identity_key(instance=self) 
        if len(ident) > 1:
          ident = ','.join(map(str, ident))
        else:
          ident = ident[0]
        if not self.is_deleted:
          cache.set(cache_key, ident)
        if force_expire_pointers:
          cache_keys.add((cache_alias, cache_key))

        # if this is a new object, we're done
        if not has_identity(self):
          continue

        # if this is an existing object, we need to handle the old key
        old_data = {}
        for attr in attrs:
          ins, eq, rm = get_history(self, attr)
          old_data[attr] = rm[0] if rm else eq[0]

        old_key = raw_key % old_data
        if old_key == cache_key and not self.is_deleted:
          # the pointer key is unchanged, nothing to do here
          continue

        old_ident = cache.get(old_key)
        if old_ident and str(old_ident) == str(ident):
          # this object is the current owner of the key. we need to remove
          # the reference to this instance
          cache.set(old_key, False)

      # cascade the cache kill operation to related objects, so parents
      # know if children have changed, in order to rebuild the cache
      for cascade in self._meta.cache_cascades:
        objs = getattr(self, cascade)
        if not objs:
          # no related objects
          continue
        if not isinstance(objs, list):
          # *-to-one relation, force into a list
          objs = [objs]
        for obj in objs:
          child_keys = obj.get_cache_keys(child_updated=True)
          cache_keys.update(child_keys[0])
          version_keys.update(child_keys[1])

      return (cache_keys, version_keys)

    def kill_cache(self, force=False):
      ident = '%s(%s)' % (self.__class__.__name__, id(self))
      cache_logger.debug('kill_cache called for %s' % ident)

      cache_keys, version_keys = self.get_cache_keys(child_updated=force)
      if not cache_keys and not version_keys:
        cache_logger.debug('  %s has no cache keys' % ident)
        return

      keymap = {}

      cache_logger.debug('  %s has the following cache keys:' % ident)
      for alias, key in cache_keys:
        cache_logger.debug('    [%s] %s' % (alias, key))
        if alias not in keymap:
          keymap[alias] = {'cache': set(), 'version': set()}
        keymap[alias]['cache'].add(key)

      cache_logger.debug('  %s has the following version keys:' % ident)
      for alias, key in version_keys:
        cache_logger.debug('    [%s] %s' % (alias, key))
        if alias not in keymap:
          keymap[alias] = {'cache': set(), 'version': set()}
        keymap[alias]['version'].add(key)

      for cache_alias, keys in keymap.items():
        cache = get_cache(cache_alias)
        cache.delete_many(keys['cache'])
        for key in keys['version']:
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
        mapper = inspect(type(self))
        attr = getattr(type(self), attr_name)
        prop = attr.property
        local_col, remote_col = prop.local_remote_pairs[0]
        local_prop = mapper.get_property_by_column(local_col)
        value = getattr(self, local_prop.key)

        if not value:
            # no relation and no fk = no parent
            return None

        parent_cls = type(self).get_related_class(attr_name)
        mapper = inspect(parent_cls)
        remote_prop = mapper.get_property_by_column(remote_col)
        filters = {remote_prop.key: value}

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
