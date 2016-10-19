import logging
import json
from aiohttp import web
from urllib import parse
import asyncio
from www.models import User
from www.config.config import configs
from www.apis import user2cookie,cooike2user,COOKIE_NAME

#在每个响应之前打印日志
async def logger_factory(app,handler):
    async def logger(request):
        logging.info("Response:%s %s" %(request.method,request.path))
        return await handler(request)
    return logger

#利用middle在处理URL之前，把cookie解析出来，并将登录用户绑定到request对象上，
# 这样，后续的URL处理函数就可以直接拿到登录用户
async def auth_factory(app,handler):
    async def auth(request):
        logging.info("check user %s %s" %(request.method,request.path))
        request.__user__ = None
        cookie_str = request.cookies.get(COOKIE_NAME)
        if cookie_str:
            user = await cooike2user(cookie_str)
            if user:
                logging.info('set current user:%s' %user.email)
                request.__user__ = user
        if request.path.startswith('/manage/') and (request.__user__ is None or not request.__user__.admin):
            return web.HTTPFound('/signin')
        return (await handler(request))
    return auth

#数据解析
async def data_factory(app,handler):
    async def parse_data(request):
        if request.method == 'POST':
            if not request.content_type:
                return web.HTTPBadRequest(text="Missing Content_type")
            content_type = request.content_type.lower()
            if content_type.startswith ('application/json'):
                request.__data__ = await request.json()
                if not isinstance(request.__data__,dict):
                    return web.HTTPBadRequest(text = "JOSN body must be object.")
            elif content_type.startswith(('application/x-www-form-urlencoded', 'multipart/form-data')):
                params = await request.post()
                request.__data__ = dict(**params)
                logging.info("request form :%s" %content_type)
            else:
                return web.HTTPBadRequest(text = "Unsupported Content-type:%s" %content_type)
        if request.method == "GET":
            qs = request.query_string
            request.__data__ = {k:v[0] for k,v in parse.parse_qs(qs,True).items() }
            logging.info("request QueryString :%s" % request.__data__)
        else:
            request.__data__ = dict()
        return await handler(request)
    return parse_data

#把任何返回值封装成浏览器可正确显示的Response对象
async def response_factory(app,handler):
    async def response(request):
        logging.info("Response handler")
        r = await handler(request)
        if isinstance(r,web.StreamResponse):
            return r
        if isinstance(r,bytes):
            resp = web.Response(body=r)
            resp.content_type = "application/octet-stream "
            return resp
        if isinstance(r,str):
            if r.startswith("redirect:"):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode("utf-8"))
            resp.content_type = "text/html;charset=utf-8"
            return resp
        if isinstance(r,dict):
            template = r.get("__template__")
            if template is None:
                resp = web.Response(body=json.dumps(r,ensure_ascii=False,default=lambda o:o.__dict__).encode("utf-8"))
                resp.content_type = "application/json;charset=utf-8"
                return resp
            else:
                #如果用jinja2进行渲染，绑定已经验证过得用户
                r['__user__'] = request.__user__
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = "text/html;utf-8"
                return resp
        if isinstance(r,int) and 100 <= r <= 600:
            return web.Response(status=r)
        if isinstance(r,tuple) and len(r) == 2:
            status,message = r
            if isinstance(status,int) and 100 <= status < 600:
                return web.Response(status=status,text=str(message))
        #default
        resp = web.Response(body=str(r).encode("utf-8"))
        resp.content_type = "text/plain;charset=utf-8"
        return  resp
    return response



