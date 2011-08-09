# -*- coding: utf-8 -*- 
from django.db import models
from django.utils.translation import ugettext_lazy as _
from datetime import datetime
from django.conf import settings
from django.core.urlresolvers import reverse
import logging

from django.db.models import Q

from django.db import connection


class SnapshotManage(models.Manager):
    def snaplist(self,**args):
        sub="select sum(hostnumber) from snapserver where fileid=snapshot.fileid group by snapserver.fileid";
        namesub = "select chname from tbname where enname=snapshot.author";
        monamesub = "select chname from tbname where enname=snapshot.lastpl";
        if args.get('listtype') == 'top':
            result = self.extra(select={'a':sub,'name':namesub,'modifypl':monamesub}).values('a','name','modifypl','fileid','filename','author','modifynum','lastpl','lastmt','score').order_by('-score')[:10]
        elif args.get('listtype') == 'part':
            """我参与的快照数据集"""
            result = self.extra(select={'a':sub,'name':namesub,'modifypl':monamesub}).filter(Q(author=args.get('author'))|Q(lastpl =args.get('author'))).values('a','name','modifypl','fileid','filename','author','modifynum','lastpl','lastmt','score').order_by('-score')
        elif args.get('listtype') == 'myconcern':
            """我关注的快照数据集Concern&Snapshotfile"""
            condition="concern.fileid=snapshot.fileid and concern.enname='%s'" % (args.get('username'))
            result = self.extra(select={'a':sub,'name':namesub,'modifypl':monamesub},tables=["concern"],where=[condition]).values('a','name','modifypl','fileid','filename','author','modifynum','lastpl','lastmt','score').order_by('-score')
        elif args.get('listtype') == 'all':
            """提取全部的快照文件列表"""
            result = self.extra(select={'a':sub,'name':namesub,'modifypl':monamesub}).values('a','name','modifypl','fileid','filename','author','modifynum','lastpl','lastmt','score').order_by('filetype')
        elif args.get('listtype') == 'filter': 
            showorder = args.get('showorder')
            if args.get('filetype') == '':
                result = self.extra(select={'a':sub,'name':namesub,'modifypl':monamesub}).values('a','name','modifypl','fileid','filename','author','modifynum','lastpl','lastmt','score')
            else:
                result = self.extra(select={'a':sub,'name':namesub,'modifypl':monamesub}).filter(filetype=args.get('filetype')).values('a','name','modifypl','fileid','filename','author','modifynum','lastpl','lastmt','score')
            if (showorder) == "b":
                result = result.order_by("a")
            elif (showorder) == "c":
                result = result.order_by("-a")
            elif (showorder) == "d":
                result = result.order_by("modifynum")
            elif (showorder) == "e":
                result = result.order_by("-modifynum")
            elif (showorder) == "a":
                result = result.order_by("filetype")
        elif args.get('listtype') == 'extend': 
            condition="snapreletd.`filename`=snapshot.`filename` "
            parentfilename = "select filename from snapshot where fileid=snapreletd.parentid";
            result = self.extra(select={'a':sub,'name':namesub,'modifypl':monamesub,'parentfilename':parentfilename},tables=["snapreletd"],where=[condition]).values('a','name','modifypl','parentfilename','fileid','filename','author','modifynum','lastpl','lastmt','score').order_by('-score')
        elif args.get('listtype') == 'filesearch': 
            """依据类型与关键字搜索"""
            if args.get('type') == "file":
                result = self.extra(select={'a':sub,'name':namesub,'modifypl':monamesub}).filter(filename__icontains=args.get('key').strip()).values('a','name','modifypl','fileid','filename','author','modifynum','lastpl','lastmt','score').order_by('filetype')
            if args.get('type') == "host":
                """分析主机&快照关系表中的快照"""
                condition="snapserver.fileid=snapshot.fileid and snapserver.hostgroup like '"+(args.get('key').strip())+"%%'"
                result = self.extra(select={'a':sub,'name':namesub,'modifypl':monamesub},tables=["snapserver"],where=[condition]).values('a','name','modifypl','fileid','filename','author','modifynum','lastpl','lastmt','score').order_by('-score')
            if args.get('type') == "author":
                """依据作者搜索"""
                condition="tbname.enname=snapshot.`author`  and (tbname.chname like '"+(args.get('key').strip())+"%%' or tbname.enname like '"+(args.get('key').strip()) + "%%')"
                result = self.extra(select={'a':sub,'name':namesub,'modifypl':monamesub},tables=["tbname"],where=[condition]).values('a','name','modifypl','fileid','filename','author','modifynum','lastpl','lastmt','score').order_by('-lastmt')
        return result
    
        
    
        
