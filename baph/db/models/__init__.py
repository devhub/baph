# -*- coding: utf-8 -*-
'''\
:mod:`baph.db.models` -- Base SQLAlchemy Models
===============================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>

'''
from django.utils.encoding import smart_str, smart_unicode
from sqlalchemy import String, Unicode, UnicodeText
from unicodedata import bidirectional

from baph.db.models import signals
from baph.db.models.base import Base
from baph.db.models.loading import (get_apps, get_app, get_models, get_model,
    get_app_errors, register_models)


class Model(object):
    '''Base object for all SQLAlchemy models. Makes sure that all string
    values are properly converted into Unicode. This object assumes that
    either the subclassed object also has a base class of
    :attr:`baph.db.orm.ORM.Base`, or the :class:`~baph.db.orm.Mapify`
    decorator was used on the object. This is because the ``__table__``
    attribute is needed for the column type check to work properly.

    :param \*\*kwargs: name-value pairs which set model properties.
    '''

    def __init__(self, **kwargs):
        for name, value in kwargs.iteritems():
            setattr(self, name, value)

    def update(self, data):
        '''Updates an SQLAlchemy model object's properties using a dictionary.

        :param data: The data to update the object properties with.
        :type data: :class:`dict`
        '''
        for key, value in data.iteritems():
            if hasattr(self, key) and getattr(self, key) != value:
                setattr(self, key, value)

    def to_dict(self):
        '''Creates a dictionary out of the column properties of the object.
        This is needed because it's sometimes not possible to just use
        :data:`__dict__`.

        :rtype: :class:`dict`
        '''
        __dict__ = dict([(key, val) for key, val in self.__dict__.iteritems()
                         if not key.startswith('_sa_')])
        if len(__dict__) == 0:
            return dict([(col.name, getattr(self, col.name))
                         for col in self.__table__.c])
        else:
            return __dict__


class CustomPropsModel(Model):
    '''Subclassed Model for SQLAlchemy models which use custom descriptors.'''

    def to_dict(self):
        '''Overrides the :meth:`Model.to_dict` method because of the way
        that inherited columns are handled.
        '''
        return dict([(x.key, getattr(self, x.key))
                     for x in self.__mapper__.iterate_properties
                     if not hasattr(x, 'primaryjoin') and \
                        not x.key.startswith('_')])
