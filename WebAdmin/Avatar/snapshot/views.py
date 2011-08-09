# -*- coding: utf-8 -*- 
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render_to_response
from Avatar.snapshot.models import History,Message,Snapshotfile,UserLogin,snapreletd,tbname,opshosts,Concern,Snapserver,Snapscore,Snaprecord
from django.http import Http404
from django.shortcuts import get_object_or_404
import logging
import urllib
import urllib2
import os,commands
from django.core.cache import cache
from Avatar.Config import AvatarConfig
from django.views.generic.list_detail import object_list
from django.core.urlresolvers import reverse
import json,hashlib
from time import strftime, localtime
from Avatar.utils.utils import getprelist
from Avatar.utils.Svnaction import exportfiles,svn_add_action,commit_from_svn_log_entry,model_add_package,model_edit_package,run_svn_log,model_file_is_svn,svn_delete_file,get_svn_status,svn_lock_unlock,create_dir,svn_update,svn_check_username

"""
接收接口参数写入到调用历史表
"""
def history(request):
    try:
        clientip = request.GET.get("clientip",'').strip()
        clientname = request.GET.get("clientname",'').strip()
        filename = request.GET.get("filename",'').strip()
        times = request.GET.get("times",'').strip()
        version = request.GET.get("version",'').strip()
        History.objects.create(clientip=clientip,clientname=clientname,filename=filename,times=times,version=version)
        return HttpResponse("1")
    except Exception,e:
        logging.debug(str(e))
        return HttpResponse("0")

def hostnamefile(request):
    clientname = request.GET.get("clientname",'').strip()
    try:
        url = "http://opsfree.corp.taobao.com:9999/nodes.json?_username=droid/droid&e=1&n=0&q=nodename==%s"%(clientname)
        url_handle=urllib.urlopen(url)
        data = json.loads(url_handle.read())
        if len(data) != 1:
            return HttpResponse(clientname)
        hostgroup = data[0].get('nodegroup').strip()
        filenamesub = "select filename from snapshot where fileid=snapserver.fileid";
        result = Snapserver.objects.extra(select={'a':filenamesub}).filter(hostgroup=hostgroup).values('a')[:1]
        if result[0].get('a') is None:
            return HttpResponse(clientname)
        return HttpResponse(result[0].get('a'))
    except Exception,e:
        logging.debug(str(e))
        return HttpResponse(clientname)
"""
接收SVN钩子调用接口
"""
def svncommit(request,svntype):
    try:
        if svntype == "A":
            """表示是添加操作"""
            filename = request.POST.get("filename",'').strip()
            author = request.POST.get("author",'').strip()
            lastmt = request.POST.get("lastmt",'').strip()
            Snapshotfile.objects.create(filename=filename,filetype=filename[0],author=author,lastpl=author,lastmt=lastmt,modifynum=1,score=0)
        elif svntype == "U":
            """表示是修改操作"""
            filename = request.POST.get("filename",'').strip()
            author = request.POST.get("author",'').strip()
            lastmt = request.POST.get("lastmt",'').strip()
            tmp = Snapshotfile.objects.get(filename=filename,filetype=filename[0])
            tmp.lastpl = author
            tmp.lastmt = lastmt
            tmp.modifynum = tmp.modifynum + 1
            tmp.save()
        elif svntype == "D":
            filename = request.POST.get("filename",'').strip()
            qs  = Snapshotfile.objects.get(filename = filename,filetype = filename[0])
            fileid = qs.fileid
            Concern.objects.filter(fileid=fileid).delete()
            Snaprecord.objects.filter(fileid=fileid).delete()
            snapreletd.objects.filter(filename=filename).delete()
            Snapscore.objects.filter(fileid=fileid).delete()
            Snapserver.objects.filter(fileid=fileid).delete()
            Snapshotfile.objects.filter(fileid=fileid).delete()
        return HttpResponse("1")
    except Exception,e:
        logging.debug("svn commit error")
        logging.debug(str(e))
        return HttpResponse("0")


def leftpage(request):
    try:
        tname = tbname.objects.get(enname=request.session["username"]).chname 
    except Exception,e:
        tname = request.session["username"]
    visitnum = Snaprecord.objects.count()
    snapnum = Snapshotfile.objects.count()
    dingyuenum = Concern.objects.count()
    a=Snapserver.objects.extra(select={'servernum':'sum(hostnumber)'}).values('servernum')
    return {"cname":tname,"visitnum":visitnum,"snapnum":snapnum,"servernum":a[0].get('servernum'),'dingyuenum':dingyuenum}

def chkindex(request):
    snapfile = Snapshotfile.objects.snaplist(listtype='top')
    dicta = leftpage(request)
    dicta['snapfile'] = snapfile
    return render_to_response('index.html',dicta)

