from baph.db.orm import ORM
from dhplatform.test.loading import get_apps
from django.core.serializers.python import Serializer as _Serializer
from django.db import DEFAULT_DB_ALIAS

orm = ORM.get()

class Serializer(_Serializer):
    pass

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
        for (field_name, field_value) in d.iteritems():
            if isinstance(field_value, str):
                field_value = smart_unicode(field_value, 
                    options.get("encoding", settings.DEFAULT_CHARSET), 
                    strings_only=True)
            data[field_name] = field_value

        yield Model(**data)

def _get_model(model_identifier):
    """
    Helper to look up a model from an "app_label.module_name" string.
    """
    registry = orm.Base._decl_class_registry
    Model = registry.get(model_identifier, None)
    if Model is None:
        raise base.DeserializationError(u"Invalid model identifier: '%s'" \
            % model_identifier)
    return Model
