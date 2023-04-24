# -*- coding: utf-8 -*-
'''\
:mod:`baph.utils.importing` -- Import-related Utilities
=======================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
.. moduleauthor:: Gerald Thibault <jt@evomediagroup.com>
'''
from __future__ import absolute_import

import logging
import pkgutil

from django.conf import settings
from django.utils.importlib import import_module


logger = logging.getLogger(__name__)


def import_any_module(modules, raise_error=True):
    '''Imports the first module available from a list of modules.

    :param modules: The list of modules to look for.
    :type modules: a :class:`list` of :class:`str`
    :returns: A module or :const:`None`, if no module could be found and
              ``raise_error`` is :const:`False`.
    '''
    mod = None
    for module in modules:
        try:
            mod = import_module(module)
        except ImportError:
            pass
        else:
            break
    if mod is None and raise_error:
        raise ImportError('Could not import any of %s' % (modules,))

    return mod


def import_attr(modules, attr, raise_error=True):
    '''Imports one or more attributes from the first module in a list of
    available modules.

    :param modules: The list of modules to look for.
    :type modules: a :class:`list` of :class:`str`
    :param attr: One or more attributes to search for.
    :type attr: either a :class:`str` or a :class:`list` of :class:`str`
    :returns: The attribute, a :class:`tuple` of attributes, or :const:`None`,
              if no module/attribute could be found and ``raise_error`` is
              :const:`False`.
    '''
    if isinstance(attr, str):
        attrs = [attr]
    else:
        attrs = attr
    result = tuple()
    module = import_any_module(modules, raise_error)
    if module:
        for a in attrs:
            if raise_error:
                result += (getattr(module, a),)
            else:
                result += (getattr(module, a, None),)
    if len(result) == 0:
        result = None
    elif len(result) == 1:
        result = result[0]
    return result


def import_all_attrs(modules, use_all=True, raise_error=True):
    '''Like :func:`import_attr`, where ``attr`` is ``*``, i.e.,
    ``from foo import *``.

    :param modules: The list of modules to look for.
    :type modules: a :class:`list` of :class:`str`
    :param bool use_all: Whether to use the ``__all__`` attribute of a module,
                         if it exists.
    :returns: A :class:`dict` of zero or more attributes, or :const:`None`,
              if no module/attribute could be found and ``raise_error`` is
              :const:`False`.
    '''
    result = {}
    module = import_any_module(modules, raise_error)
    if module:
        attrs = None
        if use_all:
            attrs = getattr(module, '__all__', None)
        if attrs is None:
            attrs = [x for x in dir(module) if not x.startswith('__')]
        for a in attrs:
            if raise_error:
                result[a] = getattr(module, a)
            else:
                result[a] = getattr(module, a, None)
    else:
        result = None
    return result


def import_any_attr(modules, attr, raise_error=True):
    '''Imports an attribute from the first module that has said attribute.

    :param modules: The list of modules to look in.
    :type modules: a :class:`list` of :class:`str`
    :param attr: One or more attributes to search for.
    :type attr: either a :class:`str` or a :class:`list` of :class:`str`
    :returns: The attribute or :const:`None`, if no module/attribute could be
              found and ``raise_error`` is :const:`False`.
    '''
    result = None
    # This hack avoids ImproperlyConfigured errors due to usage of backends
    # that Django doesn't know about but SQLAlchemy does.
    old_default = settings.DATABASES['default']
    settings.DATABASES['default'] = {'ENGINE': ''}
    try:
        mod = None
        for module in modules:
            try:
                mod = import_module(module)
            except ImportError:
                pass
            else:
                if hasattr(mod, attr):
                    result = getattr(mod, attr)
                    break
        if mod is None and raise_error:
            raise ImportError('Could not import any of %s' % (modules,))
    finally:
        # Revert the hack from above
        settings.DATABASES['default'] = old_default
    if result is None and raise_error:
        raise AttributeError('Could not locate %s in any of %s' %
                             (attr, modules))
    return result


def module_to_filename(module_name):
    pkg = pkgutil.get_loader(module_name)
    return pkg.filename


def remove_class(cls, name):
    from baph.db.models.loading import unregister_models
    subs = cls.__subclasses__()
    subs = [s for s in subs if s.__module__ != cls.__module__]
    if not subs:
        # unregister from AppCache
        unregister_models(cls._meta.app_label, cls._meta.model_name)

        # remove from SA class registry
        if cls.__name__ in cls._decl_class_registry:
            del cls._decl_class_registry[cls.__name__]

        # remove from SA module registry
        root = cls._decl_class_registry['_sa_module_registry']
        tokens = cls.__module__.split(".")
        while tokens:
            token = tokens.pop(0)
            module = root.get_module(token)
            for token in tokens:
                module = module.get_module(token)
            module._remove_item(cls.__name__)

        # delete the table
        cls.metadata.remove(cls.__table__)