"""
依据快照文件ID提取所对应的主机列表
"""
def snaphost(request,file_id):
    return object_list(request,queryset=Snapserver.objects.filter(fileid=file_id).distinct(),template_name="snaphost.html")

"""搜索主机列表"""
def searhost(request,searchtype,file_id):
    key = request.GET.get("key",'').strip()
    myresult = []
    if searchtype == 'no':
        """未绑定当前快照的主机组列表"""
        condition="opshosts.hostgroup not in (select snapserver.hostgroup from snapserver) and opshosts.hostgroup like '" + (key) + "%%'"
        notmp = opshosts.objects.extra(where=[condition]).values('hostgroup').order_by('hostgroup').distinct()
    elif searchtype == 'in':
        """提取绑定了当前应用快照的主机组列表"""
        notmp = Snapserver.objects.filter(fileid=file_id,hostgroup__icontains=key).values('hostgroup').distinct()
    """解析结果集返回JSON串"""
    for ele in notmp:
        b={}
        b['hostgroup'] = ele.get('hostgroup')
        myresult.append(b)
    return HttpResponse(json.dumps(myresult,ensure_ascii=True))

"""
依据快照文件ID提取当前这个快照文件所对应的评分表记录
"""
def snapscore(request,file_id):
    if request.method == "POST":
        vote = request.POST.get('vote')
        username = request.session["username"]
        file_name = Snapshotfile.objects.get(fileid=file_id).filename
        Message.objects.create(enname=username,content="用户给快照"+str(file_name)+"评分"+str(vote))
        """1.更新用户自身打分记录"""
        if Snapscore.objects.filter(enname=username,fileid=file_id).count()>0:
            Snapscore.objects.filter(enname=username,fileid=file_id).update(score=vote)
        else:
            Snapscore.objects.create(enname=username,fileid=file_id,score=vote)
        """2. 更新快照文件的分数"""
        a=Snapscore.objects.extra(select={'scoretotal':'round(avg(score),2)'}).filter(fileid=file_id).values('scoretotal')
        Snapshotfile.objects.filter(fileid=file_id).update(score=float(a[0].get('scoretotal')))
        return HttpResponse("1")
    else:
       namesub = "select chname from tbname where enname=snapscore.enname";
       return object_list(request,queryset=Snapscore.objects.extra(select={'a':namesub}).filter(fileid=file_id).distinct().values('a','score','times'),template_name="snapscore.html") 

def log_xu_list(request):
    
    dicta = (leftpage(request))
    
    namesub = "select chname from tbname where enname=message.enname";
    return object_list(request,queryset = Message.objects.extra(select={'name':namesub}).values('enname','name','content','times').order_by("-times"),template_name = "loglist.html",paginate_by = AvatarConfig.perpage,extra_context = dicta)

"""
依据不同类型的快照提取相应的快照文件列表
http://10.232.38.99:8080/slotlist/alllist/ 
"""
def snapfile(request,slottype):
    username = request.session["username"]
    dicta = leftpage(request)
    if slottype == 'mylist' :
        """我的快照提取两块内容：已提交到SVN的还有本地一份"""
        dicta['username'] = username
        return object_list(
                           request,
                           queryset = Snapshotfile.objects.snaplist(listtype='part',author=username),
                           template_name = "myfilelist.html",
                           paginate_by = AvatarConfig.perpage,
                           extra_context = dicta
                           )
    elif slottype == 'myconcern':
        """我所关注 的快照列表分页显示"""
        return object_list(
                           request,
                           queryset = Snapshotfile.objects.snaplist(listtype='myconcern',username=username),
                           template_name = "myconcern.html",
                           paginate_by = AvatarConfig.perpage,
                           extra_context = dicta
                           )
    elif slottype == 'alllist':
        """全部的快照列表"""
        return object_list(
                           request,
                           queryset = Snapshotfile.objects.snaplist(listtype='all'),
                           template_name = "snaplist.html",
                           paginate_by = AvatarConfig.perpage,
                           extra_context = dicta
                           )
    elif slottype == 'filtefile':
        """过滤 支持过滤的分页显示"""
        filetype = request.GET.get('filetype','').strip()
        showorder = request.GET.get('order','').strip()
        dicta['filetype'] = filetype
        dicta['showorder'] = showorder
        return object_list(
                           request,
                           queryset = Snapshotfile.objects.snaplist(listtype='filter',filetype=filetype,showorder=showorder),
                           template_name = "snaplist.html",
                           paginate_by = AvatarConfig.perpage,
                           extra_context = dicta
                           )
    elif slottype == 'extendlist':
        """被衍生的快照文件列表"""
        return object_list(
                           request,
                           queryset = Snapshotfile.objects.snaplist(listtype='extend'),
                           template_name = "extendlist.html",
                           paginate_by = AvatarConfig.perpage,
                           extra_context = dicta
                           )
    elif slottype == 'filesearch':
        """顶部的搜索"""
        search_type  = request.GET.get('search_type','').strip()
        search_keyword  = request.GET.get('search_keyword','').strip()
        if search_type == "" or search_keyword=="":
            return HttpResponse("<script>alert('请选择查询条件');history.go(-1);</script>")
        dicta['search_type'] = search_type
        dicta['search_keyword'] = search_keyword
        return object_list(
                           request,
                           queryset = Snapshotfile.objects.snaplist(listtype='filesearch',type=search_type,key=search_keyword),
                           template_name = "filesearch.html",
                           paginate_by = AvatarConfig.perpage,
                           extra_context = dicta
                           )
        
        

