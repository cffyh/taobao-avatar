# -*- coding: utf-8 -*- 
from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.simple import direct_to_template,redirect_to
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.STATIC_PATH}),
    (r'^login/$',direct_to_template,{"template":"login.html","mimetype":"text/html"}),
    (r'^$', redirect_to,{'url':'/index/'}),
    (r'^index/$', 'Avatar.snapshot.views.chkindex'),
    (r'^login/(?P<logintype>\w+)/$', 'Avatar.snapshot.views.logindo'),
    (r'^avatar/',include('Avatar.snapshot.urls')),
    (r'^svn/(?P<svntype>\w+)/$', 'Avatar.snapshot.views.svncommit'),
    (r'^inter/history/$', 'Avatar.snapshot.views.history'),
    (r'^inter/filename/$', 'Avatar.snapshot.views.hostnamefile'),
    
    
    (r'^inter/readsvn/$', 'Avatar.snapshot.views.readsvn'),
)
handler500 = 'Avatar.snapshot.views.my_custom_error_view'







