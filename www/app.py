import asyncio
import logging;logging.basicConfig(level=logging.INFO)
import os
import sys
import time
from datetime import datetime
from aiohttp import web
from jinja2 import Environment,FileSystemLoader
from www import orm
from www.webframe.requesthandler import add_routs,add_static
from www.webframe.response_factory import data_factory,response_factory,logger_factory,auth_factory
from urllib import parse
#jinja2初始化函数
def init_jinja2(app,**kw):
    logging.info("init jinja2....")
    options = dict(
        autoescape = kw.get("autoescape",True),
        block_start_string=kw.get('block_start_string', '{%'),
        block_end_string=kw.get('block_end_string', '%}'),
        variable_start_string=kw.get('variable_start_string', '{{'),
        variable_end_string=kw.get('variable_end_string', '}}'),
        auto_reload=kw.get('auto_reload', True)
    )
    path = kw.get("path",None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),"templates")
    logging.info("set jinja2 template path:%s" %path)
    env = Environment(loader=FileSystemLoader(path),**options)
    filters = kw.get("filters",None)
    if filters is not None:
        for name ,f in filters.items():
            env.filters[name] = f
    app["__templating__"] = env
def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u"1分钟前"
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta < 86400:
        return u"%s小时前" %(delta // 3600)
    if delta < 604800:
        return u"%s天前" %(delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u"%s年%s月%s日" %(dt.year,dt.month,dt.day)
@asyncio.coroutine
def create_server(loop,config_mod_name):
    config = __import__(config_mod_name,fromlist=["config","config_default"])
    #print(config.config_default.configs["db"])
    yield from orm.create_pool(loop = loop, **config.config_default.configs["db"])
    app = web.Application(loop=loop, middlewares=[logger_factory,auth_factory,data_factory,response_factory])
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    add_routs(app,"handlers")
    add_routs(app,"apis")
    add_static(app)
    srv = yield from loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv







