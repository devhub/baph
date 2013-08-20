from types import FunctionType

from django import forms
from django.utils.text import capfirst
from sqlalchemy import *
from sqlalchemy.ext.associationproxy import ASSOCIATION_PROXY
from sqlalchemy.ext.hybrid import HYBRID_PROPERTY, HYBRID_METHOD
from sqlalchemy.ext.orderinglist import OrderingList
from sqlalchemy.orm.collections import MappedCollection
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty

from baph.db import types
from baph.forms import fields


FIELD_MAP = {
    String:         forms.CharField,
    Text:           forms.CharField,
    Unicode:        forms.CharField,
    UnicodeText:    forms.CharField,
    Integer:        forms.IntegerField,
    Float:          forms.FloatField,
    DateTime:       forms.DateTimeField,
    Date:           forms.DateField,
    Time:           forms.TimeField,
    Boolean:        forms.BooleanField,
    types.Json:     fields.JsonField,
    types.List:     fields.ListField,
    types.Dict:     fields.DictField,
    object:        fields.ObjectField,
    }
COLLECTION_MAP = {
    OrderingList:   types.List,
    MappedCollection:   types.Dict,
    }

class ModelField(object):
    def __init__(self, key, data_type=None, data_collection=None, auto=False,
                 default=None, nullable=True, unique=False, readonly=False,
                 local=True, uselist=False):
        self.key = key
        self.data_type = data_type
        self.data_collection = data_collection
        self.auto = auto
        self.default = default
        self.nullable = nullable
        self.unique = unique
        self.readonly = readonly
        self.local = local
        self.uselist = uselist
        
        self.verbose_name = capfirst(self.key)

    @property
    def required(self):
        if self.data_type == Boolean:
            return False
        return not (self.nullable or self.default or self.auto)

    def as_form_field(self):
        from baph.db.models import Base
        if self.data_collection in COLLECTION_MAP:
            type_ = COLLECTION_MAP[self.data_collection]
        elif self.uselist:
            type_ = types.List
        elif issubclass(self.data_type, Base):
            type_ = object
        else:
            type_ = self.data_type
        kwargs = {
            'required': self.required,
            'initial': self.default,
            }
        field = FIELD_MAP[type_](**kwargs)
        return field

    def clean(self, value):
        return self.as_form_field().clean(value)

    def __repr__(self):
        return '<ModelField: key=%s, data_type=%s, data_collection=%s, ' \
            'auto=%s, default=%s, nullable=%s, unique=%s, readonly=%s, ' \
            'local=%s' % (self.key, self.data_type, self.data_collection,
            self.auto, self.default, self.nullable, self.unique,
            self.readonly, self.local)

    @classmethod
    def get_attr_from_proxy(cls, proxy):
        if proxy.remote_attr.extension_type == ASSOCIATION_PROXY:
            return cls.get_attr_from_proxy(proxy.remote_attr)
        return proxy.remote_attr

    @classmethod
    def from_sqla_attribute(cls, key, attr):
        if attr.is_mapper:
            return None
        elif attr.extension_type == HYBRID_METHOD:
            return None
        elif attr.extension_type == HYBRID_PROPERTY:
            field = cls.from_hybrid(key, attr)
        elif attr.extension_type == ASSOCIATION_PROXY:
            field = cls.from_proxy(key, attr)
        elif isinstance(attr.property, ColumnProperty):
            field = cls.from_column(key, attr)
        elif isinstance(attr.property, RelationshipProperty):
            field = cls.from_relationship(key, attr)

    @classmethod
    def from_column(cls, key, attr, raw=False):
        kwargs = {}
        col = attr.property.columns[0]
        kwargs['data_type'] = type(col.type)
        if len(col.proxy_set) == 1:
            # single column
            kwargs['auto'] = col.primary_key \
                and type(col.type) == Integer \
                and col.autoincrement
            kwargs['default'] = col.default
            kwargs['nullable'] = col.nullable
            kwargs['unique'] = col.unique
            kwargs['readonly'] = attr.info.get('readonly', False)
        else:
            # multiple join elements, make it readonly
            kwargs['readonly'] = True
        if raw:
            return kwargs
        return cls(key, **kwargs)
        
    @classmethod
    def from_relationship(cls, key, attr, raw=False):
        kwargs = {}
        prop = attr.property
        data_type = prop.argument
        if isinstance(data_type, FunctionType):
            # lazy-loaded attr that hasn't been evaluated yet
            data_type = data_type()
        elif getattr(data_type, 'is_mapper', False):
            data_type = data_type.class_

        data_collection = prop.collection_class
        if isinstance(data_collection, FunctionType):
            # lambda-based evaluator, call it and check the type
            data_collection = type(data_collection())

        kwargs['data_type'] = data_type
        kwargs['data_collection'] = data_collection
        kwargs['uselist'] = prop.uselist
        kwargs['readonly'] = prop.viewonly
        kwargs['local'] = False
        if raw:
            return kwargs
        return cls(key, **kwargs)

    @classmethod
    def from_hybrid(cls, key, attr, raw=False):
        kwargs = {}
        expr = attr.expr(self.model)
        kwargs['data_type'] = type(expr.type)
        kwargs['readonly'] = not attr.fset
        if raw:
            return kwargs
        return cls(key, **kwargs)

    @classmethod
    def from_proxy(cls, key, attr, raw=False, model=None):
        proxy = getattr(model, key)
        attr = cls.get_attr_from_proxy(proxy)
        prop = attr.property
        if isinstance(prop, ColumnProperty):
            kwargs = cls.from_column(key, attr, raw=True)
        elif isinstance(prop, RelationshipProperty):
            kwargs = cls.from_relationship(key, attr, raw=True)
        data_collection = proxy.local_attr.property.collection_class
        if data_collection:
            data_collection = type(data_collection())
        kwargs['data_collection'] = data_collection
        kwargs['local'] = False
        if raw:
            return kwargs
        return cls(key, **kwargs)
