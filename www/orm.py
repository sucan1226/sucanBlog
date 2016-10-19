import pymysql
import asyncio
import logging
import aiomysql
#print SQL sentence
def log(sql, args=()):
    logging.info('SQL: %s' % (sql))
#create connection pool ,each http request to get data from pool ,so,avoid frequent to connect database
@asyncio.coroutine
def create_pool(loop,**kw):
    logging.info("create database connetion pool...")
    global _pool
    #aiomysql based on PyMySQL , and provides same api, you just need to use yield from conn.f()
    # instead of just call conn.f() for every method.
    _pool = yield from aiomysql.create_pool(
        host = kw.get("host","localhost"),
        port = kw.get("port",3306),
        user = kw["user"],
        password = kw["password"],
        db = kw["db"],
        charset = kw.get("charset","utf8"),
        autocommit = kw.get('autocommit', True),
        maxsize = kw.get('maxsize', 10),          #maximum sizes of the pool.
        minsize = kw.get('minsize', 1),           #minimum sizes of the pool.
        #accept a loop instance
        loop = loop
    )

#select
@asyncio.coroutine
def select(sql,args,size=None):
    log(sql,args)
    global _pool
    with (yield  from _pool) as conn:
        cur = yield from conn.cursor(aiomysql.DictCursor)   #DictCursor cursor which returns results as a dictionary.
        yield from cur.execute(sql.replace('?','%s'),args)  #SQL sentence placeholder is?，but MySQL placeholder is %s
        #execute(query, args=None)
        #query(str) -sql statement
        #args(list) - tuple or list of arguments for sql query
        # for example: yield from cur.execute("select * from user where id = %s",(5,))
        if size:
            rs = yield from cur.fetchmany(size)
        else:
            rs = yield from cur.fetchall()
        yield from cur.close()
        s = logging.info("rows returned:%d" %len(rs))
        return rs

#insert update delete
@asyncio.coroutine
def execute(sql,args):
    log(sql)
    with (yield  from _pool) as conn:
        try:
            cur = yield from conn.cursor()
            yield from cur.execute(sql.replace('?', '%s'), args)
            affected = cur.rowcount         #Returns the number of rows that has been produced of affected.
            yield from cur.close()
        except BaseException as e:
            raise
        return affected

# 根据输入的参数生成占位符列表
def create_args_string(num):
    L = []
    for i in range(num):
        L.append("?")
    #以','为分隔符，将列表合成字符串
    return ",".join(L)

# 定义Field类，负责保存(数据库)表的字段名和字段类型
class Field(object):
    # 表的字段包含名字、类型、是否为表的主键和默认值
    def __init__(self,name,cloumn_type,primary_key,default):
        self.name = name
        self.cloumn_type = cloumn_type
        self.primary_key = primary_key
        self.default = default
    # 当打印(数据库)表时，输出(数据库)表的信息:类名，字段类型和名字
    #def __str__(self):
        #return ('<%s, %s: %s>' % (self.__class__.__name__, self.cloumn_type, self.name))

# -*- 定义不同类型的衍生Field -*-
# -*- 表的不同列的字段的类型不一样
class StringField(Field):    #similar to definition a table construction
    def __init__(self,name = None,primary_key = False,default = None,ddl = "varchar2(100)"):
         super().__init__(name,ddl,primary_key,default)
class IntergerField(Field):
    def __init__(self,name = None,primary_key = False,default = None,ddl = "int"):
         super().__init__(name,ddl,primary_key,default)
class BooleanField(Field):
    def __init__(self,name = None,primary_key = False,default = 0,ddl = "boolean"):
         super().__init__(name,ddl,primary_key,default)
class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=0.0, ddl="real"):
         super().__init__(name, ddl, primary_key, default)
class TextField(Field):
    def __init__(self,name=None,primary_key=False, default=None, ddl="Text"):
         super().__init__(name,primary_key,default,ddl)
# -*-definition Model MetaClass
# all  MetaClass inhreit type
# ModelMetaclassdefinition all Model(inhreit ModelMetaclass) child option
# -*-ModelMetaclass的工作主要是为一个数据库表映射成一个封装的类做准备：
# ***读取具体子类(user)的映射信息
# 创造类的时候，排除对Model类的修改
# 在当前类中查找所有的类属性(attrs)，如果找到Field属性，就将其保存到__mappings__的dict中，同时从类属性中删除Field(防止实例属性遮住类的同名属性)
# 将数据库表名保存到__table__中
# 完成这些工作就可以在Model中定义各种数据库的操作方法

