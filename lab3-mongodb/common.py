from pathlib import Path
from pymongo import MongoClient
from bson import json_util

ROOT = Path(__file__).resolve().parent
client = MongoClient('mongodb://127.0.0.1:27017/', serverSelectionTimeoutMS=5000)
db = client['lab3-mongodb']

def export(script, data):
    path = Path(script).with_suffix('.json')
    path.write_text(json_util.dumps(data, indent=2), encoding='utf-8')
    print('JSON exported:', path.name)
