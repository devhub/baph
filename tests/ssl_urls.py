from __future__ import absolute_import
from coffin.conf.urls.defaults import patterns

urlpatterns = patterns('test_ssl',
    (r'^secure/$', 'secure_view', {'SSL': True}),
)
