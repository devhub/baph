# -*- coding: utf-8 -*-
'''URLs for the test API.'''

from coffin.conf.urls.defaults import include, patterns
from piston.authentication.oauth import OAuthAuthentication
from piston.resource import Resource
from .handlers import HelloHandler

auth_three = OAuthAuthentication(realm='Test API')
auth_two = OAuthAuthentication(realm='Test API', two_legged=True)
three_handler = Resource(handler=HelloHandler, authentication=auth_three)
two_handler = Resource(handler=HelloHandler, authentication=auth_two)

urlpatterns = patterns('',
    (r'^three/$', three_handler, {'emitter_format': 'json'}),
    (r'^two/$', two_handler, {'emitter_format': 'json'}),
    (r'', include('baph.piston.oauth.urls')),
)
