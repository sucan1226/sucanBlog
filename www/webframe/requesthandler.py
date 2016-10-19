import functools
import asyncio,os,inspect,logging
from aiohttp import web
from urllib import parse
from www.errors import APIError
def get(path):
    """define decorate @get ('/path')"""
    def decorate(func):
        @functools.wraps(func)
        def wrapper(*args,**kw):
            return func(*args,**kw)
        wrapper.__method__ = "GET"
        wrapper.__route__ = path
        return wrapper
    return decorate
def post(path):
    """define decorate @post ('/path')"""
    def decorate(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)

        wrapper.__method__ = "POST"
        wrapper.__route__ = path
        return wrapper
    return decorate

def get_required_kw_args(fn):       #all have no default value  keyvalue paramater
    args = []
    # inspect.signature(callable, *, follow_wrapped=True)
    #Return a Signature object for the given callable:
    #for example:
    #def foo(a, *, b:int, **kwargs):
    #   pass
    #sig = inspect.signature(foo)
    #str(sig)     '(a, *, b:int, **kwargs)'
    params = inspect.signature(fn).parameters
    for name,param in params.items():
        #inspect.Parameter.empty:A special class-level marker to specify absence of a return annotation.
        #KEYWORD_ONLY:Value must be supplied as a keyword argument. Keyword only parameters are those which appear
        #             after a * or *args entry in a Python function definition.
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
            args.append(name)
    return tuple(args)
def get_named_kw_args(fn):   #get keyVaule parmater
    args = []
    params = inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)
def has_named_kw_args(fn):  #hvae or not keyVaule parmater
    args = []
    params = inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True
def has_var_kw_args(fn):   #have or not dict parameter
    params = inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True
def has_request_arg(fn):   #have or not request parameter
    sig = inspect.signature(fn)
    params = sig.parameters
    found = False
    for name,param in params.items():
        if name == "request":
            found = True
            continue
        #request paramter cannot be the var argument
        if found and (inspect.Parameter.VAR_POSITIONAL and inspect.Parameter.VAR_KEYWORD):
            return web.HTTPBadRequest(text="request paramter cannot be the var argument")
    return found
#define RequestHandler
# RequestHandler目的就是从URL函数中分析其需要接收的参数，从request中获取必要的参数，
# URL函数不一定是一个coroutine，因此我们用RequestHandler()来封装一个URL处理函数。
# 调用URL函数，然后把结果转换为web.Response对象，这样，就完全符合aiohttp框架的要求：

#RequestHandler就是View（网页） → Controller（路由）的桥梁了
#RequestHandler work step procedure process in below
#获取Controller（路由）所需的参数列表
#把 request（请求）携带的数据解析成Controller（路由）的参数
#检查解析的参数是否正确  （this we  have done  in above）
#最后把参数传送给Controller（路由）
class RequestHandler(object):
    def __init__(self,app,fn):
        self._app = app
        self._func = fn
        self._has_request_arg = has_request_arg(fn)
        self._has_var_kw_arg = has_var_kw_args(fn)
        self._has_named_kw_args = has_named_kw_args(fn)
        self._named_kw_args = get_named_kw_args(fn)
        self._required_kw_args = get_required_kw_args(fn)
