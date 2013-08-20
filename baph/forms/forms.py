from django import forms
from django.utils.datastructures import SortedDict
from sqlalchemy import *
from sqlalchemy.ext.associationproxy import AssociationProxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.util import has_identity
from sqlalchemy.sql.expression import _BinaryExpression, _Label

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
    }

def fields_for_model(model, fields=None, exclude=None, widgets=None, 
                                                formfield_callback=None):
    field_list = []
    ignored = []
    
    for k,prop in model.all_properties:
        if fields and not k in fields:
            # ignore fields not in explicit list
            continue
        if exclude and k in exclude:
            # ignore excluded fields
            continue
        if isinstance(prop, RelationshipProperty):
            # skip relations (manually add to form if needed)
            continue
        if isinstance(prop, ColumnProperty) and prop.columns[0].primary_key:
            # do not allow manipulation of primary key
            continue

        if isinstance(prop, hybrid_property):
            # this is a hybrid property
            if not prop.fset:
                # this is readonly, do not add to form
                continue
            expr = prop.expr(model)
            if not isinstance(expr, _BinaryExpression):
                raise Exception('hybrid_property expr is not a BinaryExpression')
            data_type = type(expr.type)
            kwargs = {
                'required': False,
                }
        else:
            # this is a column property
            col = prop.columns[0]
            data_type = col.type.__class__
            if isinstance(col, _Label):
                # this is an aliased expression, with no setter
                continue
            if col.default is not None:
                default = col.default.arg
            else:
                default = col.default
            kwargs = {
                'required': data_type != Boolean \
                    and not col.nullable and not col.default,
                'initial': default,
                'label': col.info.get('label', None),
                'help_text': col.info.get('help_text', None),
                }

        if widgets and k in widgets:
            kwargs['widget'] = widgets[k]

        field = FIELD_MAP.get(data_type, forms.CharField)

        if formfield_callback is None:
            formfield = field(**kwargs)
        elif not callable(formfield_callback):
            raise TypeError('formfield_callback must be a function or callable')
        else:
            formfield = formfield_callback(field, **kwargs)

        if formfield:
            field_list.append( (k,formfield) )
        else:
            ignored.append(k)

    field_dict = SortedDict(field_list)
    if fields:
        field_dict = SortedDict(
            [(f, field_dict.get(f)) for f in fields
                if ((not exclude) or (exclude and f not in exclude)) and (f not in ignored)]
        )
    return field_dict

class SQLAModelFormOptions(object):
    def __init__(self, options=None):
        self.model = getattr(options, 'model', None)
        self.fields = getattr(options, 'fields', None)
        self.exclude = getattr(options, 'exclude', None)
        self.exclude_on_create = getattr(options, 'exclude_on_create', [])
        self.exclude_on_update = getattr(options, 'exclude_on_update', [])
        self.exclude_on_nested = getattr(options, 'exclude_on_nested', [])
        self.widgets = getattr(options, 'widgets', None)

class SQLAModelFormMetaclass(type):
    def __new__(cls, name, bases, attrs):
        formfield_callback = attrs.pop('formfield_callback', None)
        try:
            parents = [b for b in bases if issubclass(b, SQLAModelForm)]
        except NameError:
            parents = None
        declared_fields = forms.forms.get_declared_fields(bases, attrs, False)
        new_class = super(SQLAModelFormMetaclass, cls) \
            .__new__(cls, name, bases, attrs)
        if not parents:
            return new_class

        if 'media' not in attrs:
            new_class.media = forms.widgets.media_property(new_class)
        opts = new_class._meta = SQLAModelFormOptions(getattr(new_class, 'Meta', None))
        if opts.model:
            # If a model is defined, extract form fields from it.
            fields = fields_for_model(opts.model, opts.fields,
                                      opts.exclude, opts.widgets, formfield_callback)
            # Override default model fields with any custom declared ones
            # (plus, include all the other declared fields).
            fields.update(declared_fields)
        else:
            fields = declared_fields
        new_class.declared_fields = declared_fields
        new_class.base_fields = fields
        return new_class

class BaseSQLAModelForm(forms.forms.BaseForm):
    def __init__(self, *args, **kwargs):
        instance = kwargs.pop('instance', None)
        nested = kwargs.pop('nested', False)
        super(BaseSQLAModelForm, self).__init__(*args, **kwargs)
        self.instance = instance
        if instance and has_identity(instance):
            excludes = self._meta.exclude_on_update[:]
        else:
            excludes = self._meta.exclude_on_create[:]
        if nested:
            excludes.extend(self._meta.exclude_on_nested)
        for k in excludes:
            if k in self.fields:
                del self.fields[k]
            
class SQLAModelForm(BaseSQLAModelForm):
    __metaclass__ = SQLAModelFormMetaclass



