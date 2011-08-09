#!/usr/bin/env python
#-*-coding:utf-8-*-
"""
initdate 实现将线上的SVN数据拉到DB中
1.遍历目录
2.解析作者、最后修改时间、最后修改人、修订次数、`filename` 、类型
@author: yaofang.zjl@taobao.com
"""
import sys,os
from subprocess import Popen, PIPE
import MySQLdb,time
import logging,locale
from time import strftime, localtime
from optparse import OptionParser
locale_encoding = locale.getpreferredencoding()
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
svn_log_args = ['log', '--xml', '-v','--username','xxxxxx','--password','xxxxxx','--no-auth-cache']

class Pubclilog():
    def __init__(self):
        self.logfile = '/tmp/initdate.txt'
    def initLog(self):
        logger = logging.getLogger()
        filehandler = logging.FileHandler(self.logfile)
        streamhandler = logging.StreamHandler()  
        fmt = logging.Formatter('%(asctime)s, %(funcName)s, %(message)s') 
        logger.setLevel(logging.DEBUG)   
        logger.addHandler(filehandler)   
        logger.addHandler(streamhandler)  
        return [logger,filehandler]  

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

"""
程序处理主体
"""
class BaseSvn:
    def __init__(self,log_switch,svnpath):
        self.conn = MySQLdb.connect(db='avatar',host='xxx.xxx.xxx.xxx', user='admin',passwd='xxxxxx',charset='utf8') 
        self.svnbin = "/usr/local/svn/bin"
        self.log_switch=log_switch  
        self.svnpath = svnpath
    
    
    def _svn_date_to_timestamp(self,svn_date):
        date = svn_date.split('.', 2)[0]
        time_tuple = time.strptime(date, "%Y-%m-%dT%H:%M:%S")
        return strftime("%Y-%m-%d %H:%M:%S",(time_tuple))
    
    """返回作者、最后修改人、最后修改时间"""
    def parse_svn_log_xml(self,xml_string):
        d = {}
        tree = ET.fromstring(xml_string)
        tmp = tree.findall('logentry')
        """第一个元素即为作者"""
        author = tmp[0].find('author')
        d['author'] = author is not None and author.text or None
        lastml = tmp[len(tmp) - 1].find('author')
        d['lastml'] = lastml is not None and lastml.text or None
        lastmt = tmp[len(tmp) - 1].find('date')
        d['lastmt'] = lastmt is not None and self._svn_date_to_timestamp(lastmt.text) or None
        d['modifcount'] = len(tmp)
        return d


    """运行SVN命令"""
    def run_svn(self,args, fail_if_stderr=False, encoding="utf-8"):
        def _transform_arg(a):
            if isinstance(a, unicode):
                a = a.encode(encoding or locale_encoding)
            elif not isinstance(a, str):
                a = str(a)
            return a
        t_args = map(_transform_arg, args)
        cmd = find_program("/usr/local/svn/bin/svn")
        cmd_string = str(" ".join(map(shell_quote, [cmd] + t_args)))
        print cmd_string
        pipe = Popen([cmd] + t_args, executable=cmd, stdout=PIPE, stderr=PIPE)
        out, err = pipe.communicate()
        if pipe.returncode != 0 or (fail_if_stderr and err.strip()):
            print("External program failed (return code %d): %s\n%s"
                % (pipe.returncode, cmd_string, err))
            return "error"
        return out
    def run_svn_log(self,svn_url_or_wc, rev_start=0, rev_end=0, stop_on_copy=False):
        if stop_on_copy:
            args = ['--stop-on-copy']
        else:
            args = []
        args += [svn_url_or_wc]
        xml_string = self.run_svn(svn_log_args + args)
        return self.parse_svn_log_xml(xml_string)
    
        """
    作用：解析指定的工作拷贝目录的全部文件
    """
    def _svnpostdb(self):
        logapp = Pubclilog()
        logger,hdlr = logapp.initLog()
        self.cursor = self.conn.cursor()  
        try:
            logger.info("Starting+++++++++++++++++++++")
            for root,dirs,files in os.walk(self.svnpath):
                for f in files:
                    if root.find('.svn') > 0:pass
                    else:
                        if f.find('@') > 0:absoulepath = root+"/"+f + "@"
                        else:absoulepath = root+"/"+f
                        firstle = f[0]
                        myresult = self.run_svn_log(absoulepath)
                        sql = "insert into `snapshot` (filename,filetype,author,lastpl,lastmt,`modifynum` ) values('%s','%s','%s','%s','%s',%d)" % (f,firstle,myresult.get('author'),myresult.get('lastml'),myresult.get('lastmt'),int(myresult.get('modifcount')))
                        print sql
                        self.cursor.execute(sql)  
                        self.conn.commit()
            logger.info("End+++++++++++++++++++++")
            hdlr.flush()
            logger.removeHandler(hdlr)
        except Exception,e:
            if self.log_switch=="on":  
                logapp = Pubclilog()
                logger,hdlr = logapp.initLog()
                logger.info(str(e))
                hdlr.flush()
                logger.removeHandler(hdlr)
                return
            
    def __del__(self):  
        try:  
            self.cursor.close()  
            self.conn.close()  
        except Exception,e:  
            pass  

"""
应用启动
@param svnpath: 代码库目录
@param svnrevision:最新版本号
@param logswitch:  日志开关
@return :None  
"""
def startpost(**args):
    app=BaseSvn(args.get('logswitch'),args.get('svnpath'))  
    app._svnpostdb()  
    app=None  
    return None


if __name__ == '__main__':
    """
    python initdate.py  -p /home/admin/Avatar/workspace -r 10
    print opts.log_switch
    print opts.path
    print opts.revision
    if opts.verbose:
        print "SVN COMMIT-POST V1.0 Beta."
        sys.exit()
    """
    MSG_USAGE = "initdate.py [-p] -l [on|off] [-v]"
    parser = OptionParser(MSG_USAGE)
    parser.add_option("-l","--log",action="store",dest="log_switch",type="string",default="on")
    parser.add_option("-p","--path", action="store", dest="path",help="SVN本地目录".decode('utf-8'))
    parser.add_option("-v","--version", action="store_true", dest="verbose", help="versionlook".decode('utf-8'))  
    opts, args = parser.parse_args()  
    
    if opts.verbose:  
        print "initdate V1.0 beta."  
        sys.exit(0)
    
    if opts.log_switch=="on":  
        log_switch="on"  
    else:  
        log_switch="off" 
    startpost(svnpath=opts.path,logswitch=log_switch)  
    sys.exit(0)