"""处理编辑快照相关逻辑"""
def rightpage(file_id,file_name='',username=''):
    """修订记录svn log的方式查看最近五次的修订记录"""
    if file_name != "":
        file_absobult = AvatarConfig.svnworkplace + username + '/' + file_name[0] + '/' + file_name
        m=run_svn_log(file_absobult, rev_start=0, rev_end=0, limit=500, stop_on_copy=True)
        
    """评价记录来自用户评价表"""
    scorename = "select chname from tbname where enname=snapscore.enname";
    visitname = "select chname from tbname where enname=snaprecord.enname";
    concename = "select chname from tbname where enname=concern.enname";
    scorelist=Snapscore.objects.extra(select={'a':scorename}).filter(fileid=file_id).distinct().values('a','score','times').order_by("-times")[:5]
    """访问记录表"""
    visitlist = Snaprecord.objects.extra(select={'a':visitname}).filter(fileid=file_id).distinct().values('a','times').order_by("-times")[:5]
    """关注用户表"""
    concerlist = Concern.objects.extra(select={'a':concename}).filter(fileid=file_id).distinct().values('a')[:5]
    """依据快照文件ID获取关联主机数"""
    a=Snapserver.objects.extra(select={'servernum':'sum(hostnumber)'}).filter(fileid=file_id).values('servernum')
    """调用记录"""
    historylist = History.objects.filter(filename=file_name).distinct().values('filename','clientip','version','times').order_by("-times")[:5]
    
    
    """
    将取出来的修订日志的作者提取出来并过滤重复的记录
    """
    result  = []
    for ele in m:
        result.append(ele.get('author'))
    aa = {}.fromkeys(result).keys()
    
    
    
    return {"scorelist":scorelist,"visitlist":visitlist,"concerlist":concerlist,"oneservernum":a[0].get('servernum'),"svnlog":m,"authorlist":aa,"historylist":historylist}

"""
方法：解析快照文件内容返回字典
@param file: 要解析的文件绝对目录
@return: {}文件内容的字典
"""
def parsefile_dict(file):
    """将一个字符串转换成一个字符串"""
    def _transform_string(mys):
        a = mys.split()
        a.sort()
        return a
    def _count_str_len(mys):
        return len(mys.split())
    def _transform_join(mys):
        a = mys.split()
        return "\n".join(a)
    result = {}
    
    tmp = commands.getstatusoutput("sed -n '/comment=/p' "+file+"|awk -F '=' '{print $2}'")[1].replace('\"','')
    result['comment'] = tmp
    
    
    tmp = commands.getstatusoutput("sed -n '/base_rpms=/p' "+file+"|awk -F '=' '{print $2}'")[1].replace('\"','')
    result['base_rpms'] = _transform_string(tmp)
    result['base_rpms_num'] = commands.getstatusoutput("sed -n '/base_rpms_num=/p' "+file+"|awk -F '=' '{print $2}'")[1]
    if result['base_rpms_num'] == _count_str_len(tmp):
        result['check_base_rpms'] = ''
    else:
        result['check_base_rpms'] = 'NUM ERROR！'
    """应用软件包""" 
    mytmp = commands.getstatusoutput("sed -n '/cust_rpms=/p' "+file+"|awk -F '=' '{print $2}'")[1].replace('\"','')
    result['cust_rpms'] = _transform_string(mytmp)
    result['cust_rpms_num'] = commands.getstatusoutput("sed -n '/cust_rpms_num=/p' "+file+"|awk -F '=' '{print $2}'")[1]
    if result['cust_rpms_num'] == _count_str_len(mytmp):
        result['check_cust_rpms'] = ''
    else:
        result['check_cust_rpms'] = 'NUM ERROR2！'
    """获取diff_content"""
    cmd = 'sed -n \'/###END OF AVATAR###/,$p\' ' + file+'|sed -e 1d';
    tmp=commands.getstatusoutput(cmd)
    totalcontent  = tmp[1]
    """diff_file 得到一个［］序列"""
    tmpaa = commands.getstatusoutput("sed -n '/diff_files=/p' "+file+"|awk -F '=' '{print $2}'")[1].replace('\"','').split()
    result['diff_file'] = tmpaa     #一个序列填充
    
    result['diff_file_length'] = len(tmpaa)
    """遍历这个序列依据这个序列去分析文本内容"""
    d = {}
    vv = ''
    for i, v in enumerate(tmpaa):
        if len(tmpaa[i+1:i+2]) == 0:
             t= tmpaa[i:i+1][0]
             start_index=totalcontent.find(t)
             vv = totalcontent[start_index:].strip()
        else:
            f = tmpaa[i:i+1][0]
            t = tmpaa[i+1:i+2][0]
            start_index = totalcontent.find(f)
            if start_index>-1:
                end_index = totalcontent.find(t,start_index)
                vv = totalcontent[start_index:end_index].strip()
        d[i+1] = u'%s' % vv.decode( 'utf-8', 'ignore') 
    result['diff_content'] = d
    """
        <select><option value=0>0</value></select>    <div id=0>text</div>
    """
    return result


