# -*- coding: utf-8 -*- 
#!/usr/bin/env python
""" 
Svnaction.py
@author: yaofang.zjl@taobao.com
@todo: 通过SVN命令获取相关SVN操作
"""
from datetime import datetime

import os
import sys
import time
import locale
import shutil
import select
import calendar
import traceback
from time import strftime, localtime
from optparse import OptionParser
from subprocess import Popen, PIPE
from datetime import datetime
import logging

from Avatar.Config import AvatarConfig


try:
    from xml.etree import cElementTree as ET
except ImportError:
    try:
        from xml.etree import ElementTree as ET
    except ImportError:
        try:
            import cElementTree as ET
        except ImportError:
            from elementtree import ElementTree as ET

svn_log_args = ['log', '--xml', '-v','--username','avatar','--password','avatar','--no-auth-cache']
svn_log_args_chk = ['log','--xml', '-v','--username','avatar','--password','avatar','--no-auth-cache']
svn_info_args = ['info', '--xml','--username','avatar','--password','avatar','--no-auth-cache']
svn_checkout_args = ['checkout', '-q']
svn_status_args = ['status', '--xml', '-v','--show-updates' ,'--ignore-externals','--username',AvatarConfig.svnusername,'--password',AvatarConfig.svnpassword,'--no-auth-cache']
svn_respotiy_url = AvatarConfig.SVN_URL 

# define exception class
class ExternalCommandFailed(RuntimeError):
    """
    An external command failed.
    """

class ParameterError(RuntimeError):
    """
    An external command failed.
    """
    
def display_error(message, raise_exception = True):
    import logging
    """
    Display error message, then terminate.
    """
    logging.debug(message)
    print
#    if raise_exception:
#        raise ExternalCommandFailed
#    else:
#        sys.exit(1)


if os.name == "nt":
    def find_program(name):
        # See MSDN for the REAL search order.
        base, ext = os.path.splitext(name)
        if ext:
            exts = [ext]
        else:
            exts = ['.bat', '.exe']
        for directory in os.environ['PATH'].split(os.pathsep):
            for e in exts:
                fname = os.path.join(directory, base + e)
                if os.path.exists(fname):
                    return fname
        return None
else:
    def find_program(name):
        """
        Find the name of the program for Popen.
        On Unix, popen isn't picky about having absolute paths.
        """
        return name

def shell_quote(s):
    if os.name == "nt":
        q = '"'
    else:
        q = "'"
    return q + s.replace('\\', '\\\\').replace("'", "'\"'\"'") + q

locale_encoding = locale.getpreferredencoding()

"""运行SVN命令"""
def run_svn(args, fail_if_stderr=False, encoding="utf-8"):
    """
    Run svn cmd in PIPE
    exit if svn cmd failed
    """
    def _transform_arg(a):
        if isinstance(a, unicode):
            a = a.encode(encoding or locale_encoding)
        elif not isinstance(a, str):
            a = str(a)
        return a
    t_args = map(_transform_arg, args)

    cmd = find_program("svn")
    cmd_string = str(" ".join(map(shell_quote, [cmd] + t_args)))
    import logging
    logging.debug(cmd_string)
    pipe = Popen([cmd] + t_args, executable=cmd, stdout=PIPE, stderr=PIPE)
    out, err = pipe.communicate()
    if pipe.returncode != 0 or (fail_if_stderr and err.strip()):
        display_error("External program failed (return code %d): %s\n%s"
            % (pipe.returncode, cmd_string, err))
        return "error"
    return out
"""
SVN里面出来的时间如：2011-06-05T10:50:46.043090Z
解析成合法的时间戳<2011-06-05 10:50:46>
"""
def svn_date_to_timestamp(svn_date):
    date = svn_date.split('.', 2)[0]
    time_tuple = time.strptime(date, "%Y-%m-%dT%H:%M:%S")
    tmp = calendar.timegm(time_tuple)
    return datetime.fromtimestamp(tmp)