class ModelMetaclass(type):
    # __new__ control __init__ excute
    # cls: stand for class need to __init__ ，the parmater befor instance provide by python interpreter relover(example:User andModel)
    # bases：stand for father class gather
    # attrs：class attribution method gather
    def __new__(cls, name,bases,attrs):
        #eliminate Model itself
        if name == "Model":
            return type.__new__(cls,name,bases,attrs)
        # get table name
        tablename = attrs.get("__table__",None) or name
        # attrs is dict type ,get table name if attrs have no __table__ return None，avoid return error
        logging.info("found model:%s (table:%s)" % (name,tablename))
        # get Field and primary key name
        mappings = dict()
        fields = []
        primaryKey = None
        for k,v in attrs.items():     #get class all attribution
            if isinstance(v,Field):    # judge type is or not database data type
                logging.info("found mappings:%s ==> %s" %(k,v))
                mappings[k] = v        #save into mappings
                if v.primary_key:      #data is key primary
                    #find primary key
                    if primaryKey:     #judge is or not single key primary
                        raise RuntimeError("Duplicate primary key for field:%s" %k)
                    primaryKey = k
                else:
                    fields.append(k)
        if not primaryKey:     # have no key primary raise a error
            raise  RuntimeError("Primary key not found")
        for k in mappings.keys():   # let databse type dispose of remove from attributions
            attrs.pop(k)
        escaped_fields = list(map(lambda f:"`%s`" %f,fields)) # 保存除主键外的属性名为``（运算出字符串）列表形式
        attrs["__mappings__"] = mappings     #svae data type mapping relation
        attrs["__table__"] = tablename
        attrs["__primary_key__"] = primaryKey     #primary key name
        attrs["__fields__"] = fields              #except primarykey attribution
        #construction default insert,update,delete
        #add `` inoder to avoid keyword conflict ,`` equal repr()
        attrs["__select__"] = 'select `%s`, %s from `%s`' % (primaryKey, \
                                        ', '.join(escaped_fields), tablename)
        attrs["__insert__"] = "insert into `%s` (%s,`%s`) VALUES (%s)" \
                                %(tablename,",".join(escaped_fields),primaryKey,create_args_string(\
                                len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tablename, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs["__delete__"] = "delete from `%s` WHERE `%s` = ?" %(tablename,primaryKey)
        return type.__new__(cls,name,bases,attrs)
# definition base class

# 定义ORM所有映射的基类：Model
# Model类的任意子类可以映射一个数据库表
# Model类可以看作是对所有数据库表操作的基本定义的映射


# 基于字典查询形式
# Model从dict继承，拥有字典的所有功能，同时实现特殊方法__getattr__和__setattr__，能够实现属性操作
# 实现数据库操作的所有方法，定义为class方法，所有继承自Model都具有数据库操作方法

class Model(dict,metaclass= ModelMetaclass):
    def __init__(self,**kw):
        super(Model,self).__init__(**kw)
    def __getattr__(self,key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError("'Model' object has no attribute:%s" %(key))
    def __setattr__(self, key, value):
        self[key] = value
    def getValue(self,key):
        return getattr(self,key,None)
    def getValueOrDefault(self,key):
        value = getattr(self,key,None)
        if not value:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug("using default value for %s:%s" %(key,str(value)))
                setattr(self,key,value)
        return value
    @classmethod
    @asyncio.coroutine
    def findAll(cls,where=None,args=None,**kw):
        """find objects by where clause"""
        sql = [cls.__select__]
        if where:
            sql.append("where")
            sql.append(where)
        if args is None:
            args = []
        orderBy = kw.get("orderBy",None)
        if orderBy:
            sql.append("order by")
            sql.append(orderBy)
        limit = kw.get("limit",None)
        if limit is not None:
            sql.append("limit")
            if isinstance(limit,tuple) and len(limit) ==2:
                sql.append('?,?')
                args.extend(limit)
            else:
                raise ValueError("Invalid limit value:%s" %str(limit))
        rs  = yield from select(' '.join(sql),args)
        return [cls(**r) for r in rs]
        print([cls(**r) for r in rs])

    @classmethod
    @asyncio.coroutine
    def findNumber(cls, selectField, where=None, args=None):
        ' find number by select and where. '
        sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = yield from select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']
    @classmethod
    @asyncio.coroutine
    def find(cls,primarykey):
        """find object by primarykey"""
        rs = yield from select("%s where `%s`=?" %(cls.__select__,cls.__primary_key__),[primarykey],1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])
    @asyncio.coroutine
    def save(self):
        args = list(map(self.getValueOrDefault,self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = yield from execute(self.__insert__,args)
        if rows != 1:
            logging.warn("failed insert record:affected rows:%s" %rows)
    @asyncio.coroutine
    def update(self):
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = yield from execute(self.__update__, args)
        if rows != 1:
            logging.warn('failed to update by primary key: affected rows: %s' % rows)
    @asyncio.coroutine
    def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = yield from execute(self.__delete__,args)
        if rows != 1:
            logging.warn("failed to remove by primary key:affected rows:%s" %rows)