#一个 Controller（路由）要求的参数有哪些， 主要有三个来源：
# 1.网页中的GET和POST方法（获取/?page=10还有json或form的数据。）
# 2.request.match_info（获取@get('/api/{table}')装饰器里面的参数）
# 3.def __call__(self, request)（获取request参数）
    async def __call__(self,request):  # any class if we define a __call__ ，we can direct call it instance
        kw = None
        if self._has_var_kw_arg or self._has_named_kw_args or self._required_kw_args:
        #如果method == 'POST'时，有两种可能，Ajax的json和html的form(表单)，分别对应request.json()和request.post()。
            if request.method == "POST":
                if not request.content_type:        #content_type代表响应的内容，浏览器就是根据这个来判断响应内容。例如：text/html
                    return web.HTTPBadRequest(text="Missing content-type")
                ct = request.content_type.lower()
                if ct.startswith("application/json"):
                    params = await request.json()
                    if not isinstance(params,dict):
                        return web.HTTPBadRequest(text="JOSN body must be object.")
                    kw = params
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                    params = await request.json()
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest(text="Unsupported Content-Type:%s" % request.content_type)
                #如果method == 'GET'时，参数就是查询字符串，也就是request.query_string
            if request.method == "GET":
                qs = request.query_string
                if qs:
                    kw = dict()
                    for k,v in parse.parse_qs(qs,True).items():
                    #urllib.parse.parse_qs:Parse a query string given as a string argument (data of type application/x-www-form-urlencoded).
                    #  Data are returned as a dictionary. The dictionary keys are the unique
                    # query variable names and the values are lists of values for each name.
                     kw[k] = v[0]
        # 获取match_info的参数值，例如@get('/blog/{id}')之类的参数值
        if kw is None:
            kw = dict(**request.match_info)
        else:
            if not self._has_var_kw_arg and self._named_kw_args:
                #remove all unnamed kw
                copy = dict()
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy
            #check name arg:
            for k,v in request.match_info.items():
                if k in kw:
                    logging.warn("Duplicate arg name in named arg and kw args:%s" %k)
                kw[k] = v

        #如果有request参数的话也加入
        if self._has_request_arg:
            kw["request"] = request
        #check required kw:
        if self._required_kw_args:
            for name in self._required_kw_args:
                if not name in kw:
                    return web.HTTPBadRequest(text="Missing argument:%s" %name)
        logging.info("call with args:%s" %str(kw))
        try:
            r = await self._func(**kw)
            return r
        except APIError as e :
            return dict(error=e.error,data=e.data,message=e.message)
# 添加静态文件夹的路径
def add_static(app):
    #os.path.abspath(os.path.join(os.path.dirname(__file__),os.path.pardir))  回到父级目录
    parent_path = os.path.abspath(os.path.join(os.path.dirname(__file__),os.path.pardir))
    path = os.path.join(parent_path, 'static')
    app.router.add_static("/static",path)
    logging.info("add static %s => %s" %("/static/",path))

# def add_route(app,fn):
#      method = getattr(fn,"__method__",None)
#      path = getattr(fn,"__route__",None)
#      if path is None or method is None:
#          raise ValueError("@get or @post not defined in %s" %str(fn))
#      if not asyncio.iscoroutine(fn) and not inspect.isgeneratorfunction(fn):
#          fn = asyncio.coroutine(fn)
#      logging.info("add route %s %s => %s(%s)" %(method,path,fn.__name__,",".join(inspect.signature(fn).parameters.keys())))
#      app.router.add_route(method,path,RequestHandler(app,fn))

# 添加一个模块的所有路由
def add_routs(app,moudle_name):
    #n = moudle_name.rfind(".")
    #if n == -1:
        #mod = __import__(moudle_name,globals(),locals())
    #else:
        #name = moudle_name[n+1:]
        #mod = getattr(__import__(moudle_name[:n],globals(),locals(),[name]),name)
    try:
        mod = __import__(moudle_name,fromlist=["get_submoudle"])
    except ImportError as e:
        raise e
    # 遍历mod的方法和属性,主要是找处理方法
    # 由于我们定义的处理方法，被@get或@post修饰过，所以方法里会有'__method__'和'__route__'属性
    for attr in dir(mod):
        # 如果是以'_'开头的，一律pass，我们定义的处理方法不是以'_'开头的
        if attr.startswith("_"):
            continue
        # 获取到非'_'开头的属性或方法
        fn = getattr(mod,attr)
        # 取能调用的，说明是方法
        if callable(fn):
            # 检测'__method__'和'__route__'属性
            method = getattr(fn,"__method__",None)
            path = getattr(fn,"__route__",None)
            # 如果都有，说明是我们定义的处理方法，加到app对象里处理route中
            if method and path:
                #add_route(method,path)
                fn = asyncio.coroutine(fn)
                args = ",".join(inspect.signature(fn).parameters.keys()) #args其实就是函数的参数
                logging.info('add route %s %s => %s(%s)' % (method, path, fn.__name__, args))
                app.router.add_route(method, path, RequestHandler(app, fn))


