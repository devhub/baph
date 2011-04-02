# -*- coding: utf-8 -*-

from baph.decorators.json import JSONify, render_to_json
from django.http import HttpResponse, HttpResponseRedirect


class TestObject(object):
    '''Test object for testing the method parameter of JSONify.'''

    @JSONify(method=True)
    def render(self, request):
        return 'In a method'


def alternate_renderer(request, data):
    return HttpResponse('<b>%s</b>' % data['content'])


@render_to_json
def test_render(request):
    return 'hello'


@JSONify(alternate_renderer=alternate_renderer)
def test_jsonify_alt_renderer_func(request):
    return 'alternate renderer function'


@JSONify(alternate_renderer='test_alt_renderer.html')
def test_jsonify_alt_renderer_tpl(request):
    return 'alternate renderer template'


@JSONify()
def test_jsonify_basic(request):
    return 'hello, world'


@JSONify()
def test_jsonify_basic_dict(request):
    return {
        'content': 'In a dict',
        'other': 'miscellaneous',
    }


@JSONify()
def test_jsonify_invalid_dict(request):
    return {
        'foo': 'bar',
    }


@JSONify()
def test_jsonify_invalid_return_value(request):
    return HttpResponse()


def test_jsonify_method_param(request):
    test_obj = TestObject()
    return test_obj.render(request)


@JSONify()
def test_jsonify_redirect(request):
    return HttpResponseRedirect('/')
