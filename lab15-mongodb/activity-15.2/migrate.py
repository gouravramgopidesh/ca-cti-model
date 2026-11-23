import csv, json, time, statistics, uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from bson import ObjectId
import os
client=MongoClient(os.getenv('MONGO_URI','mongodb://mongo:27017'),tz_aware=True)
# Dedicated database prevents migration tests from altering API tasks.
db=client['tasktracker_migration']; tenants=[f'tenant_{i}' for i in range(1,6)]
shared=db.tasks
# Only owned experiment collections reset.
for name in ['tasks']+[f'tasks_{t}' for t in tenants]: db.drop_collection(name)
shared.create_index([('tenant_id',1),('created_at',-1)])
base=datetime(2025,1,1,tzinfo=timezone.utc)
for t in tenants:
    shared.insert_many([{'tenant_id':t,'title':f'Task {i+1}','description':'Migration sample','status':['open','done'][i%2],'priority':['low','medium','high'][i%3],'owner_id':f'{t}_user','created_at':base+timedelta(seconds=i)} for i in range(100)])
assert shared.count_documents({})==500
validation=[]
for t in tenants:
    target=db[f'tasks_{t}']; target.create_index([('created_at',-1)])
    target.insert_many(list(shared.find({'tenant_id':t})))
    a=list(shared.find({'tenant_id':t}).sort('_id',1)); b=list(target.find().sort('_id',1))
    leaks=target.count_documents({'tenant_id':{'$ne':t}})
    assert len(a)==len(b)==100 and a==b and leaks==0
    validation.append({'tenant':t,'source':len(a),'destination':len(b),'leaks':leaks,'all_fields_equal':a==b}); print(validation[-1])

def listing_shared(t): return list(shared.find({'tenant_id':t}).sort('created_at',-1))
def listing_separate(t): return list(db[f'tasks_{t}'].find().sort('created_at',-1))
def analytics_shared(): return sorted(list(shared.aggregate([{'$group':{'_id':'$tenant_id','count':{'$sum':1}}}])),key=lambda x:x['_id'])
def analytics_separate():
    pipeline=[{'$unionWith':f'tasks_{t}'} for t in tenants[1:]]+[{'$group':{'_id':'$tenant_id','count':{'$sum':1}}}]
    return sorted(list(db[f'tasks_{tenants[0]}'].aggregate(pipeline)),key=lambda x:x['_id'])
assert analytics_shared()==analytics_separate()
for t in tenants: assert listing_shared(t)==listing_separate(t)
rows=[]
def timed(fn):
    start=time.perf_counter_ns(); result=fn(); return (time.perf_counter_ns()-start)/1e6,result

def compare(label,a,b,cleanup=None):
    samples=[[],[]]
    for i in range(35):
        order=(0,1) if i%2==0 else (1,0)
        for j in order:
            ms,result=timed((a,b)[j]);
            if cleanup: cleanup(j,result)
            if i>=5: samples[j].append(ms)
    for j,strategy in enumerate(['document-level','collection-per-tenant']):
        s=samples[j]; rows.append({'operation':label,'strategy':strategy,'runs':len(s),'median_ms':statistics.median(s),'mean_ms':statistics.mean(s),'p95_ms':sorted(s)[28]})
compare('list 100 tasks',lambda:listing_shared(tenants[0]),lambda:listing_separate(tenants[0]))
compare('cross-tenant analytics',analytics_shared,analytics_separate)
t=tenants[0]; separate=db[f'tasks_{t}']
def create(c): return c.insert_one({'_id':ObjectId(),'tenant_id':t,'title':'Benchmark','description':'test','owner_id':'bench','status':'open','priority':'medium','created_at':datetime.now(timezone.utc)}).inserted_id
compare('create task',lambda:create(shared),lambda:create(separate),lambda j,id:(shared if j==0 else separate).delete_one({'_id':id,'tenant_id':t}))
assert shared.count_documents({})==500
for t in tenants: assert list(shared.find({'tenant_id':t}).sort('_id',1))==list(db[f'tasks_{t}'].find().sort('_id',1))
path=Path('evidence'); path.mkdir(exist_ok=True)
(path/'15.2-migration.json').write_text(json.dumps({'validation':validation,'benchmarks':rows,'analytics':analytics_shared(),'shared_index':shared.index_information(),'tenant_index':separate.index_information()},indent=2))
with (path/'15.2-benchmark.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for row in rows: print(row)
print('LAB 15.2 PASSED: 500 documents migrated, zero leakage, full equality and benchmarks')
