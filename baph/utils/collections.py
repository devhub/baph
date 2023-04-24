# -*- coding: utf-8 -*-
'''\
:mod:`baph.utils.collections` -- Custom container data types
============================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
.. moduleauthor:: Gerald Thibault <jt@devhub.com>

.. note:: This module requires either Python >= 2.7 or the `ordereddict`_
          package installed.

.. _ordereddict: http://pypi.python.org/pypi/ordereddict
'''

from __future__ import absolute_import

from collections import defaultdict, OrderedDict

from six import PY2
from sqlalchemy.ext.associationproxy import _AssociationDict
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


def flatten(l):
    " flattens nested iterable into a single iterable "
    ltype = type(l)
    l = list(l)
    i = 0
    while i < len(l):
        while isinstance(l[i], (list, tuple)):
            if not l[i]:
                l.pop(i)
                i -= 1
                break
            else:
                l[i:i+1] = l[i]
        i += 1
    return ltype(l)


if PY2:
    class OrderedDefaultDict(defaultdict, OrderedDict):
        '''A :class:`dict` subclass with the characteristics of both
        :class:`~collections.defaultdict` and :class:`~collections.OrderedDict`.
        '''
        def __init__(self, default_factory, *args, **kwargs):
            defaultdict.__init__(self, default_factory)
            OrderedDict.__init__(self, *args, **kwargs)
else:
    OrderedDefaultDict = defaultdict
