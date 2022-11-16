# backport from django 1.6
from __future__ import absolute_import
from __future__ import unicode_literals
import re

import six.moves.html_entities
from six import unichr

if six.PY3:
    from django.utils.encoding import force_bytes
    from django.utils.encoding import smart_bytes
    from django.utils.encoding import force_str as force_unicode
    from django.utils.encoding import smart_str as smart_unicode
else:
    from django.utils.encoding import force_str as force_bytes
    from django.utils.encoding import smart_str as smart_bytes
    from django.utils.encoding import force_unicode
    from django.utils.encoding import smart_unicode


def unescape(text):
    """Removes HTML or XML character references 
      and entities from a text string.
    @param text The HTML (or XML) source text.
    @return The plain text, as a Unicode string, if necessary.
    from Fredrik Lundh
    http://effbot.org/zone/re-sub.htm#unescape-html
    """
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(six.moves.html_entities.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)
