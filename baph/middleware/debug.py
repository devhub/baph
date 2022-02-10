# -*- coding: utf-8 -*-
'''\
===========================================================
:mod:`baph.middleware.debug` -- Debug Middleware for Django
===========================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
'''

from __future__ import absolute_import
from coffin.common import env
from django.conf import settings
from django.http import HttpResponse, HttpResponseServerError

ERROR_PAGE = u'''\
<!DOCTYPE html>
<html>
<head>
<title>Django: INVALID RESPONSE</title>
</head>
<body>
<header><h1 style="color:red">INVALID RESPONSE</h1></header>
<p>The response below is <strong>not</strong> an <code>HttpResponse</code>
object. Please correct this.</p>
<pre><code>{{ response|pprint|escape }}</code></pre>
</body>
</html>
'''


class ResponseDebugMiddleware(object):
    '''Middleware which creates a very ugly error page if a view does not
    return a :class:`django.http.HttpResponse` object, and the Django instance
    is running in ``DEBUG`` mode.
    '''

    def process_response(self, request, response):
        if settings.DEBUG and not isinstance(response, HttpResponse):
            template = env.from_string(ERROR_PAGE)
            return HttpResponseServerError(template.render({
                'response': response,
            }))
        return response
