# -*- coding: utf-8 -*-

from cssutils import parseString, replaceUrls, resolveImports, ser
from django.conf import settings
import os
import re
from urllib import pathname2url
from urlparse import urlsplit


def get_recursive_imports(sheet, base=None):
    '''Recursively retrieve all @import rules in given `sheet`.

    :param sheet:
        in this given :class:`cssutils.css.CSSStyleSheet` all import rules are
        resolved and added to a resulting *flat* sheet.
    :rtype: :class:`list` of :class:`str`
    '''
    urls = []

    def getReplacer(targetbase):
        "Return a replacer which uses base to return adjusted URLs"
        basesch, baseloc, basepath, basequery, basefrag = urlsplit(targetbase)
        basepath, basepathfilename = os.path.split(basepath)

        def replacer(url):
            scheme, location, path, query, fragment = urlsplit(url)
            if not scheme and not location and not path.startswith(u'/'):
                # relative
                path, filename = os.path.split(path)
                combined = os.path.normpath(os.path.join(basepath, path,
                                                         filename))
                return pathname2url(combined)
            else:
                # keep anything absolute
                return url

        return replacer
    if not base:
        base = sheet.href
    replacer = getReplacer(base)

    for rule in sheet.cssRules:
        if rule.type == rule.IMPORT_RULE and rule.hrefFound:
            urls += [replacer(rule.href)]
            # nested imports
            nested_urls = get_recursive_imports(rule.styleSheet)
            if nested_urls:
                # adjust relative URI references
                urls += [replacer(x) for x in nested_urls]

    return urls


def replace_static_refs(urlstring):
    debug_url = re.escape(getattr(settings, 'STATICFILES_DEBUG_URL',
                                  '/static'))
    return re.sub(r'''^(['"]?)%s(.*?['"]?)$''' % debug_url,
                  r'\1%s\2' % settings.MEDIA_URL, urlstring)


def minify(source, output, **options):
    '''Minifies CSS from a file and outputs it to a different file.
    :type source: :class:`django.core.files.File`
    :type output: :class:`django.core.files.File`
    '''
    ser.prefs.useMinified()
    base_path = getattr(source, 'path', source.name)
    stylesheet = parseString(source.read(),
                             href='file://%s' % pathname2url(base_path))
    css_files = get_recursive_imports(stylesheet, base=base_path)
    # concatenate the stylesheets
    minified = resolveImports(stylesheet)
    # replace static asset references with the "live" URLs
    replaceUrls(minified, replace_static_refs, ignoreImportRules=True)
    # generate minified CSS
    css = minified.cssText
    output.write(css)
    output.seek(0)
