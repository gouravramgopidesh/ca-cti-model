import csv, os, platform, statistics, time, unittest
from collections import Counter, defaultdict
from pathlib import Path
from common import *
from collect import collect
from databases import Mongo, Cassandra, Neo, summarize_spread
from communities import detect
from report import render_report

MODE=os.getenv('LAB_RUN_MODE','local')
if MODE not in ('local','published'): raise ValueError('Invalid LAB_RUN_MODE')
OUT=ROOT/'evidence'/MODE
OUT.mkdir(parents=True,exist_ok=True)

def timed(fn):
    t=time.perf_counter(); value=fn(); return value,(time.perf_counter()-t)*1000

def compare_rows(label, rows, expected_digest, expected_count):
    h=digest(rows)
    assert len(rows)==expected_count and len({r['id'] for r in rows})==expected_count and h==expected_digest, f'{label}: count or full-row digest mismatch'
    return {'count':len(rows),'sha256':h}

def verify(db, rows, source_partitions, type_partitions):
    m,c,n=db; expected=digest(rows); count=len(rows)
    result={
      'MongoDB full_threats':compare_rows('MongoDB',m.all_rows(),expected,count),
      'Cassandra threats_by_type':compare_rows('Cassandra type',c.all_rows(type_partitions),expected,count),
      'Cassandra threats_by_source':compare_rows('Cassandra source',c.all_rows(source_partitions,True),expected,count),
      'Neo4j Threat':compare_rows('Neo4j',n.all_rows(),expected,count),
    }
    groups=defaultdict(list)
    for r in rows: groups[r['from_source']].append(r)
    for src,group in groups.items(): assert m.recent(src)==order_history(group)[:50],f'Embedded recent cache mismatch: {src}'
    assert m.db.threats.count_documents({})==len(groups)
    graph_counts={}
    for rel in ('REPORTED','OBSERVES'):
        graph_counts[rel]=n.query(f'MATCH ()-[r:{rel}]->() RETURN count(r) AS n')[0]['n']
        assert graph_counts[rel]==count
    graph_counts['IN_NETWORK']=n.query('MATCH ()-[r:IN_NETWORK]->() RETURN count(r) AS n')[0]['n']
    assert graph_counts['IN_NETWORK']==len({r['indicator'] for r in rows})
    result['embedded_sources_verified']=len(groups); result['graph_relationships']=graph_counts
    return result

def partitions(rows):
    return sorted({(r['from_source'],r['day']) for r in rows}),sorted({(r['threat_type'],r['day']) for r in rows})

def hardware():
    def read(p):
        try: return Path(p).read_text().strip()
        except OSError: return None
    info=read('/proc/meminfo') or ''
    mem=next((int(x.split()[1])*1024 for x in info.splitlines() if x.startswith('MemTotal:')),None)
    model=next((x.split(':',1)[1].strip() for x in (read('/proc/cpuinfo') or '').splitlines() if x.startswith('model name')),None)
    return dict(platform=platform.platform(),python=platform.python_version(),logical_cpus=os.cpu_count(),cpu_model=model,visible_memory_bytes=mem,cgroup_memory_limit=read('/sys/fs/cgroup/memory.max'),cgroup_cpu_limit=read('/sys/fs/cgroup/cpu.max'),topology='Single-node MongoDB, Cassandra RF1/ONE, Neo4j Community; same Docker network; acknowledged writes, not equivalent production durability.')

