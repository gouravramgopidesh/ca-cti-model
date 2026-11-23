import os, secrets, hashlib, hmac, time
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager
from typing import Literal
import jwt
from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict, Field
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError
from bson import ObjectId

client = MongoClient(os.getenv('MONGO_URI','mongodb://mongo:27017'), tz_aware=True)
db = client.tasktracker
SECRET = os.getenv('JWT_SECRET') or secrets.token_hex(32)
LIMIT = int(os.getenv('RATE_LIMIT','30'))
ISSUER = 'tasktracker-lab15'

def now(): return datetime.now(timezone.utc)
def password_hash(password, salt): return hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 250000).hex()
def init():
    db.tasks.create_index([('tenant_id',1),('created_at',-1)])
    db.tasks.create_index([('tenant_id',1),('owner_id',1),('created_at',-1)])
    db.users.create_index('username',unique=True)
    db.rate_limits.create_index('timestamp',expireAfterSeconds=0)
    for tenant in ('tenant_1','tenant_2','tenant_3','tenant_4','tenant_5'):
        for role in ('admin','user','user2'):
            name=f'{tenant}_{role}'; salt=secrets.token_hex(16)
            db.users.update_one({'username':name},{'$setOnInsert':{'username':name,'tenant_id':tenant,'role':'admin' if role=='admin' else 'user','salt':salt,'password_hash':password_hash('Lab15Demo!',salt)}},upsert=True)

@asynccontextmanager
async def lifespan(app):
    init(); yield
app=FastAPI(title='TaskTracker API - Lab 15', lifespan=lifespan)
oauth=OAuth2PasswordBearer(tokenUrl='token')

class TaskCreate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    title: str=Field(min_length=1,max_length=200)
    description: str=Field(max_length=4000)
    priority: Literal['low','medium','high']='medium'
class TaskUpdate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    title: str|None=Field(default=None,min_length=1,max_length=200)
    description: str|None=Field(default=None,max_length=4000)
    priority: Literal['low','medium','high']|None=None
    status: Literal['open','in_progress','done']|None=None
class TaskResponse(TaskCreate):
    id: str
    tenant_id: str
    owner_id: str
    status: str
    created_at: datetime

def serialize(doc):
    return {**{k:v for k,v in doc.items() if k!='_id'},'id':str(doc['_id'])}
def denied(): return HTTPException(401,'Invalid credentials or token',headers={'WWW-Authenticate':'Bearer'})
@app.get('/health')
def health(): client.admin.command('ping'); return {'ok':True}
@app.post('/token')
def token(form: OAuth2PasswordRequestForm=Depends()):
    u=db.users.find_one({'username':form.username})
    if not u or not hmac.compare_digest(u['password_hash'],password_hash(form.password,u['salt'])): raise denied()
    return {'access_token':jwt.encode({'sub':str(u['_id']),'tenant_id':u['tenant_id'],'iss':ISSUER,'iat':now(),'exp':now()+timedelta(hours=1)},SECRET,algorithm='HS256'),'token_type':'bearer'}

def current_user(token: str=Depends(oauth)):
    try:
        p=jwt.decode(token,SECRET,algorithms=['HS256'],issuer=ISSUER,options={'require':['sub','tenant_id','exp','iat','iss']})
        if not ObjectId.is_valid(p['sub']): raise ValueError()
        u=db.users.find_one({'_id':ObjectId(p['sub']),'tenant_id':p['tenant_id']})
    except (jwt.InvalidTokenError,ValueError,TypeError): raise denied()
    if not u or u['role'] not in ('admin','user'): raise denied()
    return u

def limited(response: Response,u=Depends(current_user)):
    bucket=int(time.time())//60
    key=f"{u['tenant_id']}:{u['_id']}:{bucket}"
    expiry=datetime.fromtimestamp((bucket+1)*60,timezone.utc)
    update={'$inc':{'count':1},'$setOnInsert':{'timestamp':expiry,'tenant_id':u['tenant_id'],'user_id':str(u['_id'])}}
    try: row=db.rate_limits.find_one_and_update({'_id':key},update,upsert=True,return_document=ReturnDocument.AFTER)
    except DuplicateKeyError: row=db.rate_limits.find_one_and_update({'_id':key},update,return_document=ReturnDocument.AFTER)
    remaining=max(0,LIMIT-row['count']); headers={'X-RateLimit-Limit':str(LIMIT),'X-RateLimit-Remaining':str(remaining)}
    if row['count']>LIMIT: raise HTTPException(429,'Rate limit exceeded',headers={**headers,'Retry-After':str(max(1,int(expiry.timestamp()-time.time()+1)))})
    for k,v in headers.items(): response.headers[k]=v
    return u

def scope(u,id=None):
    q={'tenant_id':u['tenant_id']}
    if u['role']!='admin': q['owner_id']=str(u['_id'])
    if id is not None:
        if not ObjectId.is_valid(id): raise HTTPException(404,'Task not found')
        q['_id']=ObjectId(id)
    return q

def found(doc):
    if not doc: raise HTTPException(404,'Task not found')
    return serialize(doc)
@app.get('/me')
def me(u=Depends(limited)): return {'id':str(u['_id']),'username':u['username'],'tenant_id':u['tenant_id'],'role':u['role']}
@app.post('/tasks/',response_model=TaskResponse,status_code=201)
def create(task:TaskCreate,u=Depends(limited)):
    doc={**task.model_dump(),'tenant_id':u['tenant_id'],'owner_id':str(u['_id']),'status':'open','created_at':now()}
    db.tasks.insert_one(doc); return serialize(doc)
@app.get('/tasks/',response_model=list[TaskResponse])
def list_tasks(u=Depends(limited)): return [serialize(d) for d in db.tasks.find(scope(u)).sort('created_at',-1)]
@app.get('/tasks/{id}',response_model=TaskResponse)
def get_task(id:str,u=Depends(limited)): return found(db.tasks.find_one(scope(u,id)))
@app.patch('/tasks/{id}',response_model=TaskResponse)
def update_task(id:str,task:TaskUpdate,u=Depends(limited)):
    q=scope(u,id); fields=task.model_dump(exclude_none=True)
    return found(db.tasks.find_one_and_update(q,{'$set':fields},return_document=ReturnDocument.AFTER) if fields else db.tasks.find_one(q))
@app.delete('/tasks/{id}')
def delete_task(id:str,u=Depends(limited)):
    if not db.tasks.delete_one(scope(u,id)).deleted_count: raise HTTPException(404,'Task not found')
    return {'deleted':True}
