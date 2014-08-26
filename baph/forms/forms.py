from django import forms
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
from sqlalchemy import *
from sqlalchemy import inspect
from sqlalchemy.ext.associationproxy import AssociationProxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.attributes import instance_dict
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.util import has_identity, identity_key
from sqlalchemy.sql.expression import _BinaryExpression, _Label

from baph.auth.models import Organization
from baph.db import types, ORM
from baph.forms import fields


FIELD_MAP = {
    String:         fields.NullCharField,
    Text:           fields.NullCharField,
    Unicode:        fields.NullCharField,
    UnicodeText:    fields.NullCharField,
    Integer:        forms.IntegerField,
    Float:          forms.FloatField,
    Numeric:        forms.FloatField,
    DateTime:       forms.DateTimeField,
    Date:           forms.DateField,
    Time:           forms.TimeField,
    Boolean:        forms.BooleanField,
    types.Json:     fields.JsonField,
    types.List:     fields.ListField,
    types.Dict:     fields.DictField,
    'collection':   fields.MultiObjectField,
    'object':       fields.ObjectField,
    }
ALL_FIELDS = '__all__'

orm = ORM.get()

def save_instance(form, instance, fields=None, fail_message='saved',
                  commit=True, exclude=None):
    """
    Saves bound Form ``form``'s cleaned_data into model instance ``instance``.

    If commit=True, then the changes to ``instance`` will be saved to the
    database. Returns ``instance``.
    """
    opts = instance._meta
    for k,v in form.cleaned_data.items():
        if k in form.data:
            try:
                # TODO: this fails when trying to reach the remote side
                # of an association_proxy when the interim node is None
                # find a better solution
                setattr(instance, k, v)
            except TypeError as e:
                continue
                
    if form.errors:
        raise ValueError("The %s could not be %s because the data didn't"
                         " validate." % (opts.object_name, fail_message))

# ModelForms

def model_to_dict(instance, fields=None, exclude=None):
    opts = instance._meta
    data = instance_dict(instance)
    for f in opts.fields:
        if issubclass(f.data_type, orm.Base):
            # skip relations
            continue

        if not f.editable:
            continue
        if fields and not f.name in fields:
            continue
        if exclude and f.name in exclude:
            continue
        try:
            data[f.name] = getattr(instance, f.name)
        except:
            pass
    return data

def fields_for_model(model, fields=None, exclude=None, widgets=None, 
                     formfield_callback=None, localized_fields=None,
                     labels=None, help_texts=None, error_messages=None):
    orm = ORM.get()
    Base = orm.Base
    field_list = []
    ignored = []
    opts = model._meta
    for f in sorted(opts.fields):
        if not f.editable:
            continue
        if fields is not None and not f.name in fields:
            continue
        if exclude and f.name in exclude:
            continue
        if issubclass(f.data_type, Base):
            # TODO: Auto-generate fields, control via 'fields' param
            continue

        kwargs = {}
        if widgets and f.name in widgets:
            kwargs['widget'] = widgets[f.name]
        if localized_fields == ALL_FIELDS or (localized_fields and f.name in localized_fields):
            kwargs['localize'] = True
        if labels and f.name in labels:
            kwargs['label'] = labels[f.name]
        if help_texts and f.name in help_texts:
            kwargs['help_text'] = help_texts[f.name]
        if error_messages and f.name in error_messages:
            kwargs['error_messages'] = error_messages[f.name]

        if f.collection_class:
            kwargs['form_class'] = FIELD_MAP['collection']
            kwargs['collection_class'] = f.collection_class
        elif issubclass(f.data_type, Base):
            kwargs['form_class'] = FIELD_MAP['object']
        else:
            kwargs['form_class'] = FIELD_MAP.get(f.data_type)
        if issubclass(f.data_type, Base):
            kwargs['related_class'] = f.data_type

        if f.nullable or f.blank:
            kwargs['required'] = False
        if f.max_length and 'collection_class' not in kwargs:
            kwargs['max_length'] = f.max_length

        if formfield_callback is None:
            formfield = f.formfield(**kwargs)
        elif not callable(formfield_callback):
            raise TypeError('formfield_callback must be a function or callable')
        else:
            formfield = formfield_callback(f, **kwargs)

        if formfield:
            field_list.append((f.name, formfield))
        else:
            ignored.append(f.name)

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
        self.exclude = getattr(options, 'exclude', [])
        self.exclude_on_create = getattr(options, 'exclude_on_create', [])
        self.exclude_on_update = getattr(options, 'exclude_on_update', [])
        self.exclude_on_nested = getattr(options, 'exclude_on_nested', [])
        self.widgets = getattr(options, 'widgets', None)
        self.localized_fields = getattr(options, 'localized_fields', None)
        self.labels = getattr(options, 'labels', None)
        self.help_texts = getattr(options, 'help_texts', None)
        self.error_messages = getattr(options, 'error_messages', None)


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
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, instance=None, nested=False, **kwargs):
        opts = self._meta
        exclude = list(opts.exclude)
        if opts.model is None:
            raise ValueError('ModelForm has no model class specified.')
        self.nested = nested
        if self.nested:
            exclude.extend(opts.exclude_on_nested)
        if instance is None:
            exclude.extend(opts.exclude_on_create)
            self.instance = opts.model()
            object_data = {}
        else:
            self.instance = instance
            object_data = model_to_dict(instance, opts.fields, exclude)
            if has_identity(instance):
                exclude.extend(opts.exclude_on_update)
            else:
                exclude.extend(opts.exclude_on_create)

        if initial is not None:
            object_data.update(initial)
        object_data.update(data)
        super(BaseSQLAModelForm, self).__init__(object_data, files, auto_id, prefix)

        for k in exclude:
            if k in self.fields:
                del self.fields[k]

    def save(self, commit=False):
        """
        Saves this ``form``'s cleaned_data into model instance
        ``self.instance``.

        If commit=True, then the changes to ``instance`` will be saved to the
        database. Returns ``instance``.
        """
        if not has_identity(self.instance):
            fail_message = 'created'
        else:
            fail_message = 'changed'
        return save_instance(self, self.instance, self._meta.fields,
                             fail_message, commit, self._meta.exclude)
        
class SQLAModelForm(BaseSQLAModelForm):
    __metaclass__ = SQLAModelFormMetaclass

    def clean_unique_field(self, key, **kwargs):
        orm = ORM.get()
        value = self.cleaned_data[key]
        print 'val=', value
        if value is None:
            return value
        filters = {
            key: value,
            }
        filters.update(kwargs)
        session = orm.sessionmaker()
        instance = session.query(self._meta.model) \
            .filter_by(**filters) \
            .filter_by(**kwargs) \
            .first()
        if instance and instance != self.instance:
            # this value is already in use
            raise forms.ValidationError(_('This value is already in use'))
        return value

    def clean_org_unique_field(self, key, **kwargs):
        orm = ORM.get()
        org_key = Organization._meta.model_name + '_id'
        value = self.cleaned_data[key]
        if value is None:
            return value
        filters = {
            org_key: Organization.get_current_id(),
            key: value,
            }
        filters.update(kwargs)
        session = orm.sessionmaker()
        instance = session.query(self._meta.model) \
            .filter_by(**filters) \
            .filter_by(**kwargs) \
            .first()
        if instance and instance != self.instance:
            # this value is already in use
            raise forms.ValidationError(_('This value is already in use'))
        return value


