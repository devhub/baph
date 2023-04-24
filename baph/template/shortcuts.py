# -*- coding: utf-8 -*-

from __future__ import absolute_import
from baph.utils.importing import import_attr
import six
base_render_to_response = import_attr(['coffin.shortcuts'],
                                      ['render_to_response'])
RequestContext = import_attr(['coffin.template'], 'RequestContext')
get_template, select_template = \
    import_attr(['coffin.template.loader'],
                ['get_template', 'select_template'])

__all__ = ['render_to_string', 'render_to_response']


def render_to_response(template_name, dictionary=None, request=None,
                       mimetype=None):
    '''Render a template into a response object. Meant to be compatible with
    the function in :mod:`djangojinja2` of the same name, distributed with
    Jinja2, as opposed to the shortcut from Django. For that, see
    :func:`coffin.shortcuts.render_to_response`.
    '''
    request_context = RequestContext(request) if request else None
    return base_render_to_response(template_name, dictionary=dictionary,
                                   context_instance=request_context,
                                   mimetype=mimetype)


def render_to_string(template_or_template_name, dictionary=None, request=None):
    '''Render a template into a string. Meant to be compatible with the
    function in :mod:`djangojinja2` of the same name, distributed with Jinja2,
    as opposed to the shortcut from Django. For that, see
    :func:`coffin.shortcuts.render_to_string`.
    '''
    dictionary = dictionary or {}
    request_context = RequestContext(request) if request else None
    if isinstance(template_or_template_name, (list, tuple)):
        template = select_template(template_or_template_name)
    elif isinstance(template_or_template_name, six.string_types):
        template = get_template(template_or_template_name)
    else:
        # assume it's a template
        template = template_or_template_name
    if request_context:
        request_context.update(dictionary)
    else:
        request_context = dictionary
    return template.render(request_context)
