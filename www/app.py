import logging;logging.basicConfig(level=logging.INFO)
import  asyncio,os,json,time
from datetime import datetime
from aiohttp import web
def index(request):
    return web.Response(body= b"<h1>hello</h1>",content_type="text/html")
    #in there content_type is must else,body will become a file to need to reload but not html
@asyncio.coroutine
def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route("GET","/",index)
    srv = yield from loop.create_server(app.make_handler(),"127.0.0.1",8100)
    logging.info("sever started at http://127.0.0.1:8100....")
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
