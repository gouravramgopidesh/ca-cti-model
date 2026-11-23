import os, time, json
from pathlib import Path
from datetime import datetime, timezone
from pymongo import MongoClient, ReadPreference
from pymongo.errors import PyMongoError
from bson import json_util
HOSTS = ['mongo1','mongo2','mongo3']
URI = os.getenv('MONGO_URI', 'mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0')
DB = 'mongodb-lab9'
EVIDENCE = Path('/work/evidence')

def utc(): return datetime.now(timezone.utc).isoformat()
def connect(): return MongoClient(URI, serverSelectionTimeoutMS=4000, connectTimeoutMS=1500, socketTimeoutMS=12000, retryWrites=False)
def direct(host): return MongoClient(host, 27017, directConnection=True, read_preference=ReadPreference.SECONDARY_PREFERRED, serverSelectionTimeoutMS=900, connectTimeoutMS=900, socketTimeoutMS=7000, retryWrites=False)
def save(name, data):
    EVIDENCE.mkdir(exist_ok=True)
    (EVIDENCE/name).write_text(json_util.dumps(data, indent=2), encoding='utf-8')
def wait_for(fn, timeout=120):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        try:
            result=fn()
            if result: return result
        except PyMongoError: pass
        time.sleep(1)
    raise RuntimeError('Timed out waiting for '+fn.__name__)
def healthy():
    with connect() as c:
        s=c.admin.command('replSetGetStatus')
        m=s['members']
        if len(m)==3 and sum(x['stateStr']=='PRIMARY' and x['health']==1 for x in m)==1 and sum(x['stateStr']=='SECONDARY' and x['health']==1 for x in m)==2:
            return s

def primary():
    with connect() as c: return c.admin.command('hello')['primary'].split(':')[0]
