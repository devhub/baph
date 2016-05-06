import copy

from sqlalchemy import inspect
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.attributes import instance_dict
from sqlalchemy.orm.collections import MappedCollection
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.session import object_session
from sqlalchemy.orm.util import identity_key

from baph.db.orm import ORM
from baph.utils.collections import duck_type_collection


orm = ORM.get()
Base = orm.Base

def reload_object(instance):
  """
  Reloads an instance with the correct polymorphic subclass
  """
  cls, pk_vals = identity_key(instance=instance)
  mapper = inspect(cls)
  pk_cols = [col.key for col in mapper.primary_key]
  pk = dict(zip(pk_cols, pk_vals))
  session = object_session(instance)
  session.expunge(instance)
  instance = session.query(cls) \
    .with_polymorphic('*') \
    .filter_by(**pk) \
    .one()
  return instance

def get_polymorphic_subclass(instance):
  """
  Return the appropriate polymorphic subclass for an instance which may not 
  have been loaded polymorphically, by checking the discriminator against
  the polymorphic map of the base class. for non-polymorphic classes, it
  returns the class
  """
  cls, pk = identity_key(instance=instance)
  base_mapper = inspect(cls)
  if base_mapper.polymorphic_on is None:
    # this is not a polymorphic class
    return cls
  discriminator = base_mapper.polymorphic_on.key
  poly_ident = getattr(instance, discriminator)
  poly_mapper = base_mapper.polymorphic_map[poly_ident]
  return poly_mapper.class_

def get_cloning_rules(cls):
  """
  Returns default cloning rules for a class
  """
  rules = getattr(cls, '__cloning_rules__', {})
  return copy.deepcopy(rules)

def get_default_excludes(cls):
  """
  By default, exclude pks and fks
  """
  mapper = inspect(cls)
  exclude_cols = set()

  for table in mapper.tables:
    exclude_cols.update(table.primary_key.columns)
    for fkc in table.foreign_key_constraints:
      exclude_cols.update(fkc.columns)

  props = map(mapper.get_property_by_column, exclude_cols)
  keys = set(prop.key for prop in props)
  return keys

def is_column(prop):
  return prop.strategy_wildcard_key == 'column'

def is_relationship(prop):
  return prop.strategy_wildcard_key == 'relationship'


class CloneEngine(object):
  def __init__(self, user=None, ruleset=None, registry=None):
    self.root = None
    self.user = user
    self.ruleset = ruleset or {}
    if registry is None:
      registry = {}
    self.registry = registry

  @staticmethod
  def get_relationship_kwargs(prop, ruleset, rule_keys):
    related_class = prop.mapper.class_
    related_ruleset = get_cloning_rules(related_class)
    related_ruleset.update(ruleset)
    related_rule_keys = ['%s.%s' % (rule_key, prop.key) for rule_key in rule_keys]
    return {
      'ruleset': related_ruleset,
      'rule_keys': related_rule_keys,
      }

  @staticmethod
  def get_rules(rules, rule_keys):
    """
    Returns the first set of rules with a matching key
    """
    #print '  possible keys:'
    #for rule_key in rule_keys:
    #  print '    ', rule_key
    for rule_key in rule_keys:
      if rule_key in rules:
        #print '  matched key:', rule_key
        return copy.deepcopy(rules[rule_key])
    return {}

  @property
  def user_id(self):
    if not self.user:
      return None
    cls, pk = identity_key(instance=self.user)
    if len(pk) > 1:
      raise Exception('chown cannot used for multi-column user pks. To '
        'specify ownership for a user with a multi-column pk, add the '
        'relationship attribute key to the chown rules')
    return pk[0]

  def get_column_data(self, instance, rules):
    """
    returns a dict of data containing values from all non-relation keys
    (relations are included if they are 'chown' or 'preserve' types)
    """
    cls = type(instance)
    mapper = inspect(cls)

    excludes = get_default_excludes(cls)
    #print 'default excludes:', excludes
    excludes.update(rules.get('excludes', []))

    data = {}    

    for prop in mapper.column_attrs:
      " start with all non-excluded column attrs "
      key = prop.key
      if key in excludes:
        continue
      data[key] = getattr(instance, key)

    for key in rules.get('preserve', []):
      " copy over preserved values with no modifications "
      data[key] = getattr(instance, key)

    for key in rules.get('chown', []):
      " assign given user to ownership fields "
      prop = mapper.get_property(key)
      if is_column(prop):
        data[key] = self.user_id
      elif is_relationship(prop):
        data[key] = self.user
      else:
        # wut
        raise Exception('unknown type: %s' % prop.strategy_wildcard_key)
    #print 'col data:', data
    return data

  def clone_collection(self, value, **kwargs):
    if not value:
      return value

    collection_class = duck_type_collection(value)

    if collection_class == dict:
      # mapped onetomany or manytomany
      items = {}
      for name, item in value.items():
        new_item = self.clone_obj(item, **kwargs)
        items[name] = new_item
      return items
    elif collection_class == list:
      # onetomany or manytomany
      items = []
      for item in value:
        new_item = self.clone_obj(item, **kwargs)
        items.append(new_item)
      return items
    else:
      # onetoone or manytoone
      item = self.clone_obj(value, **kwargs)
      return item

  def clone_obj(self, instance, ruleset=None, rule_keys=None):
    #print '\ncloning:', instance
    base_cls, pk = identity_key(instance=instance)
    #print '  identity key:', (base_cls, pk)
    if (base_cls, pk) in self.registry:
      #print '  found in registry'
      return self.registry[(base_cls, pk)]

    cls = get_polymorphic_subclass(instance)
    if type(instance) != cls:
      # reload the obj with the correct polymorphic subclass
      instance = reload_object(instance)
    mapper = inspect(cls)

    if ruleset is None:
      ruleset = self.ruleset
    if not ruleset:
      ruleset = get_cloning_rules(cls)

    rule_keys = rule_keys or []
    rule_keys = rule_keys + [base_cls.__name__]
    rules = self.get_rules(ruleset, rule_keys)
    callback = rules.get('callback', None)

    data = self.get_column_data(instance, rules)
    clone = cls(**data)
    self.registry[(base_cls, pk)] = clone

    is_root = self.root is None
    if is_root:
      # this is the top-level clone call
      self.root = clone

    for key in rules.get('relations', []) + rules.get('relinks', []):
      " copy over all specified relationships "
      #print 'relation:', key
      if not mapper.has_property(key):
        # a missing property is either a mistake, or a property which only 
        # exists on certain polymorphic subclasses. Due to the latter 
        # possibility, we can't raise an error, so we just skip it
        continue

      prop = mapper.get_property(key)
      if not is_relationship(prop):
        raise Exception('"relations" must contain only relationships')

      value = getattr(instance, key)
      #print '  value:', value

      kwargs = self.get_relationship_kwargs(prop, ruleset, rule_keys)
      value = self.clone_collection(value, **kwargs)
      setattr(clone, key, value)

    if callback:
      clone = callback(clone, self.user, self.root)
    
    if is_root:
      # reset the root so the engine can be re-used
      self.root = None
    return clone

