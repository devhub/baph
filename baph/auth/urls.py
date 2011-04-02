from coffin.conf.urls.defaults import patterns

urlpatterns = patterns('baph.auth.views',
    (r'^login/$', 'login', {'SSL': True}),
    (r'^logout/$', 'logout'),
    (r'^password_reset/$', 'password_reset'),
    (r'^password_reset/done/$', 'password_reset_done'),
    (r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
     'password_reset_confirm', {'SSL': True}),
    (r'^reset/done/$', 'password_reset_complete'),
)
