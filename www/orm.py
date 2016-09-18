import pymysql
import asyncio
import logging
import aiomysql
#create connection pool aboid frequent to connect database
@asyncio.coroutine
def create_pool(loop,**kwargs):
    logging.info("create database connetion pool...")
    global _pool
    _pool = yield from aiomysql.create_pool(
        host = kwargs.get("host","localhost"),
        port = kwargs.get("port",3306),
        user = kwargs["user"],
        password = kwargs["password"],
        db = kwargs["db"],
        charset = kwargs.get("charset","utf8"),
        autocommit = kwargs.get('autocommit', True),
        maxsize = kwargs.get('maxsize', 10),
        minsize = kwargs.get('minsize', 1),
        loop = loop
    )

#select
@asyncio.coroutine
def select(sql,args,size=None):
    #log(sql,args)
    global _pool
    with (yield  from _pool) as conn:
        cur = yield from conn.cursor(aiomysql.DictCursor)
        yield from cur.excute(sql.replace("?","%s"),args or())
        if size:
            rs = yield
        else:
            rs = yield from cur.fetchall()
        yield from cur.close()
        s = logging .info("rows returned:%s" %len(rs))

#insert update delete
@asyncio.coroutine
def excute(sql,args):
    with (yield  from _pool) as conn:
        try:
            cur = yield from conn.cursor()
            yield from cur.excute(sql.replace("?","%s"),args)
            affected = cur.rowcount
            yield from cur.close()
        except BaseException as e:
            raise
        return affected

if __name__ == "__main__":
    pass