"""
当前方法展现快照的内容。并包括了快照的详细内容、修订记录信息、及其他信息
"""
def snapedit(request,file_id):
    Snaprecord.objects.create(enname=request.session["username"],fileid=file_id)
#        """加载右侧导航数据，将其做到cache里面"""
    file_name = request.GET.get('filename','').strip()
#        """获取要更新的文件绝对目录"""
    file_absobult = AvatarConfig.svnworkplace + request.session["username"] + '/' + file_name[0] + '/' + file_name
#        """编辑之前对此快照文件进行一把svn update操作"""
    svn_update(file_absobult,username=request.session["username"],password=request.session["password"])
#        """加载当前快照文件的内容渲染编辑页/home/avtar/zjl/c/click_package"""
    mysnapfilecontent  = parsefile_dict(file_absobult)
#        """将当前这个快照文件的作者取出来"""
    author = Snapshotfile.objects.get(fileid=file_id).author
    dicta= {}
    dicta = rightpage(file_id,file_name,request.session['username'])
    dicta.update(leftpage(request))
    dicta['file_name'] = file_name
    dicta['file_id'] = file_id
#        """加载关注这个图标 """
    if Concern.objects.filter(enname=request.session["username"],fileid=file_id).count()>0:
        dicta['flag'] = "ok"
    else:
        dicta['flag'] = "off"
#        """判断当前这个文件是否上锁"""
    myresult = get_svn_status(file_absobult)
    try:
        dicta['lock'] = myresult[0].get('lock')
    except Exception,e:dicta['lock']='no'
    """判断当前这个快照的作者是不是本人"""
    if author.strip() == request.session['username'].strip():
        dicta['isauthor'] = "1"
    else:
        dicta['isauthor'] = "0"
    dicta['mysnapfilecontent'] = mysnapfilecontent
    url_back = request.META.get('HTTP_REFERER',"/")
    dicta['url_back'] = url_back
    return render_to_response('slotcontent.html',dicta)



"""
点击展开编辑页面的编辑窗口
"""
def sloteditfile(request):
    file_id = request.GET.get('fileid','').strip()
#   """加载右侧导航数据，将其做到cache里面"""
    file_name = request.GET.get('filename','').strip()
#   """获取要更新的文件绝对目录"""
#   """编辑之前对此快照文件进行一把svn update操作"""
    file_absobult = AvatarConfig.svnworkplace + request.session["username"] + '/' + file_name[0] + '/' + file_name
    svn_update(file_absobult,username=request.session["username"],password=request.session["password"])
#   """加载当前快照文件的内容渲染编辑页/home/avtar/zjl/c/click_package"""
    mysnapfilecontent  = parsefile_dict(file_absobult)
#   """将当前这个快照文件的作者取出来"""
    author = Snapshotfile.objects.get(fileid=file_id).author
    dicta= {}
    dicta.update(leftpage(request))
    dicta['file_name'] = file_name
    dicta['file_id'] = file_id
#        """加载关注这个图标 """
    if Concern.objects.filter(enname=request.session["username"],fileid=file_id).count()>0:
        dicta['flag'] = "ok"
    else:
        dicta['flag'] = "off"
#        """判断当前这个文件是否上锁"""
    myresult = get_svn_status(file_absobult)
    try:
        dicta['lock'] = myresult[0].get('lock')
    except Exception,e:dicta['lock']='no'
    """判断当前这个快照的作者是不是本人"""
    if author.strip() == request.session['username'].strip():
        dicta['isauthor'] = "1"
    else:
        dicta['isauthor'] = "0"
    dicta['mysnapfilecontent'] = mysnapfilecontent
    url_back = request.META.get('HTTP_REFERER',"/")
    dicta['url_back'] = url_back
    return render_to_response('editslot.html',dicta)

