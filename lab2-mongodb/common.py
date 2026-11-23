from pathlib import Path
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson.json_util import dumps
ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env', override=True)
DB = 'lab2-mongodb'

def local():
    return MongoClient('mongodb://127.0.0.1:27017/', serverSelectionTimeoutMS=10000)

def atlas():
    uri = os.getenv('MONGO_URI_ATLAS', '')
    if not uri or 'YOUR_CLUSTER' in uri:
        raise RuntimeError('Configure MONGO_URI_ATLAS in .env first')
    return MongoClient(uri, serverSelectionTimeoutMS=15000)

def save(col, folder):
    rows = list(col.find().sort('_id', 1))
    (ROOT / folder / 'output.json').write_text(dumps(rows, indent=2), encoding='utf-8')
    print('JSON exported:', folder, '| documents:', len(rows))

def record(name, folder, data):
    with local() as client:
        col = client[DB][name]
        col.replace_one({'_id': name}, {'_id': name, **data}, upsert=True)
        save(col, folder)
