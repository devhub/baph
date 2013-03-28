try:
    import json
except:
    import simplejson as json

from django import forms
from django.core import validators
from django.utils.translation import ugettext_lazy as _

from baph.db.orm import Base


class ObjectField(forms.Field):
    " allowed values must be sqlalchemy objects (result of resource hydration)"
    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return None
        if not isinstance(value, Base):
            raise forms.ValidationError(
                _(u'Provided data did not hydrate to an object'))        

class JsonField(forms.Field):

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return None
        if isinstance(value, basestring):
            try:
                value = json.loads(value)
            except:
                raise ValueError(_('JSON could not be deserialized'))
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
            raise ValueError(_('This field requires a list as input'))
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
            raise ValueError(_('This field requires a dict as input'))
        return value

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
            session = Session()
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
            session = Session()
            return session.query(self.model) \
                .filter(self.model.id.in_(value)) \
                .all()
        elif all(isinstance(v, self.model) for v in value):
            # list of instances
            return value
        raise ValueError(_('This field takes a list of pks or instances of %s' \
            % self.model))

