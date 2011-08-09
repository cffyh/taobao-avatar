#!/usr/bin/env python
#-*-coding:utf-8-*-
"""
post-commit程序，实现对SVN的增、删、改
@author: yaofang.zjl@taobao.com
"""
import sys,os
import logging
from time import strftime, localtime
from optparse import OptionParser
import urllib
class Pubclilog():
    def __init__(self):
        self.logfile = '/tmp/avatar_post_commit.txt'
    def initLog(self):
        logger = logging.getLogger()
        filehandler = logging.FileHandler(self.logfile)
        streamhandler = logging.StreamHandler()  
        fmt = logging.Formatter('%(asctime)s, %(funcName)s, %(message)s') 
        logger.setLevel(logging.DEBUG)   
        logger.addHandler(filehandler)   
        logger.addHandler(streamhandler)  
        return [logger,filehandler]  
class BaseSvn:
    def __init__(self,log_switch,svnpath,svnrevision):
        self.svnbin = "/usr/local/svn/bin"
        self.log_switch=log_switch  
        self.svnpath = svnpath
        self.svnrevision = svnrevision
        self.interurl = "http://10.232.xxx.xxx/svn/"		#当前跑WEB接口的URL

    def _svninfo(self):
        cmd = '%s/svnlook author %s -r %s'% (self.svnbin, self.svnpath, self.svnrevision)
        return [os.popen(cmd, 'r').readlines()[0].replace('\n',''),strftime("%Y-%m-%d %H:%M:%S",localtime())]
    
    def _svnpostdb(self):
        logapp = Pubclilog()
        logger,hdlr = logapp.initLog()
        try:
            author_time = self._svninfo()
            cmd = '%s/svnlook changed %s -r %s'% (self.svnbin, self.svnpath, self.svnrevision)
            content = os.popen(cmd).readlines()
            for line in content:
                svntype = line[0:1]
                svncont = line.split('  ')[-1]
                if svncont.count('/') == 1:
                    filename = svncont.split('/')[-1].strip()
                    filemenu = svncont.split('/')[0].strip()
                    if filename != "":
                        firstle = filename[0]
                        if firstle.lower() == filemenu.lower():
                            logger.info(svntype)
                            if svntype == 'A':
                                params = urllib.urlencode({'filename':filename,"author":author_time[0],'lastmt':author_time[1]})
                                url_handle=urllib.urlopen(self.interurl+"A/",params)
                                data = url_handle.read()
                                logger.info("============Add end=================")
                            elif svntype == 'D':
                                logger.info("===============Delete file===================")
                                params = urllib.urlencode({'filename':filename})
                                url_handle=urllib.urlopen(self.interurl+"D/",params)
                                data = url_handle.read()
                                logger.info(str(data))
                                logger.info("===============Delete file End===================")
                            elif svntype == 'U':
                                logger.info("===============Update file===================")
                                params = urllib.urlencode({'filename':filename,"author":author_time[0],'lastmt':author_time[1]})
                                url_handle=urllib.urlopen(self.interurl+"U/",params)
                                data = url_handle.read()
                                logger.info(str(data))
                                logger.info("===============Update file End===================")
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
        pass
"""
应用启动
@param svnpath: 代码库目录
@param svnrevision:最新版本号
@param logswitch:  日志开关
@return :None  
"""
def startpost(**args):
    app=BaseSvn(args.get('logswitch'),args.get('svnpath'),args.get('svnrevision'))  
    app._svnpostdb()  
    app=None  
    return None


if __name__ == '__main__':
    """
    python postcommit.py  -p /opt/svn/data -r 10
    print opts.log_switch
    print opts.path
    print opts.revision
    if opts.verbose:
        print "SVN COMMIT-POST V1.0 Beta."
        sys.exit()
    """
    MSG_USAGE = "postcommit.py [-p][-r] -l [on|off] [-v]"
    parser = OptionParser(MSG_USAGE)
    parser.add_option("-l","--log",action="store",dest="log_switch",type="string",default="on")
    parser.add_option("-p","--path", action="store", dest="path",help="SVN版本目录".decode('utf-8'))
    parser.add_option("-r","--revision", action="store", dest="revision",help="SVN版本库号".decode('utf-8'))
    parser.add_option("-v","--version", action="store_true", dest="verbose", help="versionlook".decode('utf-8'))  
    opts, args = parser.parse_args()  
    
    if opts.verbose:  
        print "Post-commit V1.0 beta."  
        sys.exit(0)
    
    if opts.log_switch=="on":  
        log_switch="on"  
    else:  
        log_switch="off" 
    startpost(svnpath=opts.path,svnrevision=opts.revision,logswitch=log_switch)  
    sys.exit(0)
