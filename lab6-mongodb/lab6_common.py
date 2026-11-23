"""Shared MongoDB index-lab helpers. Uses a dedicated database, never the CTI DB."""
import os, random, time, json
from datetime import datetime, timezone
from pathlib import Path
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import OperationFailure

URI=os.environ.get('LAB6_MONGO_URI','mongodb://localhost:27029')
DATABASE=os.environ.get('LAB6_DB','mongodb_lab6')
CATEGORIES=['Electronics','Office','Home','Gaming','Mobile','Accessories']
TAGS=['wireless','premium','sale','portable','gaming','budget','new','eco']
NAME_TYPES=['Wireless Mouse','USB Keyboard','Gaming Monitor','Desk Lamp','Laptop Stand',
            'Bluetooth Headphones','Webcam','Office Chair','Phone Case','Portable Speaker']

def connect(collection):
    client=MongoClient(URI,serverSelectionTimeoutMS=12000)
    client.admin.command('ping')
    return client,client[DATABASE][collection]

def make_documents(count,seed,start=0):
    rng=random.Random(seed)
    for i in range(start,start+count):
        yield {'sku':f'LAB6-{i:07d}',
            'name':f'{rng.choice(NAME_TYPES)} Model {i:07d}',
            'category':rng.choice(CATEGORIES),
            'price':round(rng.uniform(10,500),2),
            'rating':round(rng.uniform(1,5),1),
            'stock':rng.randint(0,250),
            'tags':rng.sample(TAGS,rng.randint(1,3))}

def insert_batches(coll,docs,batch=1000):
    buf=[]
    for doc in docs:
        buf.append(doc)
        if len(buf)>=batch:
            coll.insert_many(buf,ordered=False);buf=[]
    if buf:coll.insert_many(buf,ordered=False)

def reset_workload(coll,count=50000):
    coll.drop()
    insert_batches(coll,make_documents(count,20261123))
    assert coll.count_documents({})==count

def workloads():
    # Five identical query shapes are tested with and without indexes.
    # Name prefix search is used because $text cannot run without a text index.
    return [
      ('category_price_sort',{'category':'Electronics'}, [('price',ASCENDING)],None),
      ('price_range',{'price':{'$gte':80,'$lte':150}},None,None),
      ('tag_match',{'tags':'wireless'},None,None),
      ('rating_stock',{'rating':{'$gte':4.5},'stock':{'$gt':0}},None,None),
      ('name_prefix',{'name':{'$regex':'^Wireless Mouse'}},None,None),
    ]

def execute_query(coll,workload,limit=100):
    name,filter_,sort,_=workload
    cursor=coll.find(filter_)
    if sort:cursor=cursor.sort(sort)
    return list(cursor.limit(limit))

def explain(coll,workload):
    name,filter_,sort,_=workload
    cmd={'find':coll.name,'filter':filter_,'limit':100,'batchSize':100}
    if sort:cmd['sort']=dict(sort)
    ex=coll.database.command({'explain':cmd,'verbosity':'executionStats'})
    stats=ex.get('executionStats',{})
    winning=ex.get('queryPlanner',{}).get('winningPlan',{})
    stages=[]
    def walk(x):
        if isinstance(x,dict):
            if 'stage' in x:stages.append(x['stage'])
            for v in x.values():walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    walk(winning)
    return {'query':name,'stages':list(dict.fromkeys(stages)),
            'totalDocsExamined':stats.get('totalDocsExamined'),
            'totalKeysExamined':stats.get('totalKeysExamined'),
            'nReturned':stats.get('nReturned'),
            'executionTimeMillis':stats.get('executionTimeMillis')}

def indexes():
    return [([('category',ASCENDING),('price',ASCENDING)],'ix_category_price'),
            ([('price',ASCENDING)],'ix_price'),
            ([('tags',ASCENDING)],'ix_tags'),
            ([('rating',ASCENDING),('stock',ASCENDING)],'ix_rating_stock'),
            ([('name',ASCENDING)],'ix_name')]

def create_indexes(coll,items=None):
    for keys,name in (items or indexes()):coll.create_index(keys,name=name)

def print_explain(row):
    print(f"  {row['query']:22} stages={','.join(row['stages']) or '?':24} "
          f"docs={row['totalDocsExamined']:>6} keys={row['totalKeysExamined']:>6} "
          f"returned={row['nReturned']:>4} ms={row['executionTimeMillis']}")

def write_json(name,obj):
    target=Path(__file__).parent/'outputs'/name
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(obj,indent=2,default=str),encoding='utf-8')
    print('Evidence JSON:',target)

def load_config(filename):
    return json.loads(Path(filename).read_text(encoding='utf-8'))
