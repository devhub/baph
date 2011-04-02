# -*- coding: utf-8 -*-

from baph.auth.models import orm, User
from baph.piston.models import Consumer
from baph.test.oauth import OAuthTestCase
from baph.utils.importing import import_any_attr
from django.conf import settings
from oauth2 import Consumer as OAConsumer, Request, SignatureMethod_HMAC_SHA1
parse_qsl = import_any_attr(['urlparse', 'cgi'], 'parse_qsl')

BAPH_PISTON_OAUTH_STORE = 'baph.piston.oauth.store.sqlalchemy.ModelStore'
CALLBACK_URL = 'http://example.com/cb'


class OAuthTest(OAuthTestCase):
    '''Tests a basic OAuth-based API.'''

    urls = 'project.api.urls'

    signature_method = SignatureMethod_HMAC_SHA1()

    @classmethod
    def setUpClass(cls):
        super(OAuthTest, cls).setUpClass()
        cls.two_legged_api_path = '/two/'
        cls.two_legged_api_url = cls.get_url(cls.two_legged_api_path)
        cls.three_legged_api_path = '/three/'
        cls.three_legged_api_url = cls.get_url(cls.three_legged_api_path)

    def setUp(self):
        self.session = orm.sessionmaker()
        self.cuser = User.create_user('testoauth',
                                      'testoauth@example.com', 'testoauth')
        data = dict(name=u'Piston Test OAuth',
                    description=u'A test consumer for OAuth.',
                    session=self.session, user=self.cuser)
        self.consumer = Consumer.create(**data)
        self.old_store = getattr(settings, 'PISTON_OAUTH_STORE', None)
        settings.PISTON_OAUTH_STORE = BAPH_PISTON_OAUTH_STORE

    def tearDown(self):
        self.session.delete(self.cuser)
        self.session.delete(self.consumer)
        self.session.commit()
        del self.cuser
        del self.consumer
        settings.PISTON_OAUTH_STORE = self.old_store
        del self.old_store
        self.session.close()
        orm.sessionmaker_remove()

    def test_unauthorized(self):
        response = self.client.get(self.three_legged_api_path)
        self.assertEqual(response.status_code, 401)
        response = self.client.get(self.two_legged_api_path)
        self.assertEqual(response.status_code, 401)

    def test_get_request_token(self):
        self.get_request_token()

    def authorize_request_token(self, request_token_key):
        return super(OAuthTest,
                     self).authorize_request_token(request_token_key,
                                                   'testoauth', 'testoauth')

    def test_authorize_request_token_without_callback(self):
        request_token = self.get_request_token('oob')
        response = self.authorize_request_token(request_token.key)

        self.assertEquals(response.status_code, 200)

    def test_authorize_request_token_with_callback(self):
        request_token = self.get_request_token(CALLBACK_URL)
        response = self.authorize_request_token(request_token.key)

        self.assertEquals(response.status_code, 302)
        self.assert_(response['Location'].startswith(CALLBACK_URL))

    def test_get_access_token(self):
        self.get_access_token(CALLBACK_URL)

    def test_two_legged_api(self):
        request = Request.from_consumer_and_token(self.consumer, None, 'GET',
                                                  self.two_legged_api_url,
                                                  {'msg': 'expected response'})
        request.sign_request(self.signature_method, self.consumer, None)

        response = self.client.get(self.two_legged_api_path, request)
        self.assertEquals(response.status_code, 200)
        self.assertIn('world', response.content)

    def test_three_legged_api(self):
        consumer = OAConsumer(self.consumer.key, self.consumer.secret)
        access_token = self.get_access_token(CALLBACK_URL)

        request = Request.from_consumer_and_token(consumer, access_token,
                                                  'GET',
                                                  self.three_legged_api_url,
                                                  {'msg': 'expected response'})
        request.sign_request(self.signature_method, consumer,
                             access_token)

        response = self.client.get(self.three_legged_api_path, request)
        self.assertEquals(response.status_code, 200)
        self.assertIn('world', response.content)
