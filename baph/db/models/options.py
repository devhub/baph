import re

from django.conf import settings
from django.core.cache import DEFAULT_CACHE_ALIAS, get_cache
from django.utils.encoding import force_unicode
from django.utils.functional import cached_property
from django.utils.translation import (string_concat, get_language, activate,
    deactivate_all)
from sqlalchemy import inspect, Integer
from sqlalchemy.orm import configure_mappers
from sqlalchemy.ext.hybrid import HYBRID_PROPERTY, HYBRID_METHOD
from sqlalchemy.ext.associationproxy import ASSOCIATION_PROXY
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty

from baph.db import types
from baph.db.models.fields import Field
from baph.utils.text import camel_case_to_spaces


DEFAULT_NAMES = ('model_name', 'model_name_plural',
                 'verbose_name', 'verbose_name_plural', 
                 'app_label', 'swappable', 'auto_created',
                 'cache_alias', 'cache_timeout', 'cache_pointers',
                 'cache_detail_fields', 'cache_list_fields',
                 'cache_relations', 'cache_cascades', 
                 'filter_translations', 'last_modified',
                 'permissions', 'permission_scopes', 'form_class',
                 'permission_actions', 'permission_classes',
                 'permission_parents', 'permission_full_parents', 
                 'permission_limiters', 'permission_terminator',
                 'permission_handler', 'permission_resources',
                 'global_column', 'global_cascades', 'global_parents',
                 'latlon_field_names',
                 )