"""依据快照名称与版本号提取当前版本的快照文件内容"""
def getavatar(request):
    namespace = request.GET.get('namespace','').strip()
    revision = request.GET.get('revision','').strip()
    """1. 将当前版本的文件export一份到新目录"""
    username = request.session['username'].strip()
    password = request.session['password'].strip()
    sourcepath = AvatarConfig.svnworkplace + username + '/' + namespace[0] + '/' + namespace
    exportpath = AvatarConfig.svnexport + username + '/' + namespace[0] + '/' + namespace
    exportparentpath = AvatarConfig.svnexport + username + '/' + namespace[0] + '/' 
    tmp = exportfiles(username=username,password=password,sourcepath=sourcepath,exportpath=exportpath,revision=revision,exportparentpath=exportparentpath)
    if tmp:
        """解析export出来的内容"""
        """2. 解析export出来的新文件的内容渲染"""
        mysnapfilecontent = parsefile_dict(exportpath)
        dicta = {}
        dicta['mysnapfilecontent'] = mysnapfilecontent
        return render_to_response('loghistory.html',dicta)
    else:
        return HttpResponse("file export error!")
    
    
    

def form_to_filecontent_edit(request):
    def _str_replace(mys):
        return mys.replace('\r\n','\n')
    def _list_to_str(mys):
        return _str_replace(" ".join(mys))
    def _list_to_str2(mys):
        return _str_replace("\n\n".join(mys))
    myresult = {}
    logging.debug("Staring to receive content")
    fb_list = request.POST.getlist('fb_list')
    """应用系统基础软件包[]"""
    select_list = request.POST.getlist('select_list')
    """配置文件名称列表基础软件包str"""
    diff_files = request.POST.get('diff_filescontent','')
    """差异文件的内容列表[]"""
    diff_content = request.POST.getlist('diff_content[]')
    if len(fb_list) == 0:
        myresult['error'] = '50101'
        myresult['reason'] = 'Error:FILE_BASE_RPMS_EMPTY'
        return myresult
    if len(select_list) == 0:
        myresult['error'] = '50102'
        myresult['reason'] = 'Error:FILE_CUST_RPMS_EMPTY'
        return myresult
    if len(request.POST.get('memo','').strip()) < 5:
        myresult['error'] = '50103'
        myresult['reason'] = 'Error:FILE_MEMO_LEAST_5_LETTERS'
        return myresult
    content = "###################"+"\n";
    content += "#AVATAR State File#"+"\n";
    content += "###################"+"\n";
    content += "namespace=\""+request.POST.get('myfilename','').strip()+"\"\n";
    content += "timestamp=\""+strftime("%Y-%m-%d %H:%M:%S",localtime())+"\"\n";
    content += "base_rpms_num="+str(len(fb_list))+"\n";
    content += "cust_rpms_num="+str(len(select_list))+"\n";
    
    content += "base_rpms=\""+_list_to_str(fb_list)+"\"\n";
    content += "cust_rpms=\""+_list_to_str(select_list)+"\"\n";
    
    content += "diff_files=\""+diff_files+"\"\n";
    
    content += "comment=\""+_str_replace(request.POST.get('memo','').strip())+"\"\n";
    
    content += "###END OF AVATAR###\n";
    
    content += _list_to_str2(diff_content)
    myresult['error'] = '50104'
    myresult['reason'] = 'FILE_CONTENT_CREATE_OK'
    myresult['content'] = content
    
    
    logging.debug("Ending receive content")
    return myresult


"""
当快照文件发生变更与删除发送旺旺消息给相应的关注用户
@param users: 相应的用户列表
"""
def sendwwmsg(users, msg, subject = 'update snapfile'):
    for user in users:
        data={'user':user,'sub':subject,'msg':msg}
        url='http://172.24.102.119/sendMsg.php?' + urllib.urlencode(data)
        urllib2.urlopen(url)
    return


