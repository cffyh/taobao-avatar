#coding:utf-8
from django import template
from django.shortcuts import render_to_response
from django.template import Context
from django.template.loader import get_template
from django.template import  Template
from django.utils.encoding import smart_str, smart_unicode
import logging
register = template.Library()
"""
由于SVN在获取目录的时候没法关联到数据表所以添加一个过滤器
"""
@register.filter(name='searchvalue')
def searchvalue(value,keywords):
    myresult = value.replace(keywords,"<font color='red'>"+keywords+"</font>")
    t = Template(myresult)
    c = Context()
    html = t.render(c)
    return html
register.filter('searchvalue', searchvalue)