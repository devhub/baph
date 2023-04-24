# -*- coding: utf-8 -*-
'''\
:mod:`baph.utils.assets.jinja2` -- Jinja Static Assets Extensions
=================================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
'''

from __future__ import absolute_import

from django.conf import settings
from jinja2 import nodes
from jinja2.exceptions import TemplateSyntaxError
from jinja2.ext import Extension


class AssetExtension(Extension):
    '''Generates an XHTML tag for an asset. The URL is appended with the hash
    of the last git revision that the file was modified, for cache-busting
    purposes.

    This is an abstract base class.
    '''

    build_method = '_build_tag'

    def parse(self, parser):
        stream = parser.stream

        tag = next(stream)
        if stream.current.test('string'):
            path = parser.parse_primary()
        else:
            raise TemplateSyntaxError('''\
"%s" requires path to asset file, relative to STATICFILES_URL''' % tag.value,
                                      tag.lineno)
        while not parser.stream.current.type == 'block_end':
            next(parser.stream)
        result = self.call_method(self.build_method, args=[path])
        return nodes.Output([nodes.MarkSafe(result)]).set_lineno(tag.lineno)

    def _build_url(self, path):
        href = '%s%s' % (settings.STATICFILES_URL, path)
        revision = settings.STATICFILES_REVISIONS.get(path)
        if revision:
            href += '?%s' % revision
        return href

    def _build_url_for_ext(self, path, ext):
        return self._build_url('%s.%s' % (path, ext))


class AssetLinkExtension(AssetExtension):
    '''Generates a URL for a static file. If the file is version controlled,
    the URL is appended with the hash of its last git revision, for
    cache-busting purposes.

    Example:

    .. code-block:: jinja

       {% asset '/img/logo.png' %}

    To enable, add ``baph.utils.assets.jinja2.asset`` to
    :setting:`JINJA2_EXTENSIONS` in ``settings.py``.
    '''

    build_method = '_build_url'
    tags = set(['asset'])


class CSSAssetExtension(AssetExtension):
    '''Generates an XHTML link tag for a CSS file. The URL is appended with the
    hash of the last git revision that the file was modified, for cache-busting
    purposes.

    Example:

    .. code-block:: jinja

       {% css_asset '/css/style' %}

    To enable, add ``baph.utils.assets.jinja2.css_asset`` to
    :setting:`JINJA2_EXTENSIONS` in ``settings.py``.
    '''

    tags = set(['css_asset'])

    def _build_tag(self, path):
        return u'<link rel="stylesheet" type="text/css" href="%s" />' % \
               self._build_url_for_ext(path, 'css')


class JSAssetExtension(AssetExtension):
    '''Generates an XHTML script tag for a JavaScript file. The URL is
    appended with the hash of the last git revision that the file was modified,
    for cache-busting purposes.

    Example:

    .. code-block:: jinja

       {% js_asset '/js/base' %}

    To enable, add ``baph.utils.assets.jinja2.js_asset`` to
    :setting:`JINJA2_EXTENSIONS` in ``settings.py``.
    '''

    tags = set(['js_asset'])

    def _build_tag(self, path):
        return u'<script type="text/javascript" src="%s"></script>' % \
               self._build_url_for_ext(path, 'js')

# nicer import names, a la coffin
asset = AssetLinkExtension
css_asset = CSSAssetExtension
js_asset = JSAssetExtension