class Snapshotfile(models.Model):
    fileid = models.AutoField(primary_key=True)
    filename = models.CharField(max_length=150,null=False,default='')
    filetype = models.CharField(max_length=10,null=False,default='a')
    author = models.CharField(max_length=150,null=True,default='',help_text = _('e.g.:yaofang.zjl'))
    modifynum = models.IntegerField(default=1)
    lastpl = models.CharField(max_length=150,null=True,default='',help_text = 'e.g.:yaofang.zjl')
    lastmt =  models.DateTimeField(_("lastmt"), auto_now=True, editable=False)
    score = models.FloatField()
    objects = SnapshotManage()
    
    def __unicode__(self):
        return self.filename
    class Meta():
        db_table = 'snapshot'

    def get_absolute_url(self,ui_type):
        return reverse("snapshot_list", kwargs={"user_type": ui_type})
    @staticmethod
    def dateascount(datelist):
        cursor = connection.cursor()
        result_list = []
        for ele in datelist:
            innerlist = []
            cursor.execute("select  count(*) from snapshot where substring(lastmt,1,10)='%s'"%(ele))
            tmp = cursor.fetchone()
            innerlist.append(str(ele))
            innerlist.append(str(tmp[0]))
            result_list.append(innerlist)
        return result_list
        

class snapreletd(models.Model):
    id = models.AutoField(primary_key=True)
    filename = models.CharField(max_length=150,null=False,default='')
    parentid = models.IntegerField()
    def __unicode__(self):
        return self.filename
    class Meta():
        db_table = 'snapreletd'

class tbname(models.Model):
    id = models.AutoField(primary_key=True)
    enname = models.CharField(max_length=150,null=False,default='')
    chname  = models.CharField(max_length=150,null=False,default='')
    class Meta():
        db_table = 'tbname'

"""同步OpsFree的本地表"""
class opshosts(models.Model):
    id = models.AutoField(primary_key=True)
    hostgroup = models.CharField(max_length=150,null=False,default='')
    hostnumber=models.IntegerField(default=0)
    hostgroupid = models.IntegerField(default=0)
    class Meta():
        db_table = 'opshosts'
        
class Concern(models.Model):
    id = models.AutoField(primary_key=True)
    enname = models.CharField(max_length=150,null=False,default='',db_index=True)
    fileid = models.IntegerField(default=0)
    class Meta():
        db_table = 'concern'





class Snapserver(models.Model):
    id = models.AutoField(primary_key=True)
    fileid = models.IntegerField(default=0,db_index=True)
    hostgroup = models.CharField(max_length=150,null=False,default='')
    hostnumber=models.IntegerField(default=0)
    hostgroupid = models.IntegerField(default=0)
    class Meta():
        db_table = 'snapserver'

class Snapscore(models.Model):
    id = models.AutoField(primary_key=True)
    enname = models.CharField(max_length=150,null=False,default='',db_index=True)
    fileid = models.IntegerField()
    score = models.FloatField()
    """时间默认当前时间值"""
    times =  models.DateTimeField(auto_now=True,editable=False)     
    class Meta():
        db_table = 'snapscore' 

class Snaprecord(models.Model):
    id = models.AutoField(primary_key=True)
    enname = models.CharField(max_length=150,null=False,default='',db_index=True)
    fileid = models.IntegerField(default=0)
    times =  models.DateTimeField(auto_now=True, editable=False)
    class Meta():
        db_table = 'snaprecord' 

class Message(models.Model):
    enname = models.CharField(max_length=150,null=True,default='')
    times =  models.DateTimeField(auto_now=True,editable=False)    
    content = models.CharField(max_length=350,null=True,default='')
    class Meta():
        db_table = 'message' 

class UserLogin(models.Model):
    chname = models.CharField(max_length=150,null=True,default='')
    times =  models.DateTimeField(auto_now=True,editable=False)    
    class Meta():
        db_table = 'userlogin' 
    
class History(models.Model):
    clientip = models.CharField(max_length=50,null=True,default='')
    clientname = models.CharField(max_length=150,null=True,default='')
    filename = models.CharField(max_length=150,null=True,default='')
    times =  models.DateTimeField(auto_now=True,editable=False)    
    version = models.CharField(max_length=50,null=True,default='')
    class Meta():
        db_table = 'history' 
    
    @staticmethod
    def dateascount(datelist):
        cursor = connection.cursor()
        result_list = []
        
        tmpvalue = 0
        
        for ele in datelist:
            innerlist = []
            cursor.execute("select  count(*) from history where substring(times,1,10)='%s'"%(ele))
            tmp = cursor.fetchone()
            
            if int(tmp[0] > tmpvalue):
                tmpvalue = int(tmp[0])
            
            
            
            innerlist.append(str(ele))
            innerlist.append(str(tmp[0]))
            result_list.append(innerlist)
        
        
        result_list.append(tmpvalue)
        
        """计算最大值"""
        
        
        
        
        
        
        
        return result_list
    