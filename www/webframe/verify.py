#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-09-23 20:10
# @Author  : sucan (416570018@qq.com)
# @Version : 1.0

import re
from www.errors import APIError,APIResourceNotFoundError,APIPermissionError,APIValueError
_RE_EMAIL = re.compile(r'^[a-zA-Z0-9\.\-\_]+\@[a-zA-Z0-9\-\_]+(\.[a-zA-Z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

#check string is or not null
def check_string(**kw):
    for field,string in kw.items():
        if not string or not string.strip():
            raise APIValueError(field,"%s cannor be empty." %field)

#check email and password is or not valid
def check_email_passwd(email,password):
    if not email or not _RE_EMAIL.match(email):
        APIValueError("%s email is invalid." %email)
    if not password or not _RE_SHA1.match(password):
        APIValueError("%s password is invalid." %password)

#check admin
def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()

# 设置合法的查询字符串参数
def set_valid_value(num_str, value=1):
    try:
        num = int(num_str)
    except ValueError:
        return value
    return num if num > 0 else value
