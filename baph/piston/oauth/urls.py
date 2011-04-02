# -*- coding: utf-8 -*-
'''Convenience urls for OAuth token handling.'''

from coffin.conf.urls.defaults import patterns

urlpatterns = patterns('baph.piston.oauth.views',
    (r'^oauth/request_token/$', 'get_request_token'),
    (r'^oauth/authorize/$', 'authorize_request_token'),
    (r'^oauth/access_token/$', 'get_access_token'),
)