"""
保存编辑快照页面的内容
@param file_id: 快照文件ID
"""
def saveslot(request,file_id):
    username  = request.session["username"]
    password=request.session['password']
    
    new_file_name = request.POST.get('myfilename','').strip()
    if new_file_name == '':
        return HttpResponse("<script>alert('当前这个快照文件名称不可为空!');history.go(-1);</script>")
    myoldfilename = request.POST.get('myoldfilename','').strip()
    urlback = request.POST.get('urlback','').strip()
    if new_file_name == myoldfilename:
        """如果文件名相同则只做修改内容就提交"""
        logging.debug("Ending 1")
        tmp = form_to_filecontent_edit(request)
        if tmp.get('error') != '50104':
            logging.debug(tmp.get('reason'))
            return HttpResponse("<script>alert('"+tmp.get('reason')+"');history.go(-1);</script>")
        file_absobult = AvatarConfig.svnworkplace + username + '/' + new_file_name[0] + '/' + new_file_name
        logging.debug("Staring to save file!")
        step1 = model_edit_package(content=tmp.get('content'),memo=request.POST.get('memo','').strip(),username=username,password=password,filepath=file_absobult) 
        logging.debug("Staring to commit to svn!")
        if step1 == False:
            return HttpResponse("<script>alert('快照文件写入失败!');history.go(-1);</script>")
        step2 = commit_from_svn_log_entry(files=file_absobult,svnmsg=request.POST.get('memo','').strip(),username=username,password=password)
        svn_update(file_absobult,username=username,password=password)
        if step2 == "error":
            return HttpResponse("<script>alert('快照文件提交失败!');history.go(-1);</script>")
        else:
            selfmdkey = hashlib.new("md5", "fileid="+file_id+"&username="+username).hexdigest()
            cache.delete(selfmdkey)
            return HttpResponseRedirect(urlback)
    else:
        """"1.检查是否重名"""
        if check_file_name(new_file_name,username):
            return HttpResponse("<script>alert('当前这个快照文件名称重名了!');history.go(-1);</script>")
        """2.保存提交新文件"""
        tmp = form_to_filecontent_edit(request)
        file_absobult = AvatarConfig.svnworkplace + username + '/' + new_file_name[0] + '/' + new_file_name
        logging.debug("Staring to save file!")
        step1 = model_add_package(filename=new_file_name,content=tmp.get('content'),memo=request.POST.get('memo','').strip(),username=username,password=password,filepath=file_absobult) 
        if step1 == False:
            return HttpResponse("<script>alert('当前这个快照文件创建失败');history.go(-1);</script>")
        logging.debug("Staring to commit file!")
        step2 = svn_add_action(file_absobult,username=username,password=password)
        if step2 == "error":
            return HttpResponse("<script>alert('快照文件提交失败!');history.go(-1);</script>")
        logging.debug("=======Delete old file=====")
        """3.将原来的文件删除掉"""
        old_file_absobult = AvatarConfig.svnworkplace + username + '/' + myoldfilename[0] + '/' + myoldfilename
        if os.path.isfile(old_file_absobult):
            if model_file_is_svn(old_file_absobult):
                """表示当前这个文件在版本库里面"""
                logging.debug("old file in svn")
                if svn_delete_file(old_file_absobult,username=username,password=password)  == "error":
                    """表示SVN删除失败"""
                    return HttpResponse("<script>alert('删除旧快照文件失败');history.go(-1);</script>")
            else:
                logging.debug("old file not in svn")
                os.unlink(old_file_absobult)
        logging.debug("=======svn update file=====")
        svn_update(file_absobult,username=username,password=password)
        selfmdkey = hashlib.new("md5", "fileid="+file_id+"&username="+username).hexdigest()
        cache.delete(selfmdkey)
        return HttpResponse("<script>alert('修改成功!');history.go(-1);</script>")


"""
判断指定的文件名是否已存在
@param filename: 文件名
@param username: 当前的用户名
@return: true表示已存在
"""
def check_file_name(filename,username):
    file_absobult = AvatarConfig.svnworkplace + username + '/' + filename[0] + '/' + filename
    return os.path.isfile(file_absobult)

def form_to_filecontent(request):
    def _count_str_len(mys):
        return len(mys.split('\n'))
    def _str_replace(mys):
        return mys.replace('\r\n',' ')
    
    myresult = {}
    if request.POST.get('base_rpms','').strip() == '':
        myresult['error'] = '50101'
        myresult['reason'] = 'FILE_BASE_RPMS_EMPTY'
        return myresult
    if request.POST.get('base_rpms','').strip() == '':
        myresult['error'] = '50102'
        myresult['reason'] = 'FILE_CUST_RPMS_EMPTY'
        return myresult
    if len(request.POST.get('memo','').strip()) < 5:
        myresult['error'] = '50103'
        myresult['reason'] = 'FILE_MEMO_LEAST_5_LETTERS'
        return myresult
    diff_name  = request.POST.get('diff_name','').strip()
    content = "###################"+"\n";
    content += "#AVATAR State File#"+"\n";
    content += "###################"+"\n";
    content += "namespace=\""+request.POST.get('new_file_name','').strip()+"\"\n";
    content += "timestamp=\""+strftime("%Y-%m-%d %H:%M:%S",localtime())+"\"\n";
    content += "base_rpms_num="+str(_count_str_len(request.POST.get('base_rpms','').strip()))+"\n";
    content += "cust_rpms_num="+str(_count_str_len(request.POST.get('cust_rpms','').strip()))+"\n";
    
    content += "base_rpms=\""+_str_replace(request.POST.get('base_rpms','').strip())+"\"\n";
    content += "cust_rpms=\""+_str_replace(request.POST.get('cust_rpms','').strip())+"\"\n";
    
    content += "diff_files=\""+_str_replace(request.POST.get('diff_files','').strip())+"\"\n";
    
    content += "comment=\""+_str_replace(request.POST.get('memo','').strip())+"\"\n";
    
    content += "###END OF AVATAR###\n";
    
    content += request.POST.get('diff_content','').strip()
    myresult['error'] = '50104'
    myresult['reason'] = 'FILE_CONTENT_CREATE_OK'
    myresult['content'] = content
    logging.debug(myresult)
    return myresult





