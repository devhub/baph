import warnings

from baph.db import types
from baph.forms import fields
from django import forms
from django.forms.forms import BaseForm, get_declared_fields
from django.forms.util import ErrorList
from django.forms.widgets import media_property
from django.utils.datastructures import SortedDict
from sqlalchemy import *
from sqlalchemy.ext.associationproxy import AssociationProxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.sql.expression import _BinaryExpression, _Label


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

def model_to_dict(instance, fields=None, exclude=None):
    """
    Returns a dict containing the data in ``instance`` suitable for passing as
    a Form's ``initial`` keyword argument.

    ``fields`` is an optional list of field names. If provided, only the named
    fields will be included in the returned dict.

    ``exclude`` is an optional list of field names. If provided, the named
    fields will be excluded from the returned dict, even if they are listed in
    the ``fields`` argument.
    """
    # avoid a circular import
    #opts = instance._meta
    data = {}
    #for f in opts.concrete_fields + opts.many_to_many:
    for k, f in type(instance).all_properties:
        #if not f.editable:
        #    continue
        if fields and not k in fields:
            continue
        if exclude and k in exclude:
            continue
        data[k] = getattr(instance, k)
    return data
    
def fields_for_model(model, fields=None, exclude=None, widgets=None, 
                     formfield_callback=None, labels=None, help_texts=None,
                     error_messages=None):
    field_list = []
    ignored = []
    opts = model._meta

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
                }

        if widgets and k in widgets:
            kwargs['widget'] = widgets[k]
        if labels and k in labels:
            kwargs['label'] = labels[k]
        if help_texts and k in help_texts:
            kwargs['help_text'] = help_texts[k]
        if error_messages and k in error_messages:
            kwargs['error_messages'] = error_messages[k]

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

class ModelFormOptions(object):
    def __init__(self, options=None):
        self.model = getattr(options, 'model', None)
        self.fields = getattr(options, 'fields', None)
        self.exclude = getattr(options, 'exclude', None)
        self.widgets = getattr(options, 'widgets', None)
        self.labels = getattr(options, 'labels', None)
        self.help_texts = getattr(options, 'help_texts', None)
        self.error_messages = getattr(options, 'error_messages', None)
        self.exclude_on_create = getattr(options, 'exclude_on_create', [])
        self.exclude_on_update = getattr(options, 'exclude_on_update', [])
        self.exclude_on_nested = getattr(options, 'exclude_on_nested', [])

class ModelFormMetaclass(type):
    def __new__(cls, name, bases, attrs):
        formfield_callback = attrs.pop('formfield_callback', None)
        try:
            parents = [b for b in bases if issubclass(b, ModelForm)]
        except NameError:
            # We are defining ModelForm itself.
            parents = None
        declared_fields = get_declared_fields(bases, attrs, False)
        new_class = super(ModelFormMetaclass, cls) \
            .__new__(cls, name, bases, attrs)
        if not parents:
            return new_class

        if 'media' not in attrs:
            new_class.media = media_property(new_class)
        opts = new_class._meta = ModelFormOptions(getattr(new_class, 'Meta', None))

        if opts.model:
            # If a model is defined, extract form fields from it.
            if opts.fields is None and opts.exclude is None:
                # This should be some kind of assertion error once deprecation
                # cycle is complete.
                warnings.warn("Creating a ModelForm without either the 'fields' attribute "
                              "or the 'exclude' attribute is deprecated - form %s "
                              "needs updating" % name,
                              DeprecationWarning, stacklevel=2)

            '''
            if opts.fields == ALL_FIELDS:
                # sentinel for fields_for_model to indicate "get the list of
                # fields from the model"
                opts.fields = None
            '''
            fields = fields_for_model(opts.model, opts.fields, opts.exclude,
                                      opts.widgets, formfield_callback,
                                      opts.labels, opts.help_texts, 
                                      opts.error_messages)

            # make sure opts.fields doesn't specify an invalid field
            none_model_fields = [k for k, v in fields.items() if not v]
            missing_fields = set(none_model_fields) - \
                             set(declared_fields.keys())
            if missing_fields:
                message = 'Unknown field(s) (%s) specified for %s'
                message = message % (', '.join(missing_fields),
                                     opts.model.__name__)
                raise FieldError(message)
            # Override default model fields with any custom declared ones
            # (plus, include all the other declared fields).
            fields.update(declared_fields)
        else:
            fields = declared_fields
        new_class.declared_fields = declared_fields
        new_class.base_fields = fields
        return new_class
        
class BaseModelForm(BaseForm):
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                  initial=None, error_class=ErrorList, label_suffix=None,
                  empty_permitted=False, instance=None, nested=False):
        opts = self._meta
        if opts.model is None:
            raise ValueError('ModelForm has no model class specified')
        if instance is None:
            self.instance = opts.model()
            object_data = {}
        else:
            self.instance = instance
            object_data = model_to_dict(instance, opts.fields, opts.exclude)
        if initial is not None:
            object_data.update(initial)
        self._validate_unique = False
        self.nested = nested
        super(BaseModelForm, self).__init__(data, files, auto_id, prefix,
                                             object_data, error_class,
                                             label_suffix, empty_permitted)

class ModelForm(BaseModelForm):
    __metaclass__ = ModelFormMetaclass