class Options(object):
    def __init__(self, meta, app_label=None):
        self.cache_alias = DEFAULT_CACHE_ALIAS
        self.cache_timeout = None
        self.cache_detail_fields = []
        self.cache_list_fields = []
        # cache_pointers is a list of identity keys which contain no data
        # other than the primary key of the object being pointed at.
        # format: (cache_key_template, columns, name)
        # cache_key_template and columns function as above, and 'name' is
        # an alias to help distinguish between keys during unittesting
        # when an update occurs, two actions occur: the new value is set
        # to the current object, and the previous value (if different) is
        # set to False (not deleted)
        self.cache_pointers = []
        # cache_relations is a list of relations which should be monitored
        # for changes when generating cache keys for invalidation. This should
        # be used for relationships to composite keys, which cannot be
        # handled properly via cache_cascades
        self.cache_relations = []
        # cache_cascades is a list of relations through which to cascade
        # invalidations. Use this when an object is cached as a subobject of
        # a larger cache, to signal the parent that it needs to recache
        self.cache_cascades = []
        # global_column is the name of the boolean column which indicates
        # global status. This must be set in order to use globalization
        self.global_column = None
        # global_cascades is a list of relationships through which 
        # globalization should propagate (all children become globals)
        self.global_cascades = []
        # global_parents is a list of relationships which should be checked
        # on object creation, and if a global parent is found, the new
        # object will be globalized
        self.global_parents = []

        self.permissions = {}
        self.permission_scopes = {}
        
        # filter_translations allows mapping of filter keys to 'full' filters
        # in the event the target column is in another table.
        self.filter_translations = {}

        # permission_parents is a list of *toOne relations which can be
        # considered to refer to 'parents'. These relations will automatically
        # be considered when generating possible permission paths
        self.permission_parents = []
        # permission_resources is a dict, with each key containing a resource
        # name to expose (generally the lowercased classname), and a value 
        # containing a list of actions available on that resource
        # ex: { 'image': ['add', 'edit', 'delete', 'view', 'crop'] }
        self.permission_resources = {}
        # permission_handler is the name of the parent relation through which
        # to route permission requests for this object
        self.permission_handler = None
        # permission_limiters is a dict, with each key containing an 'alias'
        # for the limiter, used in generating codenames. Each value is a dict,
        # with the key referring to the local column to be checked, and the
        # value containing an expression which will be evaluated against the
        # permission's context
        self.permission_limiters = {}
        self.permission_full_parents = []
        self.permission_terminator = False

        # latlon_field_names is a 2-tuple containing the field names
        # of the latitude and longitude columns (for geocoding purposes)
        self.latlon_field_names = None

        self.limit = 1000
        self.object_name, self.app_label = None, app_label
        self.model_name, self.model_name_plural = None, None
        self.verbose_name, self.verbose_name_plural = None, None
        self.base_model_name, self.base_model_name_plural = None, None
        
        self.pk = None
        self.form_class = None
        self.meta = meta

        self.swappable = None
        self.auto_created = False
        self.required_fields = None

    def contribute_to_class(self, cls, name):
        cls._meta = self
        self.model = cls
        # First, construct the default values for these options.
        self.object_name = cls.__name__
        self.model_name = self.object_name.lower()
        self.verbose_name = camel_case_to_spaces(self.object_name)

        self.original_attrs = {}

        # Next, apply any overridden values from 'class Meta'.
        if self.meta:
            meta_attrs = self.meta.__dict__.copy()
            for name in self.meta.__dict__:
                # Ignore any private attributes that Django doesn't care about.
                # NOTE: We can't modify a dictionary's contents while looping
                # over it, so we loop over the *original* dictionary instead.
                if name.startswith('_'):
                    del meta_attrs[name]
            for attr_name in DEFAULT_NAMES:
                if attr_name in meta_attrs:
                    setattr(self, attr_name, meta_attrs.pop(attr_name))
                elif hasattr(self.meta, attr_name):
                    setattr(self, attr_name, getattr(self.meta, attr_name))

            # Any leftover attributes must be invalid.
            if meta_attrs != {}:
                raise TypeError("'class Meta' got invalid attribute(s): %s" 
                    % ','.join(meta_attrs.keys()))

        # initialize params that depend on other params being set
        if self.model_name_plural is None:
            self.model_name_plural = self.model_name + 's'

        if self.verbose_name_plural is None:
            self.verbose_name_plural = self.verbose_name + 's'

        if self.cache_timeout is None:
            self.cache_timeout = get_cache(self.cache_alias).default_timeout

        from baph.db import ORM
        Base = ORM.get().Base

        base_model_name = self.model_name
        base_model_name_plural = self.model_name_plural
        for base in self.model.__mro__:
            if not issubclass(base, Base):
                continue
            if base in (self.model, Base):
                continue
            if not hasattr(base, '__mapper_args__'):
                continue
            if 'polymorphic_on' in base.__mapper_args__:
                base_model_name = base._meta.base_model_name
                base_model_name_plural = base._meta.base_model_name_plural
                break
        self.base_model_name = unicode(base_model_name)
        self.base_model_name_plural = unicode(base_model_name_plural)

        del self.meta

    def verbose_name_raw(self):
        """
        There are a few places where the untranslated verbose name is needed
        (so that we get the same value regardless of currently active
        locale).
        """
        lang = get_language()
        deactivate_all()
        raw = force_text(self.verbose_name)
        activate(lang)
        return raw
    verbose_name_raw = property(verbose_name_raw)

    def _swapped(self):
        """
        Has this model been swapped out for another? If so, return the model
        name of the replacement; otherwise, return None.

        For historical reasons, model name lookups using get_model() are
        case insensitive, so we make sure we are case insensitive here.
        """
        if self.swappable:
            model_label = '%s.%s' % (self.app_label, self.model_name)
            swapped_for = getattr(settings, self.swappable, None)
            if swapped_for:
                try:
                    swapped_label, swapped_object = swapped_for.split('.')
                except ValueError:
                    # setting not in the format app_label.model_name
                    # raising ImproperlyConfigured here causes problems with
                    # test cleanup code - instead it is raised in get_user_model
                    # or as part of validation.
                    return swapped_for

                if '%s.%s' % (swapped_label, swapped_object.lower()) not in (None, model_label):
                    return swapped_for
        return None
    swapped = property(_swapped)

    @cached_property
    def fields(self):
        """
        The getter for self.fields. This returns the list of field objects
        available to this model (including through parent models).

        Callers are not permitted to modify this list, since it's a reference
        to this instance (not a copy).
        """
        try:
            self._field_name_cache
        except AttributeError:
            self._fill_fields_cache()
        return self._field_name_cache

    def _fill_fields_cache(self):
        cache = []
        if not self.model.__mapper__.configured:
            configure_mappers()
        for key, attr in inspect(self.model).all_orm_descriptors.items():
            if attr.is_mapper:
                continue
            elif attr.extension_type == HYBRID_METHOD:
                continue
            elif attr.extension_type == HYBRID_PROPERTY:
                continue
            field = Field.field_from_attr(key, attr, self.model)
            cache.append((field, None))
        self._field_cache = tuple(cache)
        self._field_name_cache = [x for x, _ in cache]

    def get_field(self, name, many_to_many=True):
        """
        Returns the requested field by name. Raises FieldDoesNotExist on error.
        """
        to_search = self.fields #(self.fields + self.many_to_many) if many_to_many else self.fields
        for f in to_search:
            if f.name == name:
                return f
        raise FieldDoesNotExist('%s has no field named %r' % (self.object_name, name))
