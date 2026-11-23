import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import *
from pymongo.write_concern import WriteConcern
from uuid import uuid4
import csv

def benchmark(journal_values, filename):
    wait_for(healthy)
    rows=[]
    with connect() as c:
        for j in journal_values:
            for label,w in [('w:1',1),('w:majority','majority'),('w:all',3)]:
                run=uuid4().hex
                opts={'w':w,'wtimeout':5000}
                if j is not None: opts['j']=j
                coll=c[DB].get_collection('write_benchmark',write_concern=WriteConcern(**opts))
                # Warm up outside the timed loop; no index creation in measurement.
                coll.insert_one({'_id':run+'-warmup','kind':'warmup'})
                start=time.perf_counter(); success=0; errors=[]
                for i in range(1000):
                    try:
                        coll.insert_one({'_id':f'{run}-{i}','sequence':i,'payload':'x'*100})
                        success+=1
                    except PyMongoError as e:
                        errors.append(str(e)); break
                seconds=time.perf_counter()-start
                row=dict(utc=utc(),run=run,concern=label,w=w,j=j,attempted=success+len(errors),successful=success,total_seconds=seconds,average_ms=seconds*1000/success if success==1000 else None,errors=errors)
                rows.append(row); save(filename+'.json',rows)
                print(f'{label:12} j={str(j):5} {success:4}/1000 total={seconds:8.3f}s avg={row["average_ms"]} ms',flush=True)
                if errors: raise RuntimeError(errors[0])
    with (EVIDENCE/(filename+'.csv')).open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    return rows
if __name__=='__main__':
    benchmark([None],'9.1-write-concern')
