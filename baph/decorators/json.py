# -*- coding: utf-8 -*-
'''\
:mod:`baph.decorators.json` -- JSON-related decorators
======================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
.. moduleauthor:: JT Thibault <jt@evomediagroup.com>
'''

from __future__ import absolute_import

from baph.utils.importing import import_any_module, import_attr
import six
render_to_response = import_attr(['coffin.shortcuts'], 'render_to_response')
from django.http import (
    HttpResponse, HttpResponseRedirect, HttpResponseForbidden)
RequestContext = import_attr(['django.template'], 'RequestContext')
from functools import wraps
json = import_any_module(['json', 'simplejson', 'django.utils.simplejson'])


def data_to_json_response(data, **kwargs):
    '''Takes any input and converts it to JSON, wraps it in an
    :class:`~django.http.HttpResponse`, and sets the proper MIME type.

    :param data: The data to be serialized.
    :param \*\*kwargs: extra keyword parameters given to :func:`json.dumps`.
    :rtype: :class:`~django.http.HttpResponse`
    '''
    return HttpResponse(json.dumps(data, **kwargs),
                        mimetype='application/json')


def render_to_json(func, **json_kwargs):
    '''A decorator that takes the return value of the given function and
    converts it to JSON, wraps it in an :class:`~django.http.HttpResponse`,
    and sets the proper MIME type.
    '''

    @wraps(func)
    def handler(request, *args, **kwargs):
        '''Creates the wrapped function/method.'''
        return data_to_json_response(func(request, *args, **kwargs),
                                     **json_kwargs)

    return handler


class JSONify(object):
    '''Generic decorator that uses Django's
    :meth:`~django.http.HttpRequest.is_ajax` request method to return either:

    * A JSON dictionary containing a ``content`` key with the rendered data,
      embedded in an :class:`~django.http.HttpResponse` object.
    * An :class:`~django.http.HttpResponse`, using a template which wraps the
      data in a given HTML file.

    :param alternate_renderer: An alternate function which renders the content
                               into HTML and wraps it in an
                               :class:`~django.http.HttpResponse`.
                               Alternatively, if you specify a template name,
                               a default Jinja2-based renderer is used.
    :type alternate_renderer: :func:`callable` or :class:`str`
    :param method: Whether or not the wrapped function is actually a method.
    :type method: :class:`bool`
    :param \*\*kwargs: extra keyword parameters given to :func:`json.dumps`.
    '''

    def __init__(self, alternate_renderer=None, method=False, **kwargs):
        if alternate_renderer is None:
            self.renderer = self.render
        elif isinstance(alternate_renderer, six.string_types):
            # assume Jinja2 template
            self.renderer = self.render_jinja
            self.template = alternate_renderer
        else:
            self.renderer = alternate_renderer
        self.method = method
        self.json_kwargs = kwargs

    def __call__(self, func):
        '''Creates the wrapped function/method.'''

        @wraps(func)
        def func_handler(request, *args, **kwargs):
            data = func(request, *args, **kwargs)
            return self._handler(data, request)

        @wraps(func)
        def method_handler(method_self, request, *args, **kwargs):
            data = func(method_self, request, *args, **kwargs)
            return self._handler(data, request)

        if self.method:
            return method_handler
        else:
            return func_handler

    def _handler(self, data, request):
        if isinstance(data, six.string_types):
            data = {
                'content': data,
            }
        elif isinstance(data, (HttpResponseRedirect, HttpResponseForbidden)):
            return data
        if not (isinstance(data, dict) and 'content' in data):
            raise ValueError('''\
Your view needs to return a string, a dict with a "content" key, or a 301/403
HttpResponse object.''')

        if request.is_ajax():
            return data_to_json_response(data, **self.json_kwargs)
        else:
            return self.renderer(request, data)

    def render(self, request, data):
        '''The default renderer for the HTML content.

        :type request: :class:`~django.http.HttpRequest`
        :param data: The data returned from the wrapped function.
        :type data: :class:`dict` (must have a ``content`` key)
        :rtype: :class:`~django.http.HttpResponse`
        '''
        return HttpResponse(data['content'])

    def render_jinja(self, request, data):
        '''The default Jinja2 renderer.

        :type request: :class:`~django.http.HttpRequest`
        :param data: The data returned from the wrapped function.
        :type data: :class:`dict`
        :rtype: :class:`~django.http.HttpResponse`
        '''
        return render_to_response(self.template, data,
                                  context_instance=RequestContext(request))
