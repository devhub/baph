# -*- coding: utf-8 -*-

from coffin.conf.urls.defaults import patterns, url

urlpatterns = patterns('baph.socialmedia.twitter.auth.views',
    url(r'^register/$', 'twitter_registration', name='twitter_register'),
    url(r'^register/complete/$', 'complete_registration',
        name='twitter_register_complete'),
    url(r'^login/$', 'login', name='twitter_login'),
    url(r'^login/complete/$', 'complete_login', name='twitter_login_complete'),
)
