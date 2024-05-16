from importlib import import_module
import os
import sys
from types import ModuleType

import six
from six.moves import html_parser


try:
    HTMLParseError = html_parser.HTMLParseError
except AttributeError:
    # create a dummy class for Python 3.5+ where it's been removed
    class HTMLParseError(Exception):
        pass

    html_parser.HTMLParseError = HTMLParseError


if six.PY3:
    # coffin/template/__init__.py uses 'import library' for a relative import,
    # which doesn't work in python3. To get around this we create an actual
    # 'library' module so the import works
    pass


def setup():
    from baph.apps import AppConfig, apps
    from baph.conf import settings
    from baph.utils.log import configure_logging

    configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)

    module = ModuleType('django.apps')
    setattr(module, 'AppConfig', AppConfig)
    sys.modules['django.apps'] = module

    apps.populate(settings.INSTALLED_APPS)


def replace_settings_class():
    from django import conf
    from baph.conf import settings
    conf.settings = settings


def apply_patches():
    patch_dir = os.path.join(os.path.dirname(__file__), 'patches')
    for mod_name in os.listdir(patch_dir):
        filename = os.path.join(patch_dir, mod_name)
        with open(filename, 'rt') as fp:
            src = fp.read()
        code = compile(src, filename, 'exec')
        mod = import_module(mod_name)
        exec(code, mod.__dict__)


replace_settings_class()
apply_patches()
