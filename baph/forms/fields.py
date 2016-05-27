from importlib import import_module
import json

from django import forms
from django.core import validators
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _

from baph.utils.collections import duck_type_collection


def coerce_to_list(value):
    " forces value into list form "
    if isinstance(value, list):
        # we're all good here
        return value
    if isinstance(value, tuple):
        # cast to list
        return list(value)
    if isinstance(value, dict):
        # this has no ordering, so will probably break things
        return value.items()
    if isinstance(value, set):
        # this has no ordering, so will probably break things
        return list(value)
    return [value]

class NullCharField(forms.CharField):
    " CharField that does not cast None to '' "
    def to_python(self, value):
        "Returns a Unicode object."
        if isinstance(value, basestring):
            value = value.strip()
        if value in validators.EMPTY_VALUES:
            return None
        return super(NullCharField, self).to_python(value)

class MultiObjectField(forms.Field):
    """
    Field for handling of collections of objects
    """
    def __init__(self, related_class=None, collection_class=None, **kwargs):
        self.related_class = related_class
        if collection_class:
            # this needs to be a list
            collection_class = coerce_to_list(collection_class)
        else:
            collection_class = [list]
        self.collection_class = collection_class
        super(MultiObjectField, self).__init__(**kwargs)

    def validate_collection(self, data, collection_class=None):
        if collection_class is None:
            collection_class = self.collection_class[:]
        if collection_class == []:
            # we've drilled down through all collections, now we
            # check the class type if available
            if self.related_class and not isinstance(data, self.related_class):
                raise forms.ValidationError(
                    _('Expected %s, got %s') % (self.related_class, type(data)))
            return

        expected_class = collection_class.pop(0)
        found_class = duck_type_collection(data)
        if found_class != expected_class:
            raise forms.ValidationError(
                _('Expected %s, got %s') % (expected_class, found_class))

        values = data.itervalues() if isinstance(data, dict) else iter(data)
        for v in values:
            self.validate_collection(v, collection_class)

    def to_python(self, value):
        from baph.db.orm import Base
        if value in validators.EMPTY_VALUES:
            return None
        self.validate_collection(value)
        return value        

class ObjectField(forms.Field):
    " allowed values must be sqlalchemy objects (result of resource hydration)"
    def __init__(self, related_class=None, **kwargs):
        if not related_class:
            raise ImproperlyConfigured(u'No related class assigned to '
                                            'ObjectField')
        self.related_class = related_class
        super(ObjectField, self).__init__(**kwargs)

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return None
        if not isinstance(value, self.related_class):
            raise forms.ValidationError(
                _(u'Provided data did not hydrate to an object'))        
        return value

class JsonField(forms.CharField):

    def __init__(self, *args, **kwargs):
        content_length_func = kwargs.pop('content_length_func', None)
        super(JsonField, self).__init__(*args, **kwargs)
        if isinstance(content_length_func, basestring):
            module, func_name = content_length_func.rsplit('.', 1)
            module = import_module(module)
            content_length_func = getattr(module, func_name)
        self.content_length_func = content_length_func

    def _as_string(self, value):
        if isinstance(value, basestring):
            return value
        return unicode(value)

    def _get_content_length(self, value):
        """
        Returns the length of the data in bytes
        """
        string = self._as_string(value)
        func = self.content_length_func or len
        return func(string)

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return None
        if self.max_length:
            length = self._get_content_length(value)
            if length > self.max_length:
                raise forms.ValidationError(_('Max length for this field is '
                    '%s bytes') % self.max_length)

        if isinstance(value, basestring):
            try:
                value = json.loads(value)
            except:
                raise forms.ValidationError(_('JSON could not be deserialized'))
        return value

class ListField(JsonField):
    " allowed values must be in list form "
    def to_python(self, value):
        if value is None:
            return value
        if value in validators.EMPTY_VALUES:
            return []
        value = super(ListField, self).to_python(value)
        # sqlalchemy.ext.associationproxy._AssociationList (and similar) does 
        # not subclass list, so we check for __iter__ to determine validity
        if not hasattr(value, '__iter__') or hasattr(value, 'items'):
            raise forms.ValidationError(_('This field requires a list as input'))
        return value

class DictField(JsonField):
    " allowed values must be in dict form "
    def to_python(self, value):
        if value is None:
            return value
        if value in validators.EMPTY_VALUES:
            return {}
        value = super(DictField, self).to_python(value)
        # sqlalchemy.ext.associationproxy._AssociationDict does not subclass
        # dict, so we check for .items to determine validity
        if not hasattr(value, 'items'): 
            raise forms.ValidationError(_('This field requires a dict as input'))
        return value

# TODO: Test these
"""
class OneToManyField(ListField):
    " input from an html form will be a list of primary keys "
    " input from resource hydration will be the objects themselves "
    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop('model')
        super(OneToManyField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return None
        value = super(OneToManyField, self).to_python(value)
        if all(isinstance(v, int) for v in value):
            # list of primary keys
            session = orm.sessionmaker()
            return session.query(self.model) \
                .filter(self.model.id.in_(value)) \
                .all()
        elif all(isinstance(v, self.model) for v in value):
            # list of instances
            return value
        raise ValueError(_('This field takes a list of pks or instances of %s' \
            % self.model))

class ManyToManyField(ListField):
    " input from an html form will be a list of primary keys "
    " input from resource hydration will be the objects themselves "
    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop('model')
        super(ManyToManyField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return None
        value = super(ManyToManyField, self).to_python(value)
        if all(isinstance(v, int) for v in value):
            # list of primary keys
            session = orm.sessionmaker()
            return session.query(self.model) \
                .filter(self.model.id.in_(value)) \
                .all()
        elif all(isinstance(v, self.model) for v in value):
            # list of instances
            return value
        raise ValueError(_('This field takes a list of pks or instances of %s' \
            % self.model))
"""
