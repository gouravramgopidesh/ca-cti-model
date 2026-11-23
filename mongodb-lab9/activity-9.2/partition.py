import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import *
from pymongo.write_concern import WriteConcern
from uuid import uuid4

def event(kind, **values):
    row={'utc':utc(),'event':kind,**values}
    with (EVIDENCE/'9.2-partition.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(row)+'\n')
    print(json.dumps(row),flush=True)

def probe(host, phase, marker, concerns):
    with direct(host) as c:
        for w in concerns:
            w=1 if w=='1' else w
            start=time.perf_counter(); doc_id=marker+'-'+str(w)
            try:
                c[DB].get_collection('partition_test',write_concern=WriteConcern(w=w,wtimeout=3000)).insert_one({'_id':doc_id,'phase':phase})
                event('write',phase=phase,w=w,doc_id=doc_id,ok=True,ms=(time.perf_counter()-start)*1000)
            except PyMongoError as e:
                event('write',phase=phase,w=w,doc_id=doc_id,ok=False,error=type(e).__name__,detail=str(e),ms=(time.perf_counter()-start)*1000)

action=sys.argv[1]
if action=='primary': print(primary())
elif action=='ready':
    s=wait_for(healthy,180); event('healthy',primary=next(m['name'] for m in s['members'] if m['stateStr']=='PRIMARY'))
elif action=='event': event(sys.argv[2],detail=' '.join(sys.argv[3:]))
elif action=='probe': probe(sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5:])
elif action=='no-primary':
    host=sys.argv[2]
    def stepped_down():
        with direct(host) as c: return not c.admin.command('hello').get('isWritablePrimary',False)
    wait_for(stepped_down,90); event('primary-stepdown-observed',host=host)
elif action=='catchup':
    host,marker=sys.argv[2:4]
    def found():
        with direct(host) as c: return c[DB]['partition_test'].find_one({'_id':marker+'-majority'})
    wait_for(found,120); event('catch-up-verified',host=host,doc_id=marker+'-majority')
else: raise ValueError(action)
