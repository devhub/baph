# -*- coding: utf-8 -*-

from __future__ import absolute_import
from baph.test.base import BaseTestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse


def secure_view(request):
    return HttpResponse()


class SSLTestCase(BaseTestCase):
    '''Test case for the SSL redirect middleware.'''

    urls = 'ssl_urls'

    def setUp(self):
        self._ssl_domains = settings.SSL_DOMAINS
        settings.SSL_DOMAINS = [None]

    def tearDown(self):
        settings.SSL_DOMAINS = self._ssl_domains

    def test_middleware(self):
        path = reverse('test_ssl.secure_view')
        response = self.client.get(path, follow=True)
        self.assertRedirects(response, 'https://testserver%s' % path)
