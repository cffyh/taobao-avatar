#coding:utf-8
from django import template
from django.shortcuts import render_to_response
from django.template import Context
from django.template.loader import get_template
from django.template import  Template
from django.utils.encoding import smart_str, smart_unicode
from Avatar.snapshot.models import tbname
import logging
register = template.Library()
"""
由于SVN在获取目录的时候没法关联到数据表所以添加一个过滤器
value:数据集。将其分割抽取出来不重复的名称
{% for objlog in svnlog %}
                {{objlog.author|enconvertch}}&nbsp;&nbsp;
            {% endfor %}
"""
@register.filter(name='enconvertch')
def enconvertch(value):
    chname = ""
    try:
        chname = tbname.objects.get(enname=value).chname
    except Exception,e:return value
    t = Template(chname)
    c = Context()
    html = t.render(c)
    return html
register.filter('enconvertch', enconvertch)