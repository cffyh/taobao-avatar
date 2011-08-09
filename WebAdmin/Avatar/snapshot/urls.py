# -*- coding: utf-8 -*- 
from django.conf.urls.defaults import *
from Avatar.snapshot.models import Snapshotfile,snapreletd,tbname,opshosts,Concern,Snapserver,Snapscore,Snaprecord
from django.views.generic.list_detail import object_detail,object_list
urlpatterns = patterns('',
    url("^loglist/$", "Avatar.snapshot.views.log_xu_list", name="snapshot_log_xu_list"),
    url("^onehost/(?P<file_id>\d+)/$", "Avatar.snapshot.views.snaphost", name="snapshot_hostlist"),
    url("^slotlist/(?P<slottype>\w+)/$", "Avatar.snapshot.views.snapfile", name="snapshot_filelist"),
    url("^score/(?P<file_id>\d+)/$", "Avatar.snapshot.views.snapscore", name="snapshot_score"),
    url("^concern/(?P<file_id>\d+)/(?P<contype>\w+)/$", "Avatar.snapshot.views.snapconcern", name="snapshot_snapconcern"),
    url("^slotedit/(?P<file_id>\d+)/$", "Avatar.snapshot.views.snapedit", name="snapshot_edit"),
    url("^sloteditfile/$", "Avatar.snapshot.views.sloteditfile", name="snapshot_edit"),
    url("^hostslot/(?P<file_id>\d+)/$", "Avatar.snapshot.views.hostslot", name="snapshot_hostslot"),
    url("^searhost/(?P<searchtype>\w+)/(?P<file_id>\d+)/$", "Avatar.snapshot.views.searhost", name="snapshot_searhost"),
    url("^snapdel/(?P<deltype>\w+)/(?P<file_id>\d+)/$", "Avatar.snapshot.views.snapdel", name="snapshot_snapdel"),
    url("^snaplock/(?P<locktype>\w+)/(?P<file_id>\d+)/$", "Avatar.snapshot.views.snaplock", name="snapshotsnaplock"),
    url("^view_inheritance/(?P<viewtype>\w+)/$", "Avatar.snapshot.views.view_inheritance", name="view_inheritance"),
    url("^report/$", "Avatar.snapshot.views.report", name="report"),
    url("^saveslot/(?P<file_id>\d+)/$", "Avatar.snapshot.views.saveslot", name="snapshot_saveslot"),
    url("^getavatar/$", "Avatar.snapshot.views.getavatar", name="snapshot_saveslot"),
    
)
