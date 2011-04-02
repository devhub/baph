# -*- coding: utf-8 -*-
'''\
:mod:`baph.test.oauth` -- TestCase for OAuth-based APIs
=======================================================
'''

from baph.utils.importing import import_any_attr
from django.core.urlresolvers import reverse
from oauth2 import Consumer, Request, Token
from .base import BaseTestCase

parse_qsl = import_any_attr(['urlparse', 'cgi'], 'parse_qsl')


class OAuthTestCase(BaseTestCase):
    '''A TestCase with helper functions for testing OAuth-based APIs.

    The following class attributes need to be defined in the subclass:

    ``signature_method``
        The instance of the signature method from :mod:`oauth2`. For example,
        :class:`oauth2.SignatureMethod_HMAC_SHA1`.

    The following object attributes need to be set in :meth:`setUp`:

    ``consumer``
        An object that has a ``key`` attribute and a ``secret`` attribute, of
        which both values exist in the store.
    '''

    @staticmethod
    def get_oauth_path(view):
        return reverse('baph.piston.oauth.views.%s' % view)

    @staticmethod
    def get_url(path):
        return 'http://testserver%s' % path

    def get_request_token(self, callback='oob'):
        path = self.get_oauth_path('get_request_token')
        url = self.get_url(path)
        request = Request.from_consumer_and_token(self.consumer, None, 'GET',
                                                  url,
                                                  {'oauth_callback': callback})
        request.sign_request(self.signature_method, self.consumer, None)

        response = self.client.get(path, request)
        self.assertEquals(response.status_code, 200)

        params = dict(parse_qsl(response.content))
        return Token(params['oauth_token'], params['oauth_token_secret'])

    def authorize_request_token(self, request_token_key, username, password):
        path = self.get_oauth_path('authorize_request_token')
        self.client.login(username=username, password=password)
        return self.client.post(path, {
            'oauth_token': request_token_key,
            'authorize_access': None,
        })

    def get_access_token(self, callback):
        path = self.get_oauth_path('get_access_token')
        url = self.get_url(path)
        consumer = Consumer(self.consumer.key, self.consumer.secret)
        request_token = self.get_request_token(callback)
        response = self.authorize_request_token(request_token.key)
        params = dict(parse_qsl(response['Location'][len(callback)+1:]))

        request_token.set_verifier(params['oauth_verifier'])

        request = Request.from_consumer_and_token(consumer, request_token,
                                                  'POST', url)
        request.sign_request(self.signature_method, consumer, request_token)

        response = self.client.post(path, request)
        self.assertEquals(response.status_code, 200)

        params = dict(parse_qsl(response.content))
        return Token(params['oauth_token'], params['oauth_token_secret'])