def clone_obj(obj, user, rules={}, registry={}, path=None, root=None,
              cast_to=None):
    """Clones an object and returns the clone.

    Default behavior is to only process columns (no relations), and
    to skip any columns which are primary keys or foreign keys.
    
    :param obj: the sqlalchemy instance to clone
    
    :param user: the user object to be used to populate fields given in
        the 'chown' directive. relations will be populated with user,
        and columns will be populated with user.id
        
    :param rules: a dictionary of rules, associating each 'path' with a
        series of directives which provide information on how to handle
        the fields present on the instance. More info later.
        
    :param registry: a mapping of class/pk comblinations linked to the
        cloned instances which were generated from those keys. This field
        should never be initialized by the user, and is used only to pass
        the updated registry to recursive calls to clone_obj
        
    :param path: the path to be used when looking up the rules for the
        current object. This is an internally used field, and users should
        not ever need to provide a value here.
        
    :param root: the top-level object. This is set automatically, and users
        should not need to use this field
    
    Rule dictionaries can contain the following directives:
    
    :callback: contains a function to be called on the cloned object after
        all properties have been processed. The given function must take 3
        args (active instance, active user, root object) and return the
        modified instance.

    :chown: (columns & relations) contains a list of properties to be
        populated with the provided 'user' param. Columns will be populated
        with user.id, while relations will receive the user object.

    :excludes: (columns) contains a list of properties to skip when processing
        the columns on the object. relations are ignored unless explcitly
        specified, so adding a relation property here isn't necessary. primary
        and foreign keys are also skipped by default.

    :preserve: (columns & relations) contains a list of properties to be
        copied EXACTLY during the cloning process. This can be used to
        create references to existing global objects which should not
        be cloned, such as foreign keys to a master 'category' list, etc.
        
    :relations: (relations) contains a list of properties which should be
        cloned along with the parent. When drilling down to process a relation,
        the relation name is added to the current 'path' value, and the new
        path is used to look up the rules for processing the related objects.

    :relinks: (relations) contains a list of properties to be 'relinked' during
        the cloning process. During a relink, the registry is first checked, to
        see if the target object was already cloned earlier in the cloning 
        process, and if found, that object will be used instead of creating a
        new one.
    """
    engine = CloneEngine(user=user, registry=registry)
    clone = engine.clone_obj(obj)
    return clone

def full_instance_dict(obj, rules={}, path=None):
    if path is None:
        path = obj.__class__.__mapper__.base_mapper.class_.__name__
    if not rules and not hasattr(obj, '__cloning_rules__'):
        raise Exception('object %s cannot be serialized' % obj)
    rules = rules or obj.__cloning_rules__

    local_rules = rules.get(path, {})
    data = {}
    for prop in class_mapper(obj.__class__).iterate_properties:
        if isinstance(prop, ColumnProperty):
            data[prop.key] = getattr(obj, prop.key)
        elif isinstance(prop, RelationshipProperty):
            if not prop.key in local_rules.get('relations', []):
                continue
            rel_path = '.'.join([path,prop.key])
            v = getattr(obj, prop.key)

            if isinstance(v, Base):
                val = full_instance_dict(v, rules, rel_path)
            elif isinstance(v, list):
                val = []
                for i in v:
                    if isinstance(i, Base):
                        val.append(full_instance_dict(i, rules, rel_path))
                    else:
                        val.append(i)
            elif isinstance(v, dict):
                # collection_class = MappedCollection
                val = {}
                for i,k in v.items():
                    if isinstance(k, Base):
                        val[i] = full_instance_dict(k, rules, rel_path)
                    else:
                        val[i] = k
            else:
                val = v
            data[prop.key] = val
        continue
    return data