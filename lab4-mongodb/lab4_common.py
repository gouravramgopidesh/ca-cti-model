"""Shared, non-destructive MongoDB helpers for Lab 4.

All activities use database mongodb_lab4, NOT the CA application database.
"""
import json
import os
from pathlib import Path
from pymongo import MongoClient, ASCENDING, UpdateOne
from pymongo.errors import ServerSelectionTimeoutError

URI = os.getenv('LAB4_MONGO_URI', 'mongodb://localhost:27029')
DB_NAME = os.getenv('LAB4_DB', 'mongodb_lab4')

SCHEMA = {'$jsonSchema': {'bsonType': 'object',
    'required': ['sku', 'name', 'price', 'stock', 'tags'],
    'properties': {
        'sku': {'bsonType': 'string', 'minLength': 1},
        'name': {'bsonType': 'string', 'minLength': 1},
        'price': {'bsonType': ['int', 'long', 'double', 'decimal'], 'minimum': 0.0000001},
        'stock': {'bsonType': ['int', 'long'], 'minimum': 0},
        'tags': {'bsonType': 'array', 'items': {'bsonType': 'string'}},
        'is_active': {'bsonType': 'bool'},
    }
}}

def connect():
    client = MongoClient(URI, serverSelectionTimeoutMS=4500)
    try:
        client.admin.command('ping')
    except ServerSelectionTimeoutError as exc:
        raise SystemExit(f'MongoDB unavailable at {URI}. Start your CA Docker MongoDB or set LAB4_MONGO_URI.\n{exc}')
    db = client[DB_NAME]
    if 'products' not in db.list_collection_names():
        db.create_collection('products', validator=SCHEMA)
    else:
        db.command({'collMod': 'products', 'validator': SCHEMA, 'validationLevel': 'strict'})
    collection = db['products']
    collection.create_index([('sku', ASCENDING)], unique=True)
    return client, collection

def read_json(filepath):
    return json.loads(Path(filepath).read_text(encoding='utf-8'))

def seed(collection, filepath):
    items = read_json(filepath)
    result = collection.bulk_write([
        UpdateOne({'sku': item['sku']}, {'$setOnInsert': item}, upsert=True)
        for item in items
    ], ordered=True)
    return result.upserted_count

def show_docs(label, cursor):
    items = list(cursor)
    print(f'\n{label}: {len(items)} matching products')
    for p in items:
        print(f"  {p['sku']}: {p['name']} | price={p['price']} | stock={p['stock']} | tags={p['tags']}")
    return items
