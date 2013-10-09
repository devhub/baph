from django.core.serializers.base import Serializer as BaseSerializer
from django.utils import six
from sqlalchemy import inspect
from sqlalchemy.orm.attributes import instance_dict
from sqlalchemy.orm.properties import ColumnProperty


class Serializer(BaseSerializer):
    def serialize(self, queryset, **options):
        self.options = options
        
        self.stream = options.pop("stream", six.StringIO())
        self.selected_fields = options.pop("fields", None)
        self.use_natural_keys = options.pop("use_natural_keys", False)
        
        self.start_serialization()
        self.first = True
        for obj in queryset:
            self.start_object(obj)
            for attr in inspect(type(obj)).all_orm_descriptors:
                if not attr.is_attribute:
                    continue
                if not isinstance(attr.property, ColumnProperty):
                    continue
                #if attr.property.columns[0].primary_key:
                #    continue
                if attr.name not in obj.__dict__:
                    continue
                self._current[attr.name] = obj.__dict__[attr.name]
            self.end_object(obj)
            if self.first:
                self.first = False
        self.end_serialization()
        return self.getvalue()