def main():
    tests=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName("test_unit"))
    if not tests.wasSuccessful(): raise RuntimeError("Unit tests failed")
    rows,manifest=collect(); base=rows[:TOTAL]; hold=rows[TOTAL:]
    dump_json(OUT/'provenance.json',manifest)
    print(f'Frozen dataset: {len(base):,} baseline + {len(hold):,} held-out real observations; {len(manifest["publisher_counts"])} publishers',flush=True)
    print('Baseline source counts:',manifest['source_counts']); print('Snapshot-day counts:',manifest['day_counts'])
    db=[Mongo(),Cassandra(),Neo()]
    try:
        env=hardware(); env['versions']={'MongoDB':db[0].client.server_info()['version'],'Cassandra':db[1].s.execute('SELECT release_version FROM system.local').one().release_version,'Neo4j':db[2].query('CALL dbms.components() YIELD versions RETURN versions[0] AS version')[0]['version']}
        dump_json(OUT/'environment.json',env)
        for store in db:
            print('Resetting dedicated Lab18 data and loading',store.name,flush=True)
            store.reset(); start=time.perf_counter()
            for i,batch in enumerate(chunks(base,1000),1):
                store.insert(batch)
                if i%10==0: print(store.name,f'{i*1000:,}/{TOTAL:,}',flush=True)
            print(store.name,'load seconds:',round(time.perf_counter()-start,3),flush=True)
        sp,tp=partitions(base); ver=verify(db,base,sp,tp)
        dump_json(OUT/'baseline_integrity.json',ver)
        print('BASELINE VERIFIED: 100,000 full records match in all three databases and both Cassandra tables.',flush=True)
        source=Counter(r['from_source'] for r in base).most_common(1)[0][0]
        source_days=sorted({r['day'] for r in base if r['from_source']==source},reverse=True)
        type_days=Counter((r['threat_type'],r['day']) for r in base)
        # Prefer a reported service category so target is not just unknown, when it exists.
        reported=[p for p in type_days if p[0]=='reported_attack']
        kind,day=max(reported or list(type_days),key=lambda p:type_days[p])
        expected={'threat_history':order_history([r for r in base if r['from_source']==source])[:50],
          'target_and_spread':summarize_spread(r for r in base if r['threat_type']==kind and r['day']==day),
          'daily_volume':dict(Counter(r['day'] for r in base))}
        specs={'threat_history':lambda s:s.history(source,source_days),'target_and_spread':lambda s:s.spread(kind,day),'daily_volume':lambda s:s.daily(tp)}
        raw=[]; summary=[]
        for op,func in specs.items():
            for store in db: assert func(store)==expected[op],f'{op} warmup mismatch: {store.name}'
            for i in range(RUNS):
                for store in db[i%3:]+db[:i%3]:
                    result,ms=timed(lambda:func(store))
                    assert result==expected[op],f'{op} mismatch: {store.name}'
                    raw.append(dict(operation=op,database=store.name,run=i+1,latency_ms=ms,records_per_second=None))
            print(op,'10 runs per database; all results equal',flush=True)
        # Compare bounded embedded recent history separately (not used in comparative table).
        extra=[]
        for i in range(RUNS):
            result,ms=timed(lambda:db[0].recent(source)); assert result==expected['threat_history']; extra.append(ms)
        communities=detect(db[2],db[0]); dump_json(OUT/'communities.json',communities)
        print('Graph:',communities['projection_nodes'],'projected observations;',len(communities['flagged_communities']),'candidate communities;',len(communities['source_suspicious_edges']),'source overlap edges',flush=True)
        for i,batch in enumerate(chunks(hold,INSERT_BATCH)):
            assert len(batch)==INSERT_BATCH
            for store in db[i%3:]+db[:i%3]:
                _,ms=timed(lambda:store.insert(batch))
                raw.append(dict(operation='real_time_insert',database=store.name,run=i+1,latency_ms=ms,records_per_second=INSERT_BATCH/(ms/1000)))
            print('Real-time insert batch',i+1,'of',RUNS,'acknowledged by all databases',flush=True)
        sp,tp=partitions(rows); final=verify(db,rows,sp,tp); dump_json(OUT/'final_integrity.json',final)
        print('FINAL VERIFIED: 101,000 records in all stores including 1,000 held-out new observations.',flush=True)
        for op in (*specs,'real_time_insert'):
            for store in db:
                v=[r for r in raw if r['operation']==op and r['database']==store.name]
                assert len(v)==RUNS
                summary.append(dict(operation=op,database=store.name,runs=RUNS,median_latency_ms=statistics.median(r['latency_ms'] for r in v),median_records_per_second=statistics.median(r['records_per_second'] for r in v) if op=='real_time_insert' else None))
        with (OUT/'benchmark_raw.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(raw[0])); w.writeheader(); w.writerows(raw)
        with (OUT/'benchmark.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(summary[0])); w.writeheader(); w.writerows(summary)
        for x in summary: print(x,flush=True)
        data=dict(run_mode=MODE,completed_utc=now().isoformat(),manifest=manifest,environment=env,benchmark=summary,query_parameters=dict(history_source=source,history_days=source_days,spread_type=kind,spread_day=day,spread_result=expected['target_and_spread'],daily_result=expected['daily_volume'],embedded_median_ms=statistics.median(extra)),baseline_integrity=ver,final_integrity=final,graph=communities,logical_bytes_per_observation=sum(len(row_bytes(r)) for r in base)/len(base))
        dump_json(OUT/'results.json',data)
        print('LAB 18.1 PASSED: genuine feed dataset, equivalent results, 10 runs, insert throughput and graph cross-reference',flush=True)
        report=render_report(data,OUT,ROOT/'reports'/f'Lab18-{MODE}-comparative-report.pdf')
        print('LAB 18.2 PASSED: comparative report generated:',report,flush=True)
        print('LAB 18 PASSED: 18.1 and 18.2',flush=True)
    finally:
        for store in db: store.close()

if __name__=='__main__': main()
