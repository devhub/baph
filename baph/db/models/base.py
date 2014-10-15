from __future__ import absolute_import
from collections import defaultdict
from importlib import import_module
import sys

from django.conf import settings
from django.forms import ValidationError
from sqlalchemy import event, inspect
from sqlalchemy.ext.associationproxy import ASSOCIATION_PROXY
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.ext.declarative.base import (_as_declarative, _add_attribute)
from sqlalchemy.ext.declarative.clsregistry import add_class
from sqlalchemy.ext.hybrid import HYBRID_PROPERTY, HYBRID_METHOD
from sqlalchemy.orm import mapper, object_session, class_mapper
from sqlalchemy.orm.attributes import instance_dict, instance_state
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.util import has_identity, identity_key
from sqlalchemy.schema import ForeignKeyConstraint

from baph.db import ORM
from baph.db.models import signals
from baph.db.models.loading import get_model, register_models
from baph.db.models.mixins import CacheMixin, ModelPermissionMixin, GlobalMixin
from baph.db.models.options import Options
from baph.db.models.utils import class_resolver, key_to_value
from baph.utils.importing import safe_import, remove_class


@compiles(ForeignKeyConstraint)
def set_default_schema(constraint, compiler, **kw):
    """ This overrides the formatting function used to render remote tables
        in foreign key declarations, because innodb (at least, perhaps others)
        requires explicit schemas when declaring a FK which crosses schemas """
    remote_table = list(constraint._elements.values())[0].column.table
   
    if remote_table.schema is None:
        default_schema = remote_table.bind.url.database
        constraint_schema = constraint.columns[0].table.schema
        if constraint_schema not in (default_schema, None):
            """ if the constraint schema is not the default, we need to 
                add a schema before formatting the table """
            remote_table.schema = default_schema
            value = compiler.visit_foreign_key_constraint(constraint, **kw)
            remote_table.schema = None
            return value
    return compiler.visit_foreign_key_constraint(constraint, **kw)

def constructor(self, **kwargs):
    cls = type(self)

    # auto-populate default values on init
    for attr in cls.__mapper__.all_orm_descriptors:
        if not hasattr(attr, 'property'):
            continue
        if not isinstance(attr.property, ColumnProperty):
            continue
        if attr.key in kwargs:
            continue
        if len(attr.property.columns) != 1:
            continue
        col = attr.property.columns[0]
        if not hasattr(col, 'default'):
            continue
        if col.default is None:
            continue
        default = col.default.arg
        if callable(default):
            setattr(self, attr.key, default({}))
        else:
            setattr(self, attr.key, default)

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

