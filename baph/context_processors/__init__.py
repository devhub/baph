# -*- coding: utf-8 -*-
'''\
:mod:`baph.context_processors` -- Template Context Processors
=============================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
'''


def http(request):
    '''A restricted set of variables from the
    :class:`~django.http.HttpResponse` object.
    '''
    gzip = 'gzip' in request.META.get('HTTP_ACCEPT_ENCODING', '')
    return {
        'gzip_acceptable': gzip,
        'is_secure': request.is_secure(),
    }
