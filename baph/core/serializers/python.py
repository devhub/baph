from __future__ import absolute_import

import six

from baph.core.serializers import base
from baph.db import DEFAULT_DB_ALIAS
from baph.db.models import get_apps
from baph.db.models.utils import identity_key
from baph.db.orm import Base
from baph.utils.encoding import smart_unicode


class Serializer(base.Serializer):
    """
    Serializes a QuerySet to basic Python objects.
    """

    internal_use_only = True

    def start_serialization(self):
        self._current = None
        self.objects = []

    def end_serialization(self):
        pass

    def start_object(self, obj):
        self._current = {}

    def end_object(self, obj):
        self.objects.append(self.get_dump_object(obj))
        self._current = None

    def get_dump_object(self, obj):
        model, pk = identity_key(instance=obj)
        self._current['__model__'] = model.__name__
        return self._current

    def getvalue(self):
        return self.objects


def Deserializer(object_list, **options):
    """
    Deserialize simple Python objects back into Django ORM instances.

    It's expected that you pass the Python objects themselves (instead of a
    stream or a string) to the constructor
    """
    db = options.pop('using', DEFAULT_DB_ALIAS)
    get_apps()
    for d in object_list:
        # Look up the model and starting build a dict of data for it.
        Model = _get_model(d.pop('__model__'))
        data = {}
        #data = {Model._meta.pk.attname : Model._meta.pk.to_python(d["pk"])}
        #m2m_data = {}

        # Handle each field
        for (field_name, field_value) in six.iteritems(d):
            if isinstance(field_value, bytes):
                field_value = smart_unicode(field_value, 
                    options.get("encoding", settings.DEFAULT_CHARSET), 
                    strings_only=True)
            data[field_name] = field_value

        yield Model(**data)


def _get_model(model_identifier):
    """
    Helper to look up a model from an "app_label.module_name" string.
    """
    registry = Base._decl_class_registry
    Model = registry.get(model_identifier, None)
    if Model is None:
        raise base.DeserializationError(u"Invalid model identifier: '%s'" \
            % model_identifier)
    return Model
