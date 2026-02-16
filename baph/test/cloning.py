import copy
import inspect as pyinspect

from sqlalchemy import inspect
from sqlalchemy.ext.associationproxy import ASSOCIATION_PROXY
from sqlalchemy.ext.orderinglist import OrderingList

from baph.db.models.cloning import *
from baph.db.models.utils import identity_key
from baph.utils.collections import duck_type_collection


def is_polymorphic(cls):
  mapper = inspect(cls).base_mapper
  return mapper.polymorphic_on is not None

def get_polymorphic_base(cls):
  mapper = inspect(cls).base_mapper
  if mapper.polymorphic_map in (None, {}):
    return cls
  poly_key = mapper.polymorphic_on.key
  default = get_default_value(cls, poly_key)
  return mapper.polymorphic_map[default].class_

def get_class_and_base_class(cls):
  """
  Returns a list containing the class and the base class (if polymorphic)
  """
  classes = [cls]
  base = get_polymorphic_base(cls)
  if base != cls:
    classes.append(base)
  return classes

def get_class_and_subclasses(cls):
  """
  Returns a list containing the class and all polymorphic subclasses
  """
  classes = []
  mapper = inspect(cls).base_mapper
  if mapper.polymorphic_map not in (None, {}):
    poly_key = mapper.polymorphic_on.key
    default = get_default_value(cls, poly_key)
    base_cls = mapper.polymorphic_map[default].class_
    for mapper_ in mapper.polymorphic_map.values():
      if mapper_.class_ in classes:
        # already present in the class list
        continue
      if mapper_.class_ == base_cls:
        # this should be last, so more specific classes have priority
        continue
      classes.append(mapper_.class_)
    classes.append(base_cls)
  else:
    classes.append(cls)
  return classes

def get_default_value(obj, key):
  """
  Returns the default value for an attribute
  """
  if pyinspect.isclass(obj):
    cls = obj
  else:
    cls = type(obj)
  attr = getattr(cls, key)
  while attr.extension_type == ASSOCIATION_PROXY:
    attr = attr.remote_attr
  prop = attr.property
  column = prop.columns[0]
  default = column.default
  if default:
    return default.arg
  return default

def get_relation_rules(cls, key):
  if not hasattr(cls, key):
    return None
  rules = {}
  mapper = inspect(cls)
  prop = mapper.get_property(key)
  remote_cls = prop.mapper.class_
  rules = get_cloning_rules(remote_cls)
  for k, v in rules.items():
    v['_source'] = remote_cls
  return (remote_cls, rules)