"""处理衍生"""
def view_inheritance(request,viewtype):
    if viewtype == 'inheritanceshow':
        """加载显示衍生页面"""
        filename = request.GET.get('filename','').strip()
        fileid = request.GET.get('fileid','').strip()
        dicta = (leftpage(request))
        dicta['filename'] = 'new@'  + filename
        dicta['base_rpms'] = '@'  + filename
        dicta['cust_rpms'] = '@'  + filename
        dicta['diff_files'] = '@'  + filename
        dicta['diff_content'] = '@'  + filename
        dicta['parentfileid'] = fileid
        return render_to_response('view_inherite.html',dicta)
    else:
        """处理保存逻辑"""
        new_file_name = request.POST.get('new_file_name','').strip()
        if new_file_name == '':
            return HttpResponse("<script>alert('名称不可为空');history.go(-1);</script>")
        """1.做文件名重名检查"""
        if check_file_name(new_file_name,request.session['username']):
            return HttpResponse("<script>alert('当前文件已存在，请换个新名称');history.go(-1);</script>")
        """2.将表单的内容保存到字符串"""
        tmp = form_to_filecontent(request)
        if tmp.get('error') != '50104':
            return HttpResponse("<script>alert('"+tmp.get('reason')+"');history.go(-1);</script>")
        file_absobult = AvatarConfig.svnworkplace + request.session["username"] + '/' + new_file_name[0] + '/' + new_file_name
        step1 = model_add_package(new_file_name,tmp.get('content'),request.POST.get('memo','').strip(),request.session['username'],request.session['password'],file_absobult)
        if step1 == False:
            return HttpResponse("<script>alert('文件提交失败!');history.go(-1);</script>")
        """svn commit"""
        step2 = svn_add_action(file_absobult,username=request.session['username'],password=request.session['password'])
        if step2 == "error":
            return HttpResponse("<script>alert('快照文件提交失败!');history.go(-1);</script>")
        """提交一条记录到关联表"""
        parentfileid = request.POST.get('parentfileid','').strip()
        snapreletd.objects.create(filename=new_file_name,parentid=parentfileid)
        return HttpResponse("<script>alert('衍生快照保存成功!');location.href='/avatar/slotlist/extendlist/';</script>")
        
        
        
"""
处理SVN的上锁与解锁操作
"""
def snaplock(request,locktype,file_id):
    file_name = request.GET.get('filename','').strip()
    file_absobult = AvatarConfig.svnworkplace + request.session["username"] + '/' + file_name[0] + '/' + file_name
    if locktype == 'lock':
        """表示对其加锁"""
        if svn_lock_unlock(dotype='lock',origina=file_absobult,username=request.session["username"],password=request.session["password"]):
            Message.objects.create(enname=request.session["username"],content="用户给快照"+str(file_name)+"加锁")
            return HttpResponse("1")
        else:
            return HttpResponse("0")
    else:
        """表示对其解锁"""
        if svn_lock_unlock(dotype='unlock',origina=file_absobult,username=request.session["username"],password=request.session["password"]):
            Message.objects.create(enname=request.session["username"],content="用户给快照"+str(file_name)+"解锁")
            return HttpResponse("1")
        else:
            return HttpResponse("0")

"""响应客户端AJAX更新关注事件"""
def snapconcern(request,file_id,contype):
    if contype == 'on':
        """表示当前你已关注，程序将记录删除"""
        Concern.objects.get(enname=request.session["username"],fileid=file_id).delete()
        return HttpResponse("1")
    elif contype == 'off':
        """表示当前你未关注，程序将添加一条记录"""
        Concern.objects.create(enname=request.session["username"],fileid=file_id)
        return HttpResponse("0")



"""以下处理快照文件与OpsFree的数据绑定相关"""
def hostslot(request,file_id):
    if request.method=="POST":
        Snapserver.objects.filter(fileid=file_id).delete()
        linked_nodegroups = request.POST.getlist('linked_nodegroups')
        for ele in linked_nodegroups:
            try:
                hostnumeber = opshosts.objects.get(hostgroup=ele.strip()).hostnumber
                hostgroupid = opshosts.objects.get(hostgroup=ele.strip()).hostgroupid
            except Exception,e:
                hostnumeber = 0
                hostgroupid = 0
            Snapserver.objects.create(fileid=int(file_id),hostgroup=ele.strip(),hostnumber=int(hostnumeber),hostgroupid=int(hostgroupid))
        file_name = Snapshotfile.objects.get(fileid=file_id).filename
        Message.objects.create(enname=request.session["username"],content="用户给快照"+str(file_name)+"配置关联主机")
        return HttpResponse(status="200",content="系统成功处理关联绑定")
    else:
        filename = request.GET.get('filename','').strip()
        dicta = rightpage(file_id,filename,request.session['username'])
        dicta.update(leftpage(request))
        """提取已绑定的主机组列表"""
        tmp = Snapserver.objects.filter(fileid=file_id).distinct()
        dicta['alreadylist'] = tmp
        """提取未绑定的主机组列表!支持not in写法"""
        condition="opshosts.hostgroup not in (select snapserver.hostgroup from snapserver )"
        notmp = opshosts.objects.extra(where=[condition]).values('hostgroup').order_by('hostgroup')
        dicta['notlist'] = notmp
        """渲染模板"""
        dicta['file_name'] = filename
        dicta['file_id'] = file_id
        dicta['alreadylistlength'] = len(tmp)
        dicta['nolistlength'] = len(notmp)
        dicta['oneservernum'] = Snapserver.objects.extra(select={'servernum':'sum(hostnumber)'}).filter(fileid=file_id).values('servernum')[0].get('servernum')
        return render_to_response('hostsnap.html',dicta)

"""处理与快照文件的编辑、提交、删除、衍生相关逻辑"""
def snapdel(request,deltype,file_id):
    if deltype == "svn":
        """1. 检查当前文件是否有继承"""
        if snapreletd.objects.filter(parentid=int(file_id)).count() > 0:
            return HttpResponse("0")
        """2. 将本地的这个文件删除掉"""
        file_name = Snapshotfile.objects.get(fileid=file_id).filename
        file_absobult = AvatarConfig.svnworkplace + request.session['username'] + '/' + file_name[0] + '/' + file_name
        logging.debug(file_absobult)
        if os.path.isfile(file_absobult):
            if model_file_is_svn(file_absobult):
                logging.debug("file in svn")
                """表示当前这个文件在版本库里面"""
                if svn_delete_file(file_absobult,username=request.session["username"],password=request.session["password"])  == "error":
                    """表示SVN删除失败"""
                    return HttpResponse("2")
            else:
                logging.debug("file notin svn")
                os.unlink(file_absobult)
            Message.objects.create(enname=request.session["username"],content="用户删除快照"+str(file_name))
    return HttpResponse("1")


def logindo(request,logintype):
    if logintype == "logincofirm":
        username = request.POST.get('username','').strip()
        password = request.POST.get('password','').strip()
        if username == "" or password == "":
            return HttpResponse("<script>alert('用户名密码输入有误');history.go(-1);</script>")
        
    
        """调用登录的方法"""
        mlogin = svn_check_username(username=username,password=password,svn_respotiy_url=AvatarConfig.SVN_URL)
        if mlogin:
            try:
                tmp = create_dir(username,password,AvatarConfig.SVN_URL,AvatarConfig.svnworkplace+username)
                if not tmp:
                    return HttpResponse("<script>alert('文件checkout失败');history.go(-1);</script>")
                Message.objects.create(enname=username,content="用户登录阿凡达系统")
                UserLogin.objects.create(chname=username)
            except Exception,e:
                logging.debug(str(e))
                return HttpResponse("<script>alert('系统出错');history.go(-1);</script>")
            request.session["username"] = username
            request.session["password"] = password
            cache.delete('tname')
            return HttpResponseRedirect('/index/')
        else:
            return HttpResponse("<script>alert('用户名密码输入有误');history.go(-1);</script>")
    elif logintype == "userexit":
        try:
            del request.session['username']
            del request.session['password']
            cache.delete('tname')
        except KeyError:
            pass
        return HttpResponseRedirect('/login/')
    else:
        raise Http404()

"""查看报表"""
def report(request):
    dicta = (leftpage(request))
    concename = "select chname from tbname where enname=userlogin.chname";
    loginlist = UserLogin.objects.extra(select={'a':concename}).values('a','chname','times').order_by("-times")[:30]
    dicta['loginlist'] = loginlist
    historylist = History.objects.all().order_by('-id')[:30]
    dicta['historylist'] = historylist
    """提取快照表与调用表得到两个数组时间06-01 & 次数    前15天的调用情况"""
    mydates = getprelist(15)
    commitlist = Snapshotfile.dateascount(mydates)#[['2011-06-19', 1L], ['2011-06-18', 1L], ['2011-06-17', 1L], ['2011-06-16', 0L]]
    getlist = History.dateascount(mydates)
    
    
    dicta['maxnum'] = getlist[-1] + 10
    
    dicta['commitarray'] = commitlist
    dicta['getlist'] = getlist
    return render_to_response("report.html",dicta)




"""
自定义500错误
"""
def my_custom_error_view(request):
    return render_to_response("500.html")