from django.template.defaultfilters import slugify

from sqlalchemy import *
from sqlalchemy.orm import attributes
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.session import object_session


class AutoSlugField(ColumnProperty):
    def __init__(self, *args, **kwargs):
        max_length = kwargs.pop('max_length', 255)
        kwargs['type_'] = String(max_length)

        self.always_update = kwargs.pop('always_update', False)    
        self.populate_from = kwargs.pop('populate_from', None)
        self.index_sep = kwargs.pop('sep', '-')
        self.unique_with = kwargs.pop('unique_with', ())
        if isinstance(self.unique_with, basestring):
            self.unique_with = (self.unique_with,)

        self.slugify = kwargs.pop('slugify', slugify)
        assert hasattr(self.slugify, '__call__')

        if self.unique_with:
            kwargs['unique'] = False
        self.unique = kwargs.get('unique', False)
        self.nullable = kwargs.get('nullable', True)

        column = Column(*args, **kwargs)
        super(AutoSlugField, self).__init__(column)

    def generate_unique_slug(self, session, instance, slug):
        original_slug = slug
        default_lookups = tuple(
            (key, getattr(instance, key))
            for key in self.unique_with)
        ident = instance.pk_as_query_filters()
        index = 1

        while True:
            filters = dict(default_lookups, **{self.key: slug})
            conflicts = session.query(type(instance)) \
                               .filter_by(**filters) \
                               .filter(not_(instance.pk_as_query_filters())) \
                               .count()
            if not conflicts:
                return slug

            index += 1
            data = dict(slug=original_slug, sep=self.index_sep, index=index)
            slug = '%(slug)s%(sep)s%(index)d' % data

    def before_flush(self, session, add, instance):
        history = attributes.get_history(instance, self.key)
        value = getattr(instance, self.key)
        if self.always_update or (self.populate_from and not value):
            value = getattr(instance, self.populate_from)

        if value:
            slug = self.slugify(value)
        else:
            slug = None
            if not self.nullable:
                slug = instance.__class__.__name__.lower()

        if self.unique or self.unique_with:
            slug = self.generate_unique_slug(session, instance, slug)

        setattr(instance, self.key, slug)
