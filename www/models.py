import sys
sys.path.append(r"E:\Python学习\python-webapp")
from www.orm import Model,IntergerField,StringField,TextField,BooleanField,FloatField,create_pool
import asyncio
import time,uuid
def next_id():
    return "%015d%s000" % (int(time.time() * 1000),uuid.uuid4().hex)

class User(Model):
    __table__ = "users"

    id = StringField(primary_key=True,default=next_id,ddl="varchar2(50)")
    email = StringField(ddl="varchar2(50)")
    password = StringField(ddl="varchar2(50)")
    admin = BooleanField()
    name = StringField(ddl="varchar2(50)")
    image = StringField("ddl=varchar2(500)")
    created_at = FloatField(default=time.time())
class Blog(Model):
    __table__ = "blogs"

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    name = StringField(ddl='varchar(50)')
    summary = StringField(ddl='varchar(200)')
    content = TextField()
    created_at = FloatField(default=time.time())

class Comment(Model):
    __table__ = "comments"

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    blog_id = StringField(ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    content = TextField()
    created_at = FloatField(default=time.time())

