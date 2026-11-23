import os, time, json
from pathlib import Path
from pymongo import MongoClient, ReadPreference
from pymongo.errors import PyMongoError
from bson import json_util
HOSTS = os.getenv('MONGO_HOSTS', 'mongo1:27017,mongo2:27017,mongo3:27017').split(',')
USER = os.getenv('MONGO_INITDB_ROOT_USERNAME', 'labadmin')
PASSWORD = os.environ['MONGO_INITDB_ROOT_PASSWORD']

def client(hosts=None, direct=False, **kw):
    return MongoClient(hosts or HOSTS, username=USER, password=PASSWORD,
        authSource='admin', serverSelectionTimeoutMS=3000,
        **({'directConnection': True} if direct else {'replicaSet':'rs0'}), **kw)

def wait(fn, timeout=180):
    end = time.monotonic() + timeout
    last = None
    while time.monotonic() < end:
        try:
            result = fn()
            if result:
                return result
        except PyMongoError as e:
            last = e
        time.sleep(1)
    raise RuntimeError(f'Timed out: {last}')

def status(c):
    return [{'name':m['name'], 'state':m['stateStr'], 'health':m['health']} for m in c.admin.command('replSetGetStatus')['members']]

def healthy(c):
    s = status(c)
    return s if len(s)==3 and all(m['health']==1 for m in s) and sorted(m['state'] for m in s)==['PRIMARY','SECONDARY','SECONDARY'] else None

def verify_all(doc_id):
    results = {}
    for h in HOSTS:
        with client(h, direct=True, read_preference=ReadPreference.NEAREST) as c:
            results[h] = bool(wait(lambda: c.lab13.records.find_one({'_id':doc_id})))
    return results

def save(name, data):
    s = json_util.dumps(data, indent=2)
    print(s, flush=True)
    p = Path('/work/evidence')
    if p.is_dir():
        (p/name).write_text(s, encoding='utf-8')
