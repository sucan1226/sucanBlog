import re, time, json, logging, hashlib, base64, asyncio
import sys
sys.path.append(r"E:\Python学习\python-webapp")
from www.webframe.requesthandler import get,post
from www.models import User,Comment,Blog
from aiohttp import web
from www.apis import COOKIE_NAME,Page
from www.filters import marked_filter
from www.webframe.verify import set_valid_value

#首页
@get('/')
def index(*,tag='',page='1',size='3'):
    num = yield from Blog.findNumber('count(id)')
    page = Page(num,set_valid_value(page),set_valid_value(size,3))
    if num == 0:
        blogs = []
    else:
        blogs = yield from Blog.findAll(orderBy='created_at desc', limit=(page.offset, page.limit))
        #blogs = yield from Blog.findAll(orderBy='created_at desc',limit=(page.offest,page.limit))
        for blog in blogs:
            blog.content = marked_filter(blog.content)
    return {
        '__template__':'blogs.html',
        'page':page,
        'blogs':blogs,
        'tag':tag
    }

#注册
@get('/register')
def register():
    return {
        '__template__':  'register.html'
    }

#登录
@get('/signin')
def signin():
    return {
        '__template__': 'signin.html'
    }

#退出
@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r

#创建一篇新博客
@get('/manage/blogs/create')
def manage_create_blog():
    return {
        '__template__': 'manage_blog_create.html',
        'id': '',
        'action': '/api/blogs'
    }

#取某篇博客
@get('/blog/{id}')
def get_blog(id):
    blog = yield from Blog.find(id)
    comments = yield from Comment.findAll('blog_id=?',[id],orderBy='created_at desc')
    for c in comments:
        c.html_content = marked_filter(c.content)
    blog.html_content = marked_filter(blog.content)
    return {
        '__template__': 'blog.html',
        'blog':blog,
        'comments':comments
    }

#管理博客
@get('/manage/blogs')
def manage_blogs():
    return {
        '__template__': 'manage_blogs.html',
        #'page': set_valid_value(page)
        #'page_index': set_valid_value(page)
    }

#修改博客
@get('/manage/blogs/edit/{id}')
def manage_update_blog(id):
    return {
        '__template__': 'manage_blog_edit.html',
        'id': id
    }

#管理用户
@get('/manage/users')
def manage_users():
    return {
     '__template__': 'manage_user.html'
    }