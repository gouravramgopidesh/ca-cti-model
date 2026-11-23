"""Lab 5 utility functions. Only writes to mongodb_lab5 collections."""
import json
import os
from pathlib import Path
from pymongo import MongoClient, UpdateOne, ASCENDING
from pymongo.errors import ServerSelectionTimeoutError

URI = os.getenv('LAB5_MONGO_URI','mongodb://localhost:27029')
DB = os.getenv('LAB5_DB','mongodb_lab5')

def connection():
    client = MongoClient(URI,serverSelectionTimeoutMS=5000)
    try:
        client.admin.command('ping')
    except ServerSelectionTimeoutError as exc:
        client.close()
        raise SystemExit(f'Cannot connect to MongoDB at {URI}. Ensure the CA MongoDB container is running or set LAB5_MONGO_URI.\n{exc}')
    return client,client[DB]

def data(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def seed(collection,rows,idfield):
    collection.create_index([(idfield,ASCENDING)],unique=True)
    if not rows: return 0
    result=collection.bulk_write([
        UpdateOne({idfield:row[idfield]}, {'$set':row},upsert=True) for row in rows
    ],ordered=True)
    return result.upserted_count

def dates_pipeline():
    # JSON holds ISO date strings for portability; $toDate creates a BSON Date in the pipeline.
    return {'$addFields':{'parsed_order_date':{'$toDate':'$order_date'}}}
