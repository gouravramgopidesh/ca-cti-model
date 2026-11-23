import json, time, uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests
from backend.main import db, LIMIT, now
BASE='http://localhost:8000'
rows=[]
def check(label,method,path,expected,token=None,**kwargs):
    r=requests.request(method,BASE+path,headers={'Authorization':'Bearer '+token} if token else {},timeout=20,**kwargs)
    assert r.status_code==expected,(label,r.status_code,r.text)
    rows.append({'test':label,'status':r.status_code,'passed':True}); print(label,r.status_code,'PASS'); return r

def login(name): return check('login '+name,'POST','/token',200,data={'username':name,'password':'Lab15Demo!'}).json()['access_token']
# Reset only demo rate counters for repeatable coursework, not tasks.
db.rate_limits.delete_many({'tenant_id':{'$in':['tenant_1','tenant_2','tenant_3']}})
a,b,admin,other,rate=[login(x) for x in ('tenant_1_user','tenant_1_user2','tenant_1_admin','tenant_2_admin','tenant_3_user')]
marker='lab15-test-'+uuid.uuid4().hex
payload={'title':marker,'description':'test','priority':'high'}
check('no token','GET','/tasks/',401)
check('invalid JWT','GET','/tasks/',401,'bad.token.value')
check('wrong password','POST','/token',401,data={'username':'tenant_1_user','password':'wrong'})
x=check('create own','POST','/tasks/',201,a,json=payload).json(); id=x['id']; path='/tasks/'+id
try:
    assert x['tenant_id']=='tenant_1'
    check('own read','GET',path,200,a)
    assert id in [t['id'] for t in check('own list','GET','/tasks/',200,a).json()]
    assert id not in [t['id'] for t in check('other owner list','GET','/tasks/',200,b).json()]
    assert id in [t['id'] for t in check('admin list','GET','/tasks/',200,admin).json()]
    assert id not in [t['id'] for t in check('other tenant list','GET','/tasks/?tenant_id=tenant_1',200,other).json()]
    for name,t in [('same tenant regular',b),('different tenant admin',other)]:
        for method in ('GET','PATCH','DELETE'):
            check(name+' '+method,method,path,404,t,**({'json':{'status':'done'}} if method=='PATCH' else {}))
    check('tenant spoof rejected','POST','/tasks/',422,a,json={**payload,'tenant_id':'tenant_2'})
    check('owner spoof rejected','PATCH',path,422,a,json={'owner_id':'fake'})
    assert check('owner update','PATCH',path,200,a,json={'status':'in_progress'}).json()['status']=='in_progress'
    assert check('admin update','PATCH',path,200,admin,json={'status':'done'}).json()['status']=='done'
    check('admin delete','DELETE',path,200,admin)
    check('deleted absent','GET',path,404,a)
    y=check('create for own deletion','POST','/tasks/',201,a,json=payload).json()
    check('owner delete','DELETE','/tasks/'+y['id'],200,a)
finally:
    db.tasks.delete_many({'tenant_id':'tenant_1','title':marker})
# Avoid crossing fixed-window boundary in concurrency test.
if time.time()%60>45: time.sleep(61-time.time()%60)
def hit(_): return requests.get(BASE+'/me',headers={'Authorization':'Bearer '+rate},timeout=20).status_code
with ThreadPoolExecutor(max_workers=8) as pool: codes=list(pool.map(hit,range(LIMIT+5)))
assert codes.count(200)==LIMIT and codes.count(429)==5,codes
u=db.users.find_one({'username':'tenant_3_user'}); counter=db.rate_limits.find_one({'tenant_id':'tenant_3','user_id':str(u['_id'])},sort=[('timestamp',-1)])
assert counter['count']==LIMIT+5
idx=db.rate_limits.index_information(); assert any(i.get('expireAfterSeconds')==0 and i['key']==[('timestamp',1)] for i in idx.values())
assert any(i['key']==[('tenant_id',1),('created_at',-1)] for i in db.tasks.index_information().values())
rows.append({'test':'concurrent atomic rate limit','allowed':codes.count(200),'blocked':codes.count(429),'counter':counter['count'],'passed':True})
# Demonstrate real TTL expiry using a dedicated already-expired counter.
from datetime import timedelta
key='ttl-test-'+uuid.uuid4().hex
db.rate_limits.insert_one({'_id':key,'timestamp':now()-timedelta(minutes=5),'count':1})
start=time.monotonic()
while db.rate_limits.find_one({'_id':key}) and time.monotonic()-start<150: time.sleep(2)
assert not db.rate_limits.find_one({'_id':key}),'TTL monitor did not remove expired counter within 150s'
rows.append({'test':'TTL automatic deletion','seconds':time.monotonic()-start,'passed':True})
Path('evidence').mkdir(exist_ok=True); Path('evidence/15.1-api.json').write_text(json.dumps(rows,indent=2))
print('LAB 15.1 PASSED: CRUD, JWT, tenant isolation, RBAC, atomic rate limit and TTL')
