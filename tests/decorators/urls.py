# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns

urlpatterns = patterns('tests.decorators.views',
    (r'^test_render/$', 'test_render'),
    (r'^test_jsonify/alt_renderer/func/$', 'test_jsonify_alt_renderer_func'),
    (r'^test_jsonify/alt_renderer/tpl/$', 'test_jsonify_alt_renderer_tpl'),
    (r'^test_jsonify/basic/$', 'test_jsonify_basic'),
    (r'^test_jsonify/basic/dict/$', 'test_jsonify_basic_dict'),
    (r'^test_jsonify/invalid_dict/$',
      'test_jsonify_invalid_dict'),
    (r'^test_jsonify/invalid_return_value/$',
      'test_jsonify_invalid_return_value'),
    (r'^test_jsonify/method_param/$', 'test_jsonify_method_param'),
    (r'^test_jsonify/redirect/$', 'test_jsonify_redirect'),
)
