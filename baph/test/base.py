# -*- coding: utf-8 -*-

from baph.utils.importing import import_any_attr, import_attr
from django.conf import settings
from django.core import mail
from django.core.mail.backends import locmem
from django.core.urlresolvers import clear_url_caches
RequestFactory = \
    import_any_attr(['django.test.client', 'baph.test.requestfactory'],
                    'RequestFactory')
template_rendered = import_attr(['django.test.signals'], 'template_rendered')
DjangoTestCase = import_attr(['django.test.testcases'], 'TestCase')
from django.utils.translation import deactivate
from jinja2 import Template
from .client import Client

# Requires unittest2 or unittest in Python >= 2.7.
from django.utils.importlib import import_module
import sys
if sys.version_info < (2, 7):
    module = 'unittest2'
else:
    module = 'unittest'
mod = import_module(module)
TestCase = mod.TestCase

__all__ = ['BaseTestCase', 'Client', 'TestCase']


def instrumented_test_render(self, *args, **kwargs):
    template_rendered.send(sender=self, template=self,
                           context=dict(*args, **kwargs))
    return self.original_render(*args, **kwargs)


class BaseTestCase(DjangoTestCase, TestCase):
    '''The base test case for baph test cases which require Django
    infrastructure.
    '''

    @classmethod
    def setUpClass(cls):
        # set up local memory mail backend
        mail.original_SMTPConnection = mail.SMTPConnection
        mail.SMTPConnection = locmem.EmailBackend
        mail.original_email_backend = settings.EMAIL_BACKEND
        settings.EMAIL_BACKEND = \
            'django.core.mail.backends.locmem.EmailBackend'
        mail.outbox = []

        # deactivate i18n
        deactivate()

        # override urls, if needed
        if hasattr(cls, 'urls'):
            cls._old_root_urlconf = settings.ROOT_URLCONF
            settings.ROOT_URLCONF = cls.urls
            clear_url_caches()

        # set test client
        cls.client = Client()

        if not issubclass(cls, RequestFactory):
            # set request factory
            cls.rfactory = RequestFactory()

        # Instrument coffin's rendering function
        Template.original_render = Template.render
        Template.render = instrumented_test_render

    @classmethod
    def tearDownClass(cls):
        # De-instrument coffin's rendering function
        Template.render = Template.original_render
        del Template.original_render
        # restore urls, if needed
        if hasattr(cls, '_old_root_urlconf'):
            settings.ROOT_URLCONF = cls._old_root_urlconf
            clear_url_caches()

        # restore mail settings
        mail.SMTPConnection = mail.original_SMTPConnection
        del mail.original_SMTPConnection
        settings.EMAIL_BACKEND = mail.original_email_backend
        del mail.original_email_backend
        del mail.outbox

    def _fixture_setup(self):
        pass

    def _fixture_teardown(self):
        pass

    def __call__(self, *args, **kwargs):
        return super(TestCase, self).__call__(*args, **kwargs)

    def make_request(self, *args, **kwargs):
        if isinstance(self, RequestFactory):
            return self.request(*args, **kwargs)
        else:
            return self.rfactory.request(*args, **kwargs)
