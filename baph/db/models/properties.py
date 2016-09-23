import itertools

from django.template.defaultfilters import slugify

from sqlalchemy import *
from sqlalchemy import inspect
from sqlalchemy.orm import attributes
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.session import object_session
from sqlalchemy.orm.util import has_identity


def is_conflict(obj, session_obj, rel_keys, col_keys, slug_key, slug_value):
  """
  returns True if the session object is a conflict with the source obj
  """
  if obj is session_obj:
    # an object can't conflict with itself
    return False

  if not isinstance(session_obj, type(obj)):
    # objects of different classes cannot conflict with eachother
    return False

  if getattr(session_obj, slug_key) != slug_value:
    # slug doesn't match, not a conflict
    return False

  # compare related objects 
  for key in rel_keys:
    if getattr(session_obj, key) != getattr(obj, key):
      # the objects have different related objects
      return False

  # now check column values
  for key in col_keys:
    if getattr(session_obj, key) != getattr(obj, key):
      return False

  return True

def has_session_conflicts(obj, rel_keys, col_keys, slug_key, slug_value):
  """
  checks in the session for items which conflict with the provided slug
  this is necessary for times when multiple items will be committed at
  the same time, in order to resolve conflict issues before the commit
  """
  session = object_session(obj)
  # session.new must be processed first, so that when a conflict arises,
  #the original owner of the slug is allowed to keep it
  for o in itertools.chain(session.new, session.dirty):
    if is_conflict(obj, o, rel_keys, col_keys, slug_key, slug_value):
      return True
  return False

def has_db_conflicts(obj, rel_keys, col_keys, slug_key, slug_value):
  """
  Checks in the database for items with conflicting slugs
  """
  session = object_session(obj)
  ident = obj.pk_as_query_filters(force=True)
  filters = {key: getattr(obj, key) for key in col_keys}
  filters[slug_key] = slug_value
  query = session.query(type(obj)) \
                             .filter_by(**filters) \
                             .filter(not_(ident))
  with session.no_autoflush:
    conflicts = query.count()
  return conflicts > 0

def has_conflicts(obj, rel_keys, col_keys, slug_key, slug_value):
  # check the session first
  if has_session_conflicts(obj, rel_keys, col_keys, slug_key, slug_value):
    return True

  # now check the db
  return has_db_conflicts(obj, rel_keys, col_keys, slug_key, slug_value)

class AutoSlugField(ColumnProperty):
    def __init__(self, *args, **kwargs):
        max_length = kwargs.pop('max_length', 255)
        kwargs['type_'] = String(max_length)

        self.always_update = kwargs.pop('always_update', False)    
        self.populate_from = kwargs.pop('populate_from', None)
        self.index_sep = kwargs.pop('sep', '-')
        self.unique_with = kwargs.pop('unique_with', ())
        if isinstance(self.unique_with, basestring):
            self.unique_with = (self.unique_with,)

        self.slugify = kwargs.pop('slugify', slugify)
        assert hasattr(self.slugify, '__call__')

        if self.unique_with:
            kwargs['unique'] = False
        self.unique = kwargs.get('unique', False)
        self.nullable = kwargs.get('nullable', True)

        column = Column(*args, **kwargs)
        super(AutoSlugField, self).__init__(column)

    def generate_unique_slug(self, session, instance, slug):
        original_slug = slug
        mapper = inspect(type(instance))
        rel_keys = []
        col_keys = []
        for key in self.unique_with:
          value = getattr(instance, key)
          prop = mapper.get_property(key)
          if isinstance(prop, RelationshipProperty):
            # add the relationship key to the comparison list
            rel_keys.append(key)
            # add the foreign keys to the list of columns to check
            for column in prop.local_columns:
              val = getattr(instance, column.key)
              if val is None:
                # incomplete or missing fk
                if value is None:
                  # no related obj and no fk, not sure how this could
                  # happen, as existing objects will always have both
                  # populated, and new objects should have at least one
                  # error for now, and figure out how to handle it if
                  # the situation arises
                  assert False
              else:
                # only add the column key as a comparison field if we have
                # a value, otherwise false positives can occur during conflict
                # checking. If the fk isn't populated, the related object will
                # still allow proper conflict detection
                col_keys.append(column.key)
          else:
            # column property
            col_keys.append(key)

        index = 1
        while has_conflicts(instance, rel_keys, col_keys, self.key, slug):
          index += 1
          data = dict(slug=original_slug, sep=self.index_sep, index=index)
          slug = '%(slug)s%(sep)s%(index)d' % data
        return slug

    def before_flush(self, session, add, instance):
        history = attributes.get_history(instance, self.key)
        value = getattr(instance, self.key)
        if self.always_update or (self.populate_from and not value):
            value = getattr(instance, self.populate_from)
        if value:
            slug = self.slugify(value)
        else:
            slug = None
        if not slug and not self.nullable:
            slug = instance.__class__.__name__.lower()
        if self.unique or self.unique_with:
            slug = self.generate_unique_slug(session, instance, slug)

        setattr(instance, self.key, slug)
