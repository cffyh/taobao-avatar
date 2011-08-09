# -*- coding: utf-8 -*- 
"""
定义系统中用到的常量
"""
class AvatarConfig:
    svnworkplace = '/home/yaofang.zjl/Avatar/workspace/'
    svnexport = '/home/yaofang.zjl/Avatar/export/'
    svncommand   = '/usr/bin/svn'
    SVN_URL = 'xxxxxx'  #填写仓库URL.即你的快照文件的URL
    cachetime = 360
    perpage = 15
    """定义快照文件名称不可以以下后缀结尾"""
    snapprefix = ['.php','.py']
    svnusername = "avatar"      #定义一个SVN用户
    svnpassword = "avatar"      #定义一个SVN密码