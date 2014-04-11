import collections
from itertools import tee
from types import FunctionType

from django import forms
from django.core import validators
from django.utils.encoding import smart_text, force_text, force_bytes
from django.utils.text import capfirst
from sqlalchemy import *
from sqlalchemy.ext.associationproxy import ASSOCIATION_PROXY
from sqlalchemy.ext.declarative.clsregistry import _class_resolver
from sqlalchemy.ext.hybrid import HYBRID_PROPERTY, HYBRID_METHOD
from sqlalchemy.ext.orderinglist import OrderingList
from sqlalchemy.orm.collections import MappedCollection
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty

from baph.db import types
from baph.forms import fields


class NOT_PROVIDED:
    pass

def get_related_class_from_attr(attr):
    prop = attr.property
    related_cls = prop.argument
    if isinstance(related_cls, FunctionType):
        # lazy-loaded Model
        related_cls = related_cls()
    if hasattr(related_cls, 'is_mapper') and related_cls.is_mapper:
        # we found a mapper, grab the class from it
        related_cls = related_cls.class_
    if isinstance(related_cls, _class_resolver):
        related_cls = related_cls()
    return related_cls

def normalize_collection_class(collection_class):
    if isinstance(collection_class, FunctionType):
        # lambda-based evaluator, call it and check the type
        collection_class = type(collection_class())
    if collection_class is None:
        return None
    if collection_class in (dict, MappedCollection):
        return dict
    if collection_class in (set, list, OrderingList):
        return list
    raise Exception('Unknown collection_class: %s' % collection_class)

class Field(object):

    creation_counter = 0
    auto_creation_counter = -1

    def __init__(self, verbose_name=None, name=None, primary_key=False, 
                  unique=False, blank=False, nullable=False, editable=True, 
                  default=None, data_type=None, auto_created=False,
                  auto=False, collection_class=None, proxy=False,
                  help_text='', choices=None, uselist=False, required=False,
                ):
        self.name = name
        self.verbose_name = verbose_name or capfirst(self.name)
        self.primary_key = primary_key
        self._unique = unique
        self.blank, self.nullable = blank, nullable
        self.default = default
        self.editable = editable
        self.help_text = help_text
        self._choices = choices or []
        self.data_type = data_type
        self.collection_class = collection_class
        self.uselist = uselist
        self.required = required

        # Adjust the appropriate creation counter, and save our local copy.
        if auto_created:
            self.creation_counter = Field.auto_creation_counter
            Field.auto_creation_counter -= 1
        else:
            self.creation_counter = Field.creation_counter
            Field.creation_counter += 1

    @property
    def unique(self):
        return self._unique or self.primary_key

    def _get_choices(self):
        if isinstance(self._choices, collections.Iterator):
            choices, self._choices = tee(self._choices)
            return choices
        else:
            return self._choices
    choices = property(_get_choices)

    def has_default(self):
        """
        Returns a boolean of whether this field has a default value.
        """
        return self.default is not NOT_PROVIDED

    def get_default(self):
        """
        Returns the default value for this field.
        """
        if self.has_default():
            if callable(self.default):
                return self.default()
            return force_text(self.default, strings_only=True)
        return None

    def formfield(self, form_class=None, **kwargs):
        defaults = {'required': self.required,
                    'label': capfirst(self.verbose_name),
                    'help_text': self.help_text}
        if self.has_default():
            if callable(self.default):
                defaults['initial'] = self.default
                defaults['show_hidden_initial'] = True
            else:
                defaults['initial'] = self.get_default()
        # TODO: convert the 'choices' logic?
        ''' 
        if self.choices:
            include_blank = (self.blank or
                             not (self.has_default() or 'initial' in kwargs))
            defaults['choices'] = self.get_choices(include_blank=include_blank)
            defaults['coerce'] = self.to_python
            if self.null:
                defaults['empty_value'] = None
            if choices_form_class is not None:
                form_class = choices_form_class
            else:
                form_class = forms.TypedChoiceField
            # Many of the subclass-specific formfield arguments (min_value,
            # max_value) don't apply for choice fields, so be sure to only pass
            # the values that TypedChoiceField will understand.
            for k in list(kwargs):
                if k not in ('coerce', 'empty_value', 'choices', 'required',
                             'widget', 'label', 'initial', 'help_text',
                             'error_messages', 'show_hidden_initial'):
                    del kwargs[k]
        '''
        defaults.update(kwargs)
        if form_class is None:
            form_class = fields.NullCharField
        return form_class(**defaults)

    def clean(self, value):
        return self.as_form_field().clean(value)

    @classmethod
    def field_from_attr(cls, key, attr, model):
        kwargs = cls.field_kwargs_from_attr(key, attr, model)
        return cls(**kwargs)

    @classmethod
    def field_kwargs_from_attr(cls, key, attr, model):
        if attr.extension_type == ASSOCIATION_PROXY:
            kwargs = cls.field_kwargs_from_proxy(key, attr, model)
        elif isinstance(attr.property, ColumnProperty):
            kwargs = cls.field_kwargs_from_column(key, attr, model)
        elif isinstance(attr.property, RelationshipProperty):
            kwargs = cls.field_kwargs_from_relationship(key, attr, model)
        else:
            raise Exception('field_kwargs_from_attr can only be called on'
                             'proxies, columns, and relationships')
        return kwargs

    @classmethod
    def field_kwargs_from_column(cls, key, attr, model):
        kwargs = {'name': attr.key}
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
            kwargs['editable'] = not kwargs['auto'] and not attr.info.get('readonly', False)
            if type(col.type) == Boolean:
                kwargs['required'] = False
            elif not col.nullable and not kwargs['auto'] and not kwargs['default']: 
                kwargs['required'] = True
            else:
                kwargs['required'] = False
        else:
            # multiple join elements, make it readonly
            kwargs['editable'] = False

        return kwargs

    @classmethod
    def field_kwargs_from_relationship(cls, key, attr, model):
        kwargs = {'name': attr.key}
        prop = attr.property
        data_type = get_related_class_from_attr(attr)
        collection_class = prop.collection_class
        collection_class = normalize_collection_class(collection_class)
        if not collection_class and prop.uselist:
            collection_class = list

        kwargs['data_type'] = data_type
        kwargs['uselist'] = prop.uselist
        kwargs['editable'] = not prop.viewonly
        kwargs['nullable'] = True
        if collection_class:
            kwargs['collection_class'] = [collection_class]
        return kwargs

    @classmethod
    def field_kwargs_from_proxy(cls, key, attr, model):
        proxy = getattr(model, key)
        kwargs = cls.field_kwargs_from_attr(key, attr.remote_attr, model)

        collection_class = attr.local_attr.property.collection_class
        collection_class = normalize_collection_class(collection_class)
        if not collection_class and attr.local_attr.property.uselist:
            collection_class = list

        collections = kwargs.get('collection_class', [])
        if collection_class:
            collections.insert(0, collection_class)
        kwargs['collection_class'] = collections
        kwargs['name'] = key
        kwargs['proxy'] = True
        kwargs['nullable'] = True
        return kwargs
