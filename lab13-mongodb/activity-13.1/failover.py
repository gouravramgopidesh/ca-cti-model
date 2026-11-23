import time, threading, uuid
from datetime import datetime, timezone
from pymongo import MongoClient, monitoring
from pymongo.errors import PyMongoError, OperationFailure
from pymongo.write_concern import WriteConcern
from common import client, wait, healthy, verify_all, save, HOSTS
class Reads(monitoring.CommandListener):
    def __init__(self): self.events=[]
    def started(self,e): pass
    def failed(self,e): pass
    def succeeded(self,e):
        if e.command_name=='find': self.events.append(str(e.connection_id))
listener=Reads()
with client(event_listeners=[listener]) as c:
    before=wait(lambda:healthy(c))
    doc_id=uuid.uuid4().hex
    c.lab13.records.with_options(write_concern=WriteConcern('majority',j=True)).insert_one({'_id':doc_id,'title':'CTI replica verification'})
    replicated=verify_all(doc_id)
    old=next(m['name'] for m in before if m['state']=='PRIMARY')
    denied=False
    with MongoClient(old,directConnection=True,serverSelectionTimeoutMS=3000) as anon:
        try: anon.lab13.records.find_one()
        except OperationFailure as e:
            if e.code!=13: raise
            denied=True
    assert denied
    stop=threading.Event(); samples=[]
    def observe():
        while not stop.is_set():
            try:
                n=len(listener.events)
                found=c.lab13.records.find_one({'_id':doc_id})
                member=listener.events[-1] if len(listener.events)>n else None
                row={'utc':datetime.now(timezone.utc).isoformat(),'ok':bool(found),'member':member}
            except PyMongoError as e:
                row={'utc':datetime.now(timezone.utc).isoformat(),'ok':False,'error':type(e).__name__}
            samples.append(row); print(row,flush=True); stop.wait(0.5)
    t=threading.Thread(target=observe); t.start()
    try:
        time.sleep(2)
        with client(old,direct=True) as direct:
            try: print('stepDown:',direct.admin.command('replSetStepDown',30,secondaryCatchUpPeriodSecs=10))
            except PyMongoError as e: print('stepDown response:',type(e).__name__,str(e))
        def changed():
            s=healthy(c)
            return s if s and any(m['state']=='PRIMARY' and m['name']!=old for m in s) else None
        after=wait(changed,90)
        new=next(m['name'] for m in after if m['state']=='PRIMARY')
        time.sleep(4)
    finally:
        stop.set(); t.join()
    assert old!=new and any(r['ok'] and new.split(':')[0] in str(r.get('member')) for r in samples)
    save('13.1-failover.json',{'passed':True,'before':before,'after':after,'old_primary':old,'new_primary':new,'replicated':replicated,'anonymous_denied':denied,'reads':samples})
