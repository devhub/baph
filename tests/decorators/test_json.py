# -*- coding: utf-8 -*-

from __future__ import absolute_import
from baph.test.base import BaseTestCase
from baph.decorators.json import json


class RenderJSONTestCase(BaseTestCase):
    '''Tests the render_to_json decorator.'''

    urls = 'tests.decorators.urls'

    def test_render_to_json(self):
        response = self.client.get('/test_render/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(json.loads(response.content), 'hello')


class JSONifyTestCase(BaseTestCase):
    '''Tests the JSONify decorator.'''

    urls = 'tests.decorators.urls'

    def test_basic(self):
        # non-AJAX
        response = self.client.get('/test_jsonify/basic/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'text/html; charset=utf-8')
        self.assertEqual(response.content, 'hello, world')

        # AJAX
        response = self.client.get('/test_jsonify/basic/',
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(json.loads(response.content), {
            'content': 'hello, world',
        })

    def test_basic_dict(self):
        # non-AJAX
        response = self.client.get('/test_jsonify/basic/dict/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'text/html; charset=utf-8')
        self.assertEqual(response.content, 'In a dict')

        # AJAX
        response = self.client.get('/test_jsonify/basic/dict/',
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(json.loads(response.content), {
            'content': 'In a dict',
            'other': 'miscellaneous',
        })

    def test_alternate_renderer_function(self):
        response = self.client.get('/test_jsonify/alt_renderer/func/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'text/html; charset=utf-8')
        self.assertEqual(response.content,
                         '<b>alternate renderer function</b>')

    def test_alternate_renderer_template(self):
        response = self.client.get('/test_jsonify/alt_renderer/tpl/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'text/html; charset=utf-8')
        self.assertEqual(response.content,
                         '<i>alternate renderer template</i>')

    def test_invalid_dict(self):
        self.assertRaises(ValueError, self.client.get,
                          '/test_jsonify/invalid_dict/')

    def test_invalid_return_value(self):
        self.assertRaises(ValueError, self.client.get,
                          '/test_jsonify/invalid_return_value/')

    def test_method_param(self):
        # non-AJAX
        response = self.client.get('/test_jsonify/method_param/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'text/html; charset=utf-8')
        self.assertEqual(response.content, 'In a method')

        # AJAX
        response = self.client.get('/test_jsonify/method_param/',
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(json.loads(response.content), {
            'content': 'In a method',
        })

    def test_redirect(self):
        response = self.client.get('/test_jsonify/redirect/')
        self.assertEqual(response.status_code, 302)
