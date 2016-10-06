import itertools

from django.template.defaultfilters import slugify

from sqlalchemy import *
from sqlalchemy import inspect, func
from sqlalchemy.orm import attributes
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.session import object_session
from sqlalchemy.orm.util import has_identity


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

  def contribute_to_class(self, cls, name):
    self.cls = cls
    self.slug_key = name
    setattr(cls, name, self)

  @property
  def comparison_keys(self):
    if not hasattr(self, '_comparison_keys'):
      keys = {
        'col_keys': [],
        'rel_keys': [],
      }
      mapper = inspect(self.cls)
      for key in self.unique_with:
        prop = mapper.get_property(key)
        if isinstance(prop, RelationshipProperty):
          fks = [c.key for c in prop.local_columns]
          keys['rel_keys'].append( (key, fks) )
        else:
          keys['col_keys'].append(key)
      self._comparison_keys = keys
    return self._comparison_keys

  def is_conflict(self, instance, other, slug):
    """
    returns True if 'other' is a slug conflict with the source obj
    """
    if other is instance:
      # an object can't conflict with itself
      return False

    if not isinstance(other, type(instance)):
      # objects of different classes cannot conflict with eachother
      return False

    if getattr(other, self.slug_key) != slug:
      # slug doesn't match, not a conflict
      return False

    # compare related objects and foreign keys
    for key, fks in self.comparison_keys['rel_keys']:
      if getattr(other, key) != getattr(instance, key):
        # the objects have different related objects
        return False
      for fk in fks:
        if getattr(instance, fk) is None:
          # incomplete foreign key, comparison will be done via the 
          # related object rather than the key values
          continue
        if getattr(other, fk) != getattr(instance, fk):
          # the objects have different related objects
          return False

    # now check column values
    for key in self.comparison_keys['col_keys']:
      if getattr(other, key) != getattr(instance, key):
        return False

    return True

  def has_conflicts(self, instance, slug):
    # check the session first
    if self.has_session_conflicts(instance, slug):
      return True

    # now check the db
    return self.has_db_conflicts(instance, slug)

  def has_session_conflicts(self, instance, slug):
    """
    checks in the session for items which conflict with the provided slug
    this is necessary for times when multiple items will be committed at
    the same time, in order to resolve conflict issues before the commit
    """
    session = object_session(instance)
    # session.new must be processed first, so that when a conflict arises,
    #the original owner of the slug is allowed to keep it
    for obj in itertools.chain(session.new, session.dirty):
      if self.is_conflict(instance, obj, slug):
        return True
    return False

  def has_db_conflicts(self, instance, slug):
    """
    Checks in the database for items with conflicting slugs
    """
    session = object_session(instance)
    keys = self.comparison_keys['col_keys'][:]
    for rel_key, fk_keys in self.comparison_keys['rel_keys']:
      keys.extend(fk_keys)
    filters = {key: getattr(instance, key) for key in keys}
    filters[self.slug_key] = slug

    query = session.query(self.cls).filter_by(**filters)
    if has_identity(instance):
      # for existing objects, exclude the object from the search
      ident = instance.pk_as_query_filters(force=True)
      query = query.filter(not_(ident))
    with session.no_autoflush:
      conflicts = query.count()
    return conflicts > 0

  def generate_unique_slug(self, instance, slug):
    original_slug = slug

    # check relationships to ensure either an object or fk is present
    for rel_key, fk_keys in self.comparison_keys['rel_keys']:
      if getattr(instance, rel_key):
        # we have a related object
        continue
      fk_vals = [getattr(instance, key) for key in fk_keys]
      if None in fk_vals:
        # no related obj and no fk, not sure how this could
        # happen, as existing objects will always have both
        # populated, and new objects should have at least one
        # error for now, and figure out how to handle it if
        # the situation arises
        assert False

    index = 1
    while self.has_conflicts(instance, slug):
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
      slug = self.generate_unique_slug(instance, slug)

    setattr(instance, self.key, slug)
