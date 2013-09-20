import re

from django.conf import settings
from django.core.urlresolvers import reverse

#from baph.auth.models import User
from baph.test import TestCase
from baph.auth.registration import settings as auth_settings


class DecoratorTests(TestCase):
    """ Test the decorators """
    fixtures = ['users',]

    def test_secure_required(self):
        """
        Test that the ``secure_required`` decorator does a permanent redirect
        to a secured page.

        """
        auth_settings.BAPH_USE_HTTPS = True
        response = self.client.get(reverse('baph_signin'))

        # Test for the permanent redirect
        self.assertEqual(response.status_code, 301)

        # Test if the redirected url contains 'https'. Couldn't use
        # ``assertRedirects`` here because the redirected to page is
        # non-existant.
        self.assertTrue('https' in str(response))

        # Set back to the old settings
        auth_settings.BAPH_USE_HTTPS = False
