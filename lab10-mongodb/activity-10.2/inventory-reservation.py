import csv, time, threading
from concurrent.futures import ThreadPoolExecutor
from common import connect, save, EVIDENCE
from inventory import seed_inventory, reserve, state
from transactions import OutOfStock, InjectedFailure
from pymongo.errors import PyMongoError


def workload(client,workers,requests,stock,retries=5,transactional=True,contend=False):
    run=seed_inventory(client,stock)
    barrier=threading.Barrier(workers) if contend else None
    def job(i):
        events=[]; status='success'; error=None
        try: reserve(client,run,f'C{i}',retries=retries,events=events,barrier=barrier,transactional=transactional)
        except OutOfStock: status='out_of_stock'
        except PyMongoError as e:
            if not e.has_error_label('TransientTransactionError'): raise
            status='write_conflict_exhausted'; error=str(e)
        return {'status':status,'retry_count':sum(x['kind']=='transaction-retry' for x in events),'retry_events':events,'error':error}
    start=time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool: outcomes=list(pool.map(job,range(requests)))
    elapsed=time.perf_counter()-start
    summary=state(client,run,stock)
    successes=sum(x['status']=='success' for x in outcomes)
    assert summary['consistent'] and summary['orders']==successes
    result={'run':run,'workers':workers,'requests':requests,'transactional':transactional,'retries_allowed':retries,'successes':successes,'out_of_stock':sum(x['status']=='out_of_stock' for x in outcomes),'conflict_failures':sum(x['status']=='write_conflict_exhausted' for x in outcomes),'retries':sum(x['retry_count'] for x in outcomes),'elapsed_s':elapsed,'successful_per_second':successes/elapsed,**summary,'outcomes':outcomes}
    print({k:v for k,v in result.items() if k!='outcomes'}); return result


def chart(rows):
    # Dependency-free SVG plot of measured throughput, not predicted values.
    width,height=800,430; left,top,right,bottom=80,55,760,355
    ymax=max(1,max(r['successful_per_second'] for r in rows))*1.12
    def x(i): return left+i*(right-left)/3
    def y(v): return bottom-v/ymax*(bottom-top)
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">','<rect width="100%" height="100%" fill="white"/>','<g font-family="Arial" font-size="13" fill="#172b3a">','<text x="80" y="28" font-size="20" font-weight="bold">Measured reservation throughput</text>']
    for i in range(6):
        v=ymax*i/5; yy=y(v); parts += [f'<path d="M{left} {yy}H{right}" stroke="#dce3e8"/>',f'<text x="70" y="{yy+4}" text-anchor="end">{v:.0f}</text>']
    for i,w in enumerate([1,4,8,16]): parts.append(f'<text x="{x(i)}" y="375" text-anchor="middle">{w}</text>')
    for mode,color,label,ly in [(True,'#007c83','Transactions',402),(False,'#b65c20','Non-transactional',420)]:
        vals=[r['successful_per_second'] for r in rows if r['transactional']==mode]
        parts.append(f'<polyline fill="none" stroke="{color}" stroke-width="3" points="'+ ' '.join(f'{x(i)},{y(v)}' for i,v in enumerate(vals))+'"/>')
        for i,v in enumerate(vals): parts.append(f'<circle cx="{x(i)}" cy="{y(v)}" r="4" fill="{color}"/>')
        parts.append(f'<text x="100" y="{ly}" fill="{color}">{label}</text>')
    parts += ['<text x="420" y="395" text-anchor="middle">Concurrent threads</text>','<text transform="translate(18 205) rotate(-90)" text-anchor="middle">Successful reservations / second</text>','</g></svg>']
    (EVIDENCE/'10.2-throughput.svg').write_text('\n'.join(parts),encoding='utf-8')

with connect() as client:
    print('Contention: eight customers, five units, no retry')
    no_retry=workload(client,8,8,5,retries=0,contend=True)
    print('Contention: eight customers, five units, retry enabled')
    retry=workload(client,8,8,5,retries=5,contend=True)
    assert retry['successes']==5 and retry['out_of_stock']==3 and retry['remaining_stock']==0
    assert retry['retries']>0
    rows=[]
    for mode in [True,False]:
        for workers in [1,4,8,16]:
            print('Throughput:', 'transactional' if mode else 'non-transactional',workers,'threads')
            rows.append(workload(client,workers,80,80,transactional=mode))
    failure=[]
    for mode in [True,False]:
        run=seed_inventory(client,5)
        try: reserve(client,run,'failure-demo',transactional=mode,inject_failure=True)
        except InjectedFailure: pass
        else: raise AssertionError('Expected injected failure')
        s=state(client,run,5); s['transactional']=mode; failure.append(s); print('Failure test:',s)
        assert s['consistent']==mode and s['orders']==0
    save('10.2-inventory.json',{'no_retry':no_retry,'with_retry':retry,'throughput':rows,'failure_comparison':failure,'passed':True})
    fields=['transactional','workers','requests','successes','out_of_stock','conflict_failures','retries','elapsed_s','successful_per_second','remaining_stock','consistent']
    with (EVIDENCE/'10.2-throughput.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); writer.writeheader(); writer.writerows(rows)
    chart(rows)
    print('Inventory tests passed. Actual throughput CSV and SVG chart saved.')
