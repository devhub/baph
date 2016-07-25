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

def has_conflicts(obj, rel_keys, col_keys, slug_key, slug_value):
  session = object_session(obj)

  # check the session first
  for o in session.new.union(session.dirty):
    if is_conflict(obj, o, rel_keys, col_keys, slug_key, slug_value):
      return True

  # now check the db
  ident = obj.pk_as_query_filters(force=True)
  filters = {key: getattr(obj, key) for key in col_keys}
  filters[slug_key] = slug_value
  conflicts = session.query(type(obj)) \
                             .filter_by(**filters) \
                             .filter(not_(ident)) \
                             .count()
  if conflicts:
    return True

  return False

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
            cols = [col.key for col in prop.local_columns]
            vals = [getattr(instance, k) for k in cols]

            if None not in vals:
              # all fks are populated, safe to use these values
              col_keys.extend(cols)
            elif value is None:
              # not sure when this would happen
              assert False
            elif has_identity(value):
              # parent already exists in the db
              col_keys.extend(cols)
            else:
              # parent is a new instance
              rel_keys.append(key)
          else:
            # column property
            col_keys.append(key)

        index = 1
        base_col_keys = col_keys[:]

        while True:
          if not has_conflicts(instance, rel_keys, col_keys, self.key, slug):
            return slug
          index += 1
          data = dict(slug=original_slug, sep=self.index_sep, index=index)
          slug = '%(slug)s%(sep)s%(index)d' % data

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
