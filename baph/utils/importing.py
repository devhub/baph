# -*- coding: utf-8 -*-
'''\
:mod:`baph.utils.importing` -- Import-related Utilities
=======================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
.. moduleauthor:: Gerald Thibault <jt@evomediagroup.com>
'''
from __future__ import absolute_import
import ast
import logging
import pkgutil
import sys

from django.conf import settings
from django.utils.importlib import import_module


logger = logging.getLogger('baph_safe_import')

class ImportTransformer(ast.NodeTransformer):

    def __init__(self, modules):
        self.modules = modules
        super(ImportTransformer, self).__init__()

    def visit_ImportFrom(self, node):
        if node.module not in self.modules:
            " we're not monitoring imports from this module, handle as normal "
            self.generic_visit(node)
            return node

        code = ['import sys\n']
        for name in node.names:
            asname = name.asname or name.name
            logger.debug('[ImportTransformer] transforming node %s' % asname)
            if hasattr(sys.modules[node.module], name.name):
                """
                This was already loaded during the partial load, we'll replace
                the import with a raw call to sys.modules, to avoid a circular
                reference
                """
                line = "%s = sys.modules['%s'].%s\n" \
                    % (asname, node.module, name.name)
                logger.debug('[ImportTransformer] %s' % line.strip())
                code.append(line)
            else:
                logger.debug('[ImportTransformer] not loaded yet')
        code = ''.join(code)

        nodes = tuple([self.visit(n) for n in ast.parse(code).body])
        return nodes

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
        raise AttributeError('Could not locate %s in any of %s' % \
                             (attr, modules))
    return result

def module_to_filename(module_name):
    pkg = pkgutil.get_loader(module_name)
    return pkg.filename

def safe_import(path, replace_modules=[]):
    " input is a dotted path "
    
    
    logger.debug('safe_import called:\n\tpath=%s\n\treplace_modules=%s'
        % (path, replace_modules))
    if not replace_modules:
        raise ValueError('replace_modules must contain at least one value')

    mod, name = path.rsplit('.',1)
    filename = module_to_filename(mod)
    logger.debug('\tpath -> filename=%s' % filename)
    f = open(filename)
    code = f.read()
    f.close()

    if not mod in sys.modules:
        sys.modules[mod] = type(sys)(mod)
        sys.modules[mod].__file__ = filename

    node = ast.parse(code, filename)
    node = ImportTransformer(replace_modules).visit(node)
    node = ast.fix_missing_locations(node)

    while True:
        code = compile(node, filename, 'exec')
        logger.debug('\ttrying to exec node %s' % node)
        try:
            exec code in sys.modules[mod].__dict__
            logger.debug('\t\tsuccess')
            break
        except:
            exc_type, exc_value, tb_root = sys.exc_info()

            tb = tb_root
            while tb is not None:
                if tb.tb_frame.f_code.co_filename == filename:
                    break
                tb = tb.tb_next
            if tb is None:
                raise Exception('no tb frame contained an error in '
                    'the source file')
            logger.debug('\texception at line %s: %s' % (tb.tb_lineno, 
                                                         exc_value))

            last_valid_idx = None
            for i, item in enumerate(node.body):
                if item.lineno <= tb.tb_lineno:
                    last_valid_idx = i
                else:
                    break
            item = node.body[last_valid_idx]
            logger.debug('\t\tfailed node index=%s' % last_valid_idx)
            logger.debug('\t\tfailed node at line %s: %s' % (item.lineno,
                                                           item))

            if not last_valid_idx:
                raise Exception('tb line # didn\'t fall in any '
                    'ranges present in source file (how?)')
            del node.body[last_valid_idx]
            logger.debug('\t\tnode deleted, retrying exec')
            if len(node.body) == 0:
                raise Exception('Source AST was trimmed to zero trying to '
                    'eliminate circular import errors. "oops".')

    code = compile(node, filename, 'exec')
    exec code in sys.modules[mod].__dict__
    return getattr(sys.modules[mod], name)    

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
