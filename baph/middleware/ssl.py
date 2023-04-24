# -*- coding: utf-8 -*-
'''\
:mod:`baph.middleware.ssl` -- SSL Redirect Middleware
=====================================================

.. moduleauthor:: Daniel Rust <daniel@evomediagroup.com>

Based on <http://djangosnippets.org/snippets/880/>, which was based on
<http://djangosnippets.org/snippets/240/>, which is licensed under the
"Python" license (for some reason). This presumably means the `Python Software
Foundation License, version 2 <http://python.org/psf/license/>`_.
'''

from __future__ import absolute_import
from django.conf import settings
from django.http import HttpResponseRedirect

SSL = 'SSL'


class SSLRedirect(object):
    '''A middleware that allows you to specify which views require SSL (or
    not) in ``urls.py``. This requires that a settings variable,
    ``SSL_DOMAINS``, is set with a list of domains that handle HTTPS URLS
    properly.

    Example:

    .. code-block:: python

       from coffin.conf.urls.defaults import patterns

       urlpatterns = patterns('foo.views',
           (r'^/$', 'front'),
           (r'^/signup$', 'signup', {'SSL': True}),
       )
    '''

    def process_view(self, request, view_func, view_args, view_kwargs):
        if SSL in view_kwargs:
            secure = view_kwargs[SSL]
            del view_kwargs[SSL]
        else:
            secure = False

        if secure != self.is_secure(request) and \
           request.META.get('HTTP_HOST') in getattr(settings,
                                                    'SSL_DOMAINS', []):
            return self.redirect(request, secure)

    def is_secure(self, request):
        return request.is_secure() or \
            request.META.get('X_HTTP_CONNECTION_TYPE') == 'https'

    def redirect(self, request, secure):
        protocol = 'https' if secure else 'http'
        new_url = '%s://%s%s' % (protocol, 
                                 request.get_host(),
                                 request.get_full_path())

        if settings.DEBUG and request.method == 'POST':
            raise RuntimeError('''\
Django can't perform a SSL redirect while maintaining POST data.
Please structure your views so that redirects only occur during GETs.''')

        return HttpResponseRedirect(new_url)
