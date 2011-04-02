# -*- coding: utf-8 -*-

from baph.auth.registration.views import register
from coffin.conf.urls.defaults import patterns, url
from django.conf import settings

FB_CONNECT = 'baph.socialmedia.facebook.connect'

urlpatterns = patterns('',
    url(r'^register/$',
        register,
        {
            'backend': '%s.FacebookConnectBackend' % FB_CONNECT,
            'extra_context': {
                'fb_app_id': settings.FACEBOOK_APP_ID,
                'fb_extra_perms': getattr(settings,
                                          'FACEBOOK_EXTRA_PERMISSIONS', None),
            },
            'template_name': 'fb_connect/register.html',
        },
        name='facebook_register'),
    url(r'^login/$',
        '%s.views.facebook_login' % FB_CONNECT,
        name='facebook_login'),
)
