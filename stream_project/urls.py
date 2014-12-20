from django.conf.urls import include, url
from django.contrib import admin
from search.views import search_func, search_trend, about, help

urlpatterns = [
    # Examples:
    # url(r'^$', 'stream_project.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    # url for video recommendation search
    url(r'^search/$', search_func),
    # url for video trend search (administrator only)
    url(r'^search_trend/$', search_trend),
    # url for help page
    url(r'^help/$', help),
    #url for about page
    url(r'^about/$', about),
]
