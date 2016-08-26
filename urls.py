from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'apldms.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^dms/', include('dms.urls', namespace='dms')),
    url(r'^admin/', include(admin.site.urls)),
)