"""
Parse the XML output from an "svn log" command and extract 
useful information as a list of dicts (one per log changeset).
@param xml_string: 通过命令执行的SVN返回的结果集
<logentry
   revision="95">
<author>yifan</author>
<date>2010-12-23T02:24:26.566330Z</date>
<paths>
<path
   kind="file"
   action="A">/a/algoyt1.kgb.cnz.alimama.com</path>
</paths>
<msg>algoyt1.kgb.cnz.alimama.com.20101223</msg>
</logentry>
/usr/local/svn/bin/svn log algoyt1.kgb.cnz.alimama.com --xml -v
@return: [{}]字典列表里面存放 了日志的详细信息<线上应用只需要获取作者、时间、版本号>
"""
def parse_svn_log_xml(xml_string):
    l = []
    tree = ET.fromstring(xml_string)
    for entry in tree.findall('logentry'):
        d = {}
        d['revision'] = int(entry.get('revision'))
        # Some revisions don't have authors, most notably
        # the first revision in a repository.
        author = entry.find('author')
        d['author'] = author is not None and author.text or None
        
        
        
        d['date'] = svn_date_to_timestamp(entry.find('date').text)
        # Some revisions may have empty commit message
        message = entry.find('msg')
        message = message is not None and message.text is not None \
                        and message.text.strip() or ""
        # Replace DOS return '\r\n' and MacOS return '\r' with unix return '\n'
        d['message'] = message.replace('\r\n', '\n').replace('\n\r', '\n'). \
                               replace('\r', '\n')
        """获取变更的目录列表.带上参数-v获取"""
        """
        paths = d['changed_paths'] = []
        for path in entry.findall('.//path'):
            copyfrom_rev = path.get('copyfrom-rev')
            if copyfrom_rev:
                copyfrom_rev = int(copyfrom_rev)
            paths.append({
                'path': path.text,
                'action': path.get('action'),
                'copyfrom_path': path.get('copyfrom-path'),
                'copyfrom_revision': copyfrom_rev,
            })
        """
        l.append(d)
    
    l.reverse()
    return l


"""
Parse the XML output from an "svn status" command and extract 
useful info as a list of dicts (one per status entry).
<status>
<target
   path="algoyt1.kgb.cnz.alimama.com">
<entry
   path="algoyt1.kgb.cnz.alimama.com">
<wc-status
   props="none"
   item="normal"
   revision="536">
<commit
   revision="511">
<author>yifan</author>
<date>2011-05-30T01:28:21.514294Z</date>
</commit>
</wc-status>
</entry>
</target>
</status>
/usr/local/svn/bin/svn status algoyt1.kgb.cnz.alimama.com --xml -v
如果lock=no就表示没有上锁
"""
def parse_svn_status_xml(xml_string, base_dir=None):
    l = []
    tree = ET.fromstring(xml_string)
    for entry in tree.findall('.//entry'):
        d = {}
        path = entry.get('path')
        if base_dir is not None:
            assert path.startswith(base_dir)
            path = path[len(base_dir):].lstrip('/\\')
        d['path'] = path
        wc_status = entry.find('wc-status')
        if wc_status.get('item') == 'external':
            d['type'] = 'external'
        elif wc_status.get('revision') is not None:
            d['type'] = 'normal'
        else:
            d['type'] = 'unversioned'
        
        try:
            d['lock'] = tree.find('.//lock/token').text
        except AttributeError,e:
            print str(e)
            d['lock'] = 'no'
        print d['lock']
        
        l.append(d)
    return l


"""
Parse the XML output from an "svn info" command and extract 
useful information as a dict.
"""
def parse_svn_info_xml(xml_string):
    d = {}
    tree = ET.fromstring(xml_string)
    entry = tree.find('.//entry')
    if entry:
        d['url'] = entry.find('url').text
        d['revision'] = int(entry.get('revision'))
        d['repos_url'] = tree.find('.//repository/root').text
        d['last_changed_rev'] = int(tree.find('.//commit').get('revision'))
        
        d['kind'] = entry.get('kind')
    return d

