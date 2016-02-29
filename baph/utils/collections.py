# -*- coding: utf-8 -*-
'''\
:mod:`baph.utils.collections` -- Custom container data types
============================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>

.. note:: This module requires either Python >= 2.7 or the `ordereddict`_
          package installed.

.. _ordereddict: http://pypi.python.org/pypi/ordereddict
'''

from __future__ import absolute_import

from collections import defaultdict, OrderedDict

from sqlalchemy.ext.associationproxy import (
    _AssociationList, _AssociationDict, _AssociationSet)
from sqlalchemy.util import duck_type_collection as sqla_duck_type_collection


def duck_type_collection(specimen, default=None):
    " does the same thing as the sqla function, but handles proxy dict "
    guess = sqla_duck_type_collection(specimen, default=None)
    if guess is not None:
        return guess

    isa = isinstance(specimen, type) and issubclass or isinstance
    if isa(specimen, _AssociationDict):
        return dict
    return default

class OrderedDefaultDict(defaultdict, OrderedDict):
    '''A :class:`dict` subclass with the characteristics of both
    :class:`~collections.defaultdict` and :class:`~collections.OrderedDict`.
    '''
    def __init__(self, default_factory, *args, **kwargs):
        defaultdict.__init__(self, default_factory)
        OrderedDict.__init__(self, *args, **kwargs)

class LazyDict(dict):

    def __init__(self, func, *args, **kwargs):
        dict.__init__(self)
        self.initialized = False
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def populate(self):
        data = self.func(*self.args, **self.kwargs)
        if not isinstance(data, dict):
            raise Exception('function did not return a dict')
        self.update(data)
        self.initialized = True

    def __getitem__(self, key):
        if not self.initialized:
            self.populate()
        return dict.__getitem__(self, key)

    def get(self, key, default=None):
        if not self.initialized:
            self.populate()
        return dict.get(self, key, default)

if __name__ == '__main__':
    items = [
        _AssociationList,
        _AssociationDict,
        _AssociationSet,
    ]
    for item in items:
        print (sqla_duck_type_collection(item), duck_type_collection(item))