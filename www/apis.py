#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-09-23 20:10
# @Author  : sucan (416570018@qq.com)
# @Version : 1.0

import hashlib
import logging
import asyncio
import time
import json
from aiohttp import web
from www.webframe.requesthandler import get,post
from www.webframe.verify import check_email_passwd,check_string,check_admin,set_valid_value
from www.models import User,Blog,Comment,next_id
from www.errors import APIValueError,APIPermissionError,APIResourceNotFoundError,APIError
from www.config.config import configs
from www.filters import marked_filter

COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret

#计算加密cookie
def user2cookie(user,max_age):
    """
    generate cookie by str user
    :param user:
    :param max_age:
    :return:
    """
    # build cookie string by :id-expires-sha1
    expires = str(int(time.time()) + max_age)       #expiration time
    s = '%s-%s-%s-%s' %(user.id,user.password,expires,_COOKIE_KEY)
    L = [user.id,expires,hashlib.sha1(s.encode("utf-8")).hexdigest()]
    return '-'.join(L)

#计算解密cookie
@asyncio.coroutine
def cooike2user(cookie_str):
    """
    Parse cookie and load user if cookie is invalid

    """
    if not cookie_str:
        return None
    try:
        L = cookie_str.split("-")
        if len(L) != 3:
            return None
        uid,expires,sha1 = L
        if int(expires) < time.time():
            return None
        user = yield from User.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.password, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode("utf-8")).hexdigest():
            logging.info('invalid sha1')
            return None
        user.password = "******"
        return user
    except Exception as e:
        logging.exception(e)
        return None

#register API
@post("/api/users")
#accept params from web and insert params into table
def api_register(*,name,email,password):
    logging.info("enter")
    check_string(name=name)
    check_email_passwd(email,name)
    users = yield from User.findAll('email = ?',[email])
    if users:
        raise APIValueError("email","Email is already in used")
    uid = next_id()
    sha1_passwd = '%s:%s' % (email, password)
    user = User(name=name.strip(),email=email,password=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),image="/static/img/user.png",admin=0)
    yield from user.save()

    #make session cooike
    r = web.Response()
    r.set_cookie(COOKIE_NAME,user2cookie(user,86400),max_age=86400,httponly=True)
    user.password = '******'
    r.content_type="application/json"
    r.body = json.dumps(user,ensure_ascii=False).encode("utf-8")
    return r

#login API
@post('/api/authenticate')
def authenticate(*,email,password):
    if not email:
        raise APIValueError('email','email is Invalid')
    if not password:
        raise APIValueError('password','Invalid password')
    users = yield from User.findAll('email = ?', [email])
    if len(users) == 0:
        raise  APIValueError('email','email is not exsists')
    user = users[0]
    #check password
    sha1 = hashlib.sha1()
    sha1.update(user.email.encode('utf-8'))
    sha1.update(b':')
    sha1.update(password.encode('utf-8'))
    if user.password != sha1.hexdigest():
        raise APIValueError("password","Invalid password")

    #authenticate is ok ,set cookie
    r = web.Response()
    r.set_cookie(COOKIE_NAME,user2cookie(user,86400),max_age=86400,httponly=True)
    user.password = "******"
    r.content_type = 'application/json'
    r.body = json.dumps(user,ensure_ascii=False).encode("utf-8")
    return r

#create new blog
@post('/api/blogs')
def api_create_blog(request,*,name,summary,content):
    check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name','name cannot be empty.')
    if not summary  or not summary.strip():
        raise APIValueError('summary','summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content','content cannot be empty.')
    blog_markdown_content = marked_filter(content.strip())
    blog = Blog(user_id = request.__user__.id,user_name = request.__user__.name,user_image = request.__user__.image,
                name = name.strip(),summary = summary.strip(),content = blog_markdown_content)
    yield from blog.save()
    return blog

#define a class Page to save the paging information
class Page(object):
    def __init__(self,item_count,page_index=1,page_size=3):
        self.item_count = item_count
        self.page_count = item_count // page_size + (1 if item_count % page_size > 0 else 0)        #last page
        self.page_size = page_size
        if (item_count == 0) or (page_index > self.page_count):
            self.offset = 0
            self.limit = 0
            self.page_index = 1
        else:
            self.page_index = page_index              #当前页
            self.offset = self.page_size * (page_index -1) #数据库查询时使用，偏移量
            self.limit = self.page_size                #一页有多少个元素
        self.has_next = self.page_index < self.page_count          #判断是否有下一页
        self.has_previous = self.page_index > 1                #判断是否有下一页

    def __str__(self):
        return 'item_count: %s, page_count: %s, page_index: %s, page_size: %s, offset: %s, limit: %s' % (
        self.item_count, self.page_count, self.page_index, self.page_size, self.offset, self.limit)

        __repr__ = __str__

#update  blog
@post('/api/blogs/{id}')
def update_blog(id,request,*,name,summary,content):
    check_admin(request)
    blog = yield from Blog.find(id)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog.name = name.strip()
    blog.summary = summary.strip()
    blog.content = content.strip()
    yield from blog.update()
    return blog

#delete blog
@post('/api/blogs/{id}/delete')
def api_delete_blog(request,*,id):
    check_admin(request)
    blog = yield from Blog.find(id)
    yield from blog.remove()
    return dict(id=id)

#管理博客
@get('/api/blogs')
async def api_blogs(*,page=1,size=10):
    num = await Blog.findNumber('count(id)')
    page = Page(num,set_valid_value(page),set_valid_value(size,10))
    if num == 0:
        return dict(page=page,blogs=())
    blogs = await Blog.findAll(orderBy='created_at desc',limit=(page.offset,page.limit))
    return dict(page=page,blogs=blogs)

#取一篇博客
@get('/api/blogs/{id}')
def api_get_blog(*, id):
    blog = yield from Blog.find(id)
    return blog

#管理用户
@get('/api/users')
def manage_users(*,page=1,size=10):
    num = yield from User.findNumber('count(id)')
    page = Page(num,set_valid_value(page),set_valid_value(size,10))
    if num == 0:
        return dict(page=page,users=())
    users = yield from User.findAll(orderBy='created_at desc',limit=(page.offset,page.limit + num % page.limit))
    for u in users:
        u.password = '******'
    return dict(page=page,users=users)