"""
Fetch up to 'limit' SVN log entries between the given revisions.可以指定LOG的长度
@param svn_url_or_wc: 指定文件的绝对目录值
@param limit:限定的日志
"""
def run_svn_log(svn_url_or_wc, rev_start=0, rev_end=0, limit=100, stop_on_copy=False):
    if svn_url_or_wc.find('@') > 0:svn_url_or_wc = svn_url_or_wc + "@"
    if stop_on_copy:
        args = ['--stop-on-copy']
    else:
        args = []
    args += ['--limit',str(limit), svn_url_or_wc]
    xml_string = run_svn(svn_log_args + args)
    if xml_string == 'error':return []
    return parse_svn_log_xml(xml_string)

"""
Get SVN status information about the given working copy.
@param svn_wc: 指定的SVN工作目录
"""
def get_svn_status(svn_wc):
    # Ensure proper stripping by canonicalizing the path
    svn_wc = os.path.abspath(svn_wc)
    args = [svn_wc]
    xml_string = run_svn(svn_status_args + args)
    if xml_string == 'error':return []
    return parse_svn_status_xml(xml_string, svn_wc)

"""
获取SVN的INFO信息
@param svn_wc: 指定的SVN工作目录
"""
def get_svn_info(svn_wc):
    svn_wc = os.path.abspath(svn_wc)
    args = [svn_wc]
    xml_string = run_svn(svn_info_args + args)
    if xml_string == 'error':return []
    return parse_svn_info_xml(xml_string)
    
    

"""
Given an SVN log entry and an optional sequence of files, do an svn commit.
svn commit提交<编辑之后就可以直接提交>
@param files: 表示要提交的文件列表<如果文件有做过修改>
@param svnmsg: 表示要提交的说明日志
@param username: svn操作的用户名
@param password: svn所对应的密码
@return: 如果返回error就表示命令执行失败其他的就表示正常
"""
def commit_from_svn_log_entry(files=None,svnmsg = "",username="",password=""):
    options = ["commit",files,"--no-auth-cache","--username" ,username,"--password",password,"-m", svnmsg]
    return run_svn(options)

"""
判断某个文件是否已经纳入到SVN
检查原则：如果执行svn  log返回值非0就表示未纳入到SVN中
@param file: 要检查的文件绝对目录
@return: True表示在仓库中 False表示未纳入
"""
def svn_add_action(p,username="",password=""):
    run_svn(["add",p])
    return commit_from_svn_log_entry(files=p,svnmsg="Avatar system Add file",username=username,password=password)

"""
判断某个文件是否已经纳入到SVN
检查原则：如果执行svn  log返回值非0就表示未纳入到SVN中
@param file: 要检查的文件绝对目录
@return: True表示在仓库中 False表示未纳入
"""
def model_file_is_svn(file):
    if file.find('@') > 0:file = file + "@"
    
    
    
    args = ['--limit','1',file]
    xml_string = run_svn(svn_log_args_chk + args)
    if xml_string == "error":return False
    else:
        return True   

"""
将本地文件删除并提交到SVN
@param p: 要删除的文件列表<单个文件的绝对目录>
@param username: svn操作的用户名
@param password: svn所对应的密码
"""
def svn_delete_file(p,username="",password=""):
    run_svn(["remove",  p,"--username" ,username,"--password",password,"--no-auth-cache"])
    return commit_from_svn_log_entry(files=p,svnmsg="Avatar system delete file",username=username,password=password)
    

"""update本地工作目录"""
"""
@param original_wc: 本地的SVN目录<指定的文件名绝对目录>
@param username: svn操作的用户名
@param password: svn所对应的密码
"""
def svn_update(original_wc,username="",password=""):
    run_svn(["up", "--ignore-externals","--no-auth-cache","--non-interactive" ,original_wc,"--username" ,username,"--password",password])

"""
Checkout the given URL at an optional revision number.
当用户登录的时候需要checkout一份数据文件
@param svn_url: SVN仓库URL
@param checkout   :表示本地的工作拷贝目录 
@param username: svn操作的用户名
@param password: svn所对应的密码
"""
def svn_checkout(svn_url, checkout_dir, rev_number=None,username="",password=""):
    args = []
    if rev_number is not None:
        args += ['-r', rev_number]
    args += ["--username" ,username,"--password",password,'--no-auth-cache',svn_url, checkout_dir]
    return run_svn(svn_checkout_args + args)

