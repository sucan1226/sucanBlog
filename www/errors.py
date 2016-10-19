#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-09-23 20:10
# @Author  : sucan (416570018@qq.com)
# @Version : 1.0
import json,logging,inspect,functools
class APIError(Exception):
    """
    the base APIError which contains error which contains error(required),data(optional) and
    message(optional)

    """
    def __init__(self,error,data="",message=""):
        super(APIError,self).__init__(message)
        self.error = error
        self.data = data
        self.message = message

class APIValueError(Exception):
    """
    Indicate the input value has error or invalid .The data specifies the error field of imput form.

    """
    def __init__(self,field,message=""):
        super(APIValueError,self).__init__("value:invalid",field,message)

class APIResourceNotFoundError(Exception):
    """
    Indicate the resource was not found.The data specifies the resource name.

    """
    def __init__(self,field,message=""):
        super(APIResourceNotFoundError,self).__init__("value:notfound",field,message)

class APIPermissionError(Exception):
    """
    Indicate the api has no permission

    """
    def __init__(self,message=""):
        super(APIPermissionError,self).__init__("permission:forbidden","permission",message)