class CloningTestMixin(object):

  def get_default_rules(self, cls, suffix=None):
    if not hasattr(cls, '__cloning_rules__'):
      return {}
    key = cls.__name__
    if suffix is not None:
      key += suffix
    if key not in cls.__cloning_rules__:
      return {}
    return cls.__cloning_rules__[key]

  def get_applicable_rules(self, cls, path=None):
    if path is None:
      return self.get_default_rules(cls)

    valid_terminators = get_class_and_base_class(cls)

    attrs = path.split('.')
    root_classname = attrs.pop(0)
    root_cls = cls._decl_class_registry[root_classname]

    rule_keys = [root_classname]
    mapper = inspect(root_cls)
    if mapper != mapper.base_mapper:
      # include the base class
      rule_keys.append(mapper.base_mapper.class_.__name__)

    if hasattr(root_cls, '__cloning_rules__'):
      rules = copy.deepcopy(root_cls.__cloning_rules__)
    else:
      rules = {}

    current_classes = [root_cls]

    while attrs:
      attr = attrs.pop(0)
      if attrs:
        next_attr = attrs[0]
      else:
        next_attr = None

      classes = set()
      for c in current_classes:
        new_classes = get_class_and_subclasses(c)
        for new_class in new_classes:
          classes.add(new_class)

      rule_keys = ["%s.%s" % (key, attr) for key in rule_keys]

      new_rules = {}
      current_classes = set()

      for c in classes:
        base_cls = get_polymorphic_base(c)
        info = get_relation_rules(c, attr)
        if not info:
          continue

        remote_cls, remote_rules = info
        remote_mapper = inspect(remote_cls)
        remote_is_polymorphic = is_polymorphic(remote_cls)

        if len(attrs) == 0:
          # this is the last step in the relation chain
          if remote_cls not in valid_terminators:
            # for the last relation, skip non-matching rules
            continue
          else:
            # use the explicitly defined class instead of the class which was
            # introspected from the relationship (because it may be a 
            # polymorphic base)
            rule_keys.extend([i.__name__ for i in valid_terminators])
        elif len(attrs) == 1:
          # for the step prior to last, exclude any classes which lack
          # the specified attribute
          if remote_is_polymorphic:
            remote_base = get_polymorphic_base(remote_cls)
            if remote_base == remote_cls:
              # always pass the base class through
              pass
            else:
              # a polymorphic subclass which lacks the specified attribute
              # skip this
              continue
          elif not hasattr(remote_cls, next_attr):
            continue
          rule_keys.append(remote_cls.__name__)
          current_classes.add(remote_cls)
        else:
          # for interim relations, branch through all possible subclasses
          rule_keys.append(remote_cls.__name__)
          current_classes.add(remote_cls)

        new_rules.update(remote_rules)

      new_rules.update(rules)
      rules = new_rules

    for rule_key in rule_keys:
      # test the potential keys in order to find the applicable ruleset
      if rule_key in rules:
        return rules[rule_key]
    return {}

  def check_base_columns(self, old, new, rules):
    columns = get_default_columns(type(old)) \
      - set(rules.get('preserve', [])) \
      - set(rules.get('excludes', [])) \
      - set(rules.get('relations', [])) \
      - set(rules.get('relinks', [])) \
      - set(rules.get('chown', [])) \
      - set(rules.get('data', {}).keys())
    for key in columns:
      default = get_default_value(old, key)
      old_value = getattr(old, key)
      new_value = getattr(new, key)
      self.assertEqual(old_value, new_value,
        'field "%s" was not copied over during cloning' % key)

  def check_chown_rules(self, old, new, rules):
    user_values = (self.user, self.user.id)
    for key in rules.get('chown', []):
      old_value = getattr(old, key)
      new_value = getattr(new, key)
      self.assertNotIn(old_value, user_values,
        'initial user for field "%s" is the same as the cloning user. '
        'chown rule cannot be tested' % key)
      self.assertIn(new_value, user_values,
        'field "%s" was not chowned during cloning' % key)

  def check_exclude_rules(self, old, new, rules):
    for key in rules.get('excludes', []):
      if not hasattr(old, key):
        # TODO: fix this
        # this is here to handle properties on polymorphic subclasses
        continue
      default = get_default_value(old, key)
      old_value = getattr(old, key)
      new_value = getattr(new, key)
      if key not in rules.get('default_ok', []):
        self.assertNotEqual(old_value, default,
          'value for field "%s" is equal to the default field value. '
          'exclude rule cannot be tested' % key)
      self.assertNotEqual(old_value, new_value,
        'field "%s" was not excluded during cloning' % key)

  def check_preserve_rules(self, old, new, rules):
    columns = set(rules.get('preserve', [])) \
      - set(rules.get('data', {}).keys())
    for key in columns:
      if not hasattr(old, key):
        # TODO: fix this
        # this is here to handle properties on polymorphic subclasses
        continue
      default = get_default_value(old, key)
      old_value = getattr(old, key)
      new_value = getattr(new, key)
      if key not in rules.get('default_ok', []):
        self.assertNotEqual(old_value, default,
          'value for field "%s" is equal to the default field value. '
          'preserve rule cannot be tested' % key)
      self.assertEqual(old_value, new_value,
        'field "%s" was not preserved during cloning' % key)

  def check_relations_rules(self, old, new, rules, path):
    keys = rules.get('relations', []) + rules.get('relinks', [])
    cls = type(old)
    mapper = inspect(cls)
    for key in keys:
      prop = mapper.get_property(key)
      remote_cls = prop.mapper.class_
      classname = remote_cls.__name__

      old_value = getattr(old, key)
      new_value = getattr(new, key)
      new_path = "%s.%s" % (path, key)
      collection_class = duck_type_collection(old_value)
      if collection_class:
        self.compare_collections(old_value, new_value, new_path, classname)
      else:
        self.compare_objects(old_value, new_value, new_path)

  def normalize_collections(self, old, new):
    self.assertEqual(type(old), type(new),
      'Collections have different classes. (initial=%s, cloned=%s)'
      % (type(old), type(new)))
    if type(old) == OrderingList:
      collection_class = OrderingList
    else:
      collection_class = duck_type_collection(old)

    if collection_class == OrderingList:
      # ordering is important here, so we pass through unmodified
      pass
    elif collection_class == dict:
      # we want to compare objects with matching keys, so we order
      # the objects by key
      self.assertItemsEqual(old.keys(), new.keys(),
        'mapped collections have different keys')
      old = [i[1] for i in sorted(old.items())]
      new = [i[1] for i in sorted(new.items())]
    elif collection_class == list:
      # this is an unordered list, so we need to manually order
      # related items to prevent future tests from failing
      new_ = []
      for obj in old:
        ident = identity_key(instance=obj)
        clone = self.registry[ident]
        if isinstance(clone, tuple):
          # this is an identity key
          idents = {identity_key(instance=i): i for i in new}
          self.assertIn(clone, idents)
          new_.append(idents[clone])
        else:
          # this is an actual object
          self.assertIn(clone, new)
          new_.append(clone)
      new = new_
    return (old, new)

  def compare_collections(self, old, new, path, cls_name, extra_rules=None):
    self.assertGreater(len(old), 0,
      'Initial %s count is 0. %s cloning cannot be tested'
      % (cls_name, cls_name))
    self.assertEqual(len(old), len(new),
      'Cloned %s count differs from initial %s count '
      '(initial has %s, clone has %s)'
      % (cls_name, cls_name, len(old), len(new)))
    old, new = self.normalize_collections(old, new)
    for old_, new_ in zip(old, new):
      self.compare_objects(old_, new_, path, extra_rules)

  def compare_objects(self, old, new, path, extra_rules=None, data=None):
    self.assertEqual(type(old), type(new))
    if not old:
      return
    rules = self.get_applicable_rules(type(old), path)
    if extra_rules:
      rules.update(extra_rules)
    if data:
      # data contains values applied to the objects which override the
      # default behavior
      rules['data'] = data
    ident = identity_key(instance=old)
    clone = self.registry[ident]
    if isinstance(clone, tuple):
      # this is an identity key
      self.assertEqual(clone, identity_key(instance=new))
    else:
      # this is an actual object
      self.assertEqual(clone, new)
    self.check_base_columns(old, new, rules)
    self.check_chown_rules(old, new, rules)
    self.check_exclude_rules(old, new, rules)
    self.check_preserve_rules(old, new, rules)
    self.check_relations_rules(old, new, rules, path)