"""
依据用户名与密码创建新目录并CO一份数据
@param username: 用户名
@param password: 密码
@param svn_url: SVN仓库URL
@param checkout   :表示本地的工作拷贝目录 
"""
def create_dir(username,password,svn_url,checkout_dir):
    """
    实现消息队列。将co 操作放到后台执行 
    """
    import pika,json
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='task_queue',durable=True)
        message = json.dumps([{"mqtype":"svnco","username":username,"password":password,"svnurl":svn_url,"workplace":checkout_dir}],ensure_ascii=True)
        channel.basic_publish(exchange='',
                          routing_key='task_queue',
                          body=message,
                          properties=pika.BasicProperties(delivery_mode=2))
        connection.close()
    except Exception,e:
        return False
    
#    if not os.path.exists(checkout_dir):
#        os.mkdir(checkout_dir)
#        tmp = svn_checkout(svn_url=svn_url,checkout_dir=checkout_dir,username=username,password=password)
#        if tmp == "error":return False
#    return True
    



"""检验指定用户名与密码是否为合法用户
@param username:用户
@param password: 相应的密码
@return: true表示合法用户>
"""
def svn_check_username(username="",password="",svn_respotiy_url=""):
    xml_string = run_svn(["ls", svn_respotiy_url,"--username" ,username,"--password",password,'--non-interactive'])
    status = (True,False)[xml_string == "error"]
    return status

"""
对指定的文件进行加锁与解锁处理
@param dotype: lock表示上锁 unlock表示解锁
@param origina: 文件绝对目录
@param username: svn操作的用户名
@param password: svn所对应的密码
@return: true表示操作成功
"""
def svn_lock_unlock(dotype='',origina='',username="",password=""):
    if dotype == 'lock':
        tmp=run_svn(["lock", origina,"--username" ,username,"--password",password,'--no-auth-cache'])
    else:
        tmp=run_svn(["unlock", origina,"--username" ,username,"--password",password,'--no-auth-cache'])
    if tmp=="error":return False
    return  True
"""
将内容写入到文件并提交到SVN!
应用场景：在编辑快照文件的时候快照名称!只是写往里面写内容
@param string: filepath表示的文件的绝对目录
@return: True表示提交成功 False表示提交失败 
"""
def model_add_package(filename='',content='',memo='',username="",password="",filepath=''):
    def _str_replace(mys):
        return mys.replace('\r\n','\n')
    namespace = _str_replace(filename)
    try:
        f = open(filepath, "w", 1024) 
        f.writelines(content.encode('utf'))
    except Exception,e:
        logging.debug("============write file fails 99999========")
        logging.debug(str(e))
        try:
            os.unlink(filepath)
        except Exception,e:pass
        return False
    return True


"""
名称相同的时候处理的提交保存
将内容覆盖原来的内容并做commit
@param filepath: 表示绝对目录值
@param content: 要写入文件的内容值
@param memo: 表示备注内容
"""
def model_edit_package(content='',memo='',username="",password="",filepath=''):
    try:
        f = open(filepath, "w", 1024) 
        f.writelines(content.encode('utf'))
    except Exception,e:
        logging.debug("============write file fails5050550========")
        logging.debug(str(e))
        print "*"*30
        return False
    """将此文件提交到SVN"""
    return True



"""
作用：导出一份指定的记录文件信息
@param sourcepath:表示源目录
@param exportpath:表示要导出的目录位置 
@revision:表示导出的版本号
"""
def exportfiles(username="",password="",sourcepath='',exportpath='',revision=0,exportparentpath=''):
    if not os.path.exists(exportparentpath):
        os.makedirs(exportparentpath)
    
    if sourcepath.find('@') > 0:sourcepath = sourcepath + "@"
    tmp = run_svn(["export", "--no-auth-cache","--non-interactive" ,"-r",revision,sourcepath,exportpath,"--username" ,username,"--password",password])
    if tmp=="error":return False
    return  True


if __name__ == '__main__':
    commit_from_svn_log_entry(files="/home/avtar/zjl/a/azjl.txt",svnmsg = "ddddddddddddddddddddddddddddddddd",username="zjl",password="zjl")