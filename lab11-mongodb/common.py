import os, json, time
from pathlib import Path
from bson import json_util
from pymongo import MongoClient
from pymongo.errors import PyMongoError
EVIDENCE = Path('/work/evidence')
DB = 'lab11-mongodb'
def save(name, data):
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / name).write_text(json_util.dumps(data, indent=2), encoding='utf-8')
def client():
    return MongoClient(os.environ.get('MONGO_URI', 'mongodb://mongos:27017/'), serverSelectionTimeoutMS=10000)
def wait_for(fn, seconds=180):
    end = time.monotonic() + seconds
    last = None
    while time.monotonic() < end:
        try:
            value = fn()
            if value:
                return value
        except PyMongoError as exc:
            last = exc
        time.sleep(1)
    raise RuntimeError(f'Timed out: {last}')
