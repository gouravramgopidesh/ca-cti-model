import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import *
from concurrent.futures import ThreadPoolExecutor

def inspect(host):
    try:
        with direct(host) as c:
            h=c.admin.command('hello')
            s=c.admin.command('replSetGetStatus')
            return {'host':host,'primary':h.get('isWritablePrimary',False),'state':next((m['stateStr'] for m in s['members'] if m.get('self')),None),'members':[{'name':m['name'],'state':m['stateStr'],'health':m['health']} for m in s['members']]}
    except PyMongoError as e: return {'host':host,'primary':False,'error':str(e)}
with (EVIDENCE/'9.2-observer.jsonl').open('a',encoding='utf-8',buffering=1) as f, ThreadPoolExecutor(max_workers=3) as pool:
    while True:
        start=time.monotonic()
        nodes=list(pool.map(inspect,HOSTS)); row={'utc':utc(),'primary':[n['host'] for n in nodes if n['primary']], 'nodes':nodes}
        f.write(json.dumps(row)+'\n'); print(json.dumps(row),flush=True)
        time.sleep(max(0,1-(time.monotonic()-start)))