class Model(CacheMixin, ModelPermissionMixin, GlobalMixin):

    @classmethod
    def create(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def get_form_class(cls, *args, **kwargs):
        if not cls._meta.form_class:
            return None
        cls_path = cls._meta.form_class
        cls_mod, cls_name = cls_path.rsplit('.', 1)
        module = import_module(cls_mod)
        return getattr(module, cls_name)

    def update(self, data):
        for key, value in data.iteritems():
            if hasattr(self, key) and getattr(self, key) != value:
                setattr(self, key, value)       

    def delete(self):
        if has_identity(self):
            session = object_session(self)
            session.delete(self)
            session.commit()

    def to_dict(self):
        '''Creates a dictionary out of the column properties of the object.
        This is needed because it's sometimes not possible to just use
        :data:`__dict__`.

        :rtype: :class:`dict`
        '''
        __dict__ = dict([(key, val) for key, val in self.__dict__.iteritems()
                         if not key.startswith('_sa_')])
        if len(__dict__) == 0:
            for attr in inspect(type(self)).all_orm_descriptors:
                if not hasattr(attr, 'property'):
                    continue
                if not isinstance(attr.property, ColumnProperty):
                    continue
                __dict__[attr.key] = getattr(self, attr.key)
        return __dict__

    @property
    def is_deleted(self):
        return False

    def save(self, commit=False):
        from baph.db.orm import ORM
        orm = ORM.get()
        session = orm.sessionmaker()

        if commit:
            if not self in session:
                session.add(self)
            session.commit()

        

class ModelBase(type):

    def __init__(cls, name, bases, attrs):
        #print '%s.__init__(%s)' % (name, cls)
        found = False
        registry = cls._decl_class_registry
        if name in registry:
            found = True
        elif cls in registry.values():
            found = True
            add_class(name, cls)

        if '_decl_class_registry' not in cls.__dict__:
            if not found:
                _as_declarative(cls, name, cls.__dict__)

        type.__init__(cls, name, bases, attrs)


    def __new__(cls, name, bases, attrs):
        #print '%s.__new__(%s)' % (name, cls)
        req_sub = attrs.pop('__requires_subclass__', False)

        super_new = super(ModelBase, cls).__new__

        parents = [b for b in bases if isinstance(b, ModelBase) and
            not (b.__name__ == 'Base' and b.__mro__ == (b, object))]
        if not parents:
            return super_new(cls, name, bases, attrs)

        module = attrs.pop('__module__')
        new_class = super_new(cls, name, bases, {'__module__': module})

        # check the class registry to see if we created this already
        if name in new_class._decl_class_registry:
            return new_class._decl_class_registry[name]

        attr_meta = attrs.pop('Meta', None)
        if not attr_meta:
            meta = getattr(new_class, 'Meta', None)
        else:
            meta = attr_meta
        base_meta = getattr(new_class, '_meta', None)

        if getattr(meta, 'app_label', None) is None:
            model_module = sys.modules[new_class.__module__]
            kwargs = {"app_label": model_module.__name__.rsplit('.',1)[0]}
        else:
            kwargs = {}

        new_class.add_to_class('_meta', Options(meta, **kwargs))
        if base_meta:
            for k,v in vars(base_meta).items():
                if not getattr(new_class._meta, k, None):
                    setattr(new_class._meta, k, v)

        if new_class._meta.swappable:
            if not new_class._meta.swapped:
                # class is swappable, but hasn't been swapped out, so we create
                # an alias to the base class, rather than trying to create a new
                # class under a second name
                base_cls  = bases[0]
                base_cls.add_to_class('_meta', new_class._meta)
                register_models(base_cls._meta.app_label, base_cls)
                return base_cls

            # class has been swapped out
            model = safe_import(new_class._meta.swapped, [new_class.__module__])

            for b in bases:
                if not getattr(b, '__mapper__', None):
                    continue
                if not getattr(b, '_sa_class_manager', None):
                    continue
                subs = [c for c in b.__subclasses__() if c.__name__ != name]
                if any(c.__name__ != name for c in b.__subclasses__()):
                    # this base class has a subclass inheriting from it, so we
                    # should leave this class alone, we'll need it
                    continue
                else:
                    # this base class is used by no subclasses, so it can be
                    # removed from appcache/cls registry/mod registry
                    remove_class(b, name)
            return model

        # Add all attributes to the class.
        for obj_name, obj in attrs.items():
            new_class.add_to_class(obj_name, obj)
        
        if attrs.get('__abstract__', None):
            return new_class

        signals.class_prepared.send(sender=new_class)
        register_models(new_class._meta.app_label, new_class)
        return get_model(new_class._meta.app_label, name,
                         seed_cache=False, only_installed=False)

    def __setattr__(cls, key, value):
        _add_attribute(cls, key, value)

    def add_to_class(cls, name, value):
        if hasattr(value, 'contribute_to_class'):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)

    def get_prop_from_proxy(cls, proxy):
        if proxy.scalar:
            # column
            prop = proxy.remote_attr.property
        elif proxy.remote_attr.extension_type == ASSOCIATION_PROXY:
            prop = cls.get_prop_from_proxy(proxy.remote_attr)
        elif isinstance(proxy.remote_attr.property, RelationshipProperty):
            prop = proxy.remote_attr.property
        else:
            prop = proxy.remote_attr.property
        return prop

    @property
    def all_properties(cls):
        for key, attr in inspect(cls).all_orm_descriptors.items():
            if attr.is_mapper:
                continue
            elif attr.extension_type == HYBRID_METHOD:
                # not a property
                continue
            elif attr.extension_type == HYBRID_PROPERTY:
                prop = attr
            elif attr.extension_type == ASSOCIATION_PROXY:
                proxy = getattr(cls, key)
                prop = cls.get_prop_from_proxy(proxy)
            elif isinstance(attr.property, ColumnProperty):
                prop = attr.property
            elif isinstance(attr.property, RelationshipProperty):
                prop = attr.property
            yield (key, prop)

    @property
    def resource_name(cls):
        try:
            if cls.__mapper__.polymorphic_on is not None:
                return cls.__mapper__.primary_base_mapper.class_.resource_name
        except:
            pass
        return cls._meta.object_name

    def get_base_class(cls):
        """Returns the base class if polymorphic, else the class itself"""
        try:
            if cls.__mapper__.polymorphic_on is not None:
                return cls.__mapper__.primary_base_mapper.class_
        except:
            pass
        return cls


def get_declarative_base(**kwargs):
    return declarative_base(cls=Model, 
        metaclass=ModelBase,
        constructor=constructor,
        **kwargs)

if getattr(settings, 'CACHE_ENABLED', False):
    @event.listens_for(mapper, 'after_insert')
    @event.listens_for(mapper, 'after_update')
    @event.listens_for(mapper, 'after_delete')
    def kill_cache(mapper, connection, target):
        target.kill_cache()

@event.listens_for(Session, 'before_flush')
def check_global_status(session, flush_context, instances):
    """
    If global_parents is defined, we check the parents to see if any of them
    are global. If a global parent is found, we set the child to global as well
    """
    for target in session:
        if target._meta.global_parents:
            if target.is_globalized():
                continue
            for parent_rel in target._meta.global_parents:
                parent = key_to_value(target, parent_rel, raw=True)
                if parent and parent.is_globalized():
                    target.globalize(commit=False)
                    break

