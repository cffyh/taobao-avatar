# -*- coding: utf-8 -*- 
"""
定义系统中与SVN相关的方法供VIEW层调用
调用的时候事先new一个对象依据session里面的用户名与密码
"""
import pysvn
from Avatar.Config import AvatarConfig
class Basesvn:
    baseWorkingDir = AvatarConfig.svnworkplace
    svn_url = AvatarConfig.SVN_URL
    
    def __init__(self,svnuser='',svnpassword=''):
        SVNUser = svnuser
        SVNPasswd = svnpassword
    
    def _svnlogin(self, realm, username, may_save):
        return True, self.SVNUser, self.SVNPasswd, True
        
    def svnco(self, localPath = ''):
        if not localPath:
            localPath = self.baseWorkingDir+self.SVNUser
        svnClient = pysvn.Client()
        svnClient.callback_get_login = self._svnlogin
        try:
            svnClient.checkout(self.svn_url, localPath)
        except:
            return {'status':False,'content':'CheckOut ERROR!'}
        return {'status':True,'content':'CheckOut OK!'}