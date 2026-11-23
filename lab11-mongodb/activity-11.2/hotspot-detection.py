from datetime import datetime, timedelta, timezone
from bson import ObjectId, MinKey
from common import client, DB, save, EVIDENCE
import csv, random, time

def explain(db, name, query):
    plan = db.command('explain', {'find': name, 'filter': query}, verbosity='executionStats')
    shards = plan['queryPlanner']['winningPlan'].get('shards', [])
    if not shards:
        raise RuntimeError('No shard routing information in explain')
    return {'targeted_shards': [s['shardName'] for s in shards],
            'nReturned': plan['executionStats']['nReturned'], 'explain': plan}

with client() as c:
    assert c.admin.command('hello')['msg'] == 'isdbgrid'
    db = c[DB]
    # Repeatable isolated experiment: disable balancer and explicitly place ranges.
    previous = c.admin.command('balancerStatus')['mode']
    c.admin.command('balancerStop')
    try:
        for name in ['hotspot_data','even_data']:
            db[name].drop()
            db.create_collection(name)
        start = datetime(2025,1,1,tzinfo=timezone.utc)
        split = start + timedelta(seconds=500)
        hot = db.hotspot_data; even = db.even_data
        hot.create_index('ts'); even.create_index([('user_id','hashed')])
        c.admin.command('shardCollection', hot.full_name, key={'ts':1})
        c.admin.command('split', hot.full_name, middle={'ts':split})
        # Put old range on A and newest range on B, even if DB primary differs.
        for point, target in [(start,'shardA'),(split,'shardB')]:
            try:
                c.admin.command('moveChunk',hot.full_name,find={'ts':point},to=target,_waitForDelete=True)
            except Exception as exc:
                # Some versions reject a move to the current owner; verify owner below.
                meta=c.config.collections.find_one({'_id':hot.full_name})
                chunks=list(c.config.chunks.find({'uuid':meta['uuid']}))
                if not any(ch['shard']==target and (isinstance(ch['min']['ts'],MinKey) if point==start else ch['min']['ts']==split.replace(tzinfo=None)) for ch in chunks):
                    raise exc
        c.admin.command('shardCollection', even.full_name,key={'user_id':'hashed'},numInitialChunks=4)
        rng=random.Random(11)
        ids=[ObjectId(rng.randbytes(12)) for _ in range(10000)]
        for col in [hot,even]:
            t=time.perf_counter()
            for i in range(0,10000,500):
                col.insert_many([{'_id':j,'ts':start+timedelta(seconds=j),'user_id':ids[j],'payload':'x'*256} for j in range(i,i+500)])
            print(col.name, 'inserted',col.count_documents({}), 'seconds',round(time.perf_counter()-t,3))
        rows=[]; plans={}; raw={}
        lower,upper=sorted(ids)[1000],sorted(ids)[2000]
        # Same timestamp predicate on both collections; hashed-key range also tested explicitly.
        date_query={'ts':{'$gte':start+timedelta(seconds=1000),'$lt':start+timedelta(seconds=2000)}}
        for col in [hot,even]:
            raw[col.name]=db.command('collStats',col.name)
            per=list(col.aggregate([{'$collStats':{'storageStats':{},'count':{}}}]))
            for item in per:
                stats=item['storageStats']; rows.append({'collection':col.name,'shard':item['shard'],'count':item['count'],'data_bytes':stats['size'],'storage_bytes':stats['storageSize']})
            assert col.count_documents({})==10000
            plans[col.name+'_date_range']=explain(db,col.name,date_query)
        plans['even_hashed_range']=explain(db,even.name,{'user_id':{'$gte':lower,'$lt':upper}})
        plans['even_hashed_equality']=explain(db,even.name,{'user_id':ids[0]})
        save('11.2-distribution.json',rows); save('11.2-collstats.json',raw); save('11.2-explain.json',plans)
        with (EVIDENCE/'11.2-distribution.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        for row in rows: print(row)
        for name,plan in plans.items(): print(name,plan['targeted_shards'],'returned',plan['nReturned'])
        hot_counts={r['shard']:r['count'] for r in rows if r['collection']=='hotspot_data'}
        even_counts={r['shard']:r['count'] for r in rows if r['collection']=='even_data'}
        assert hot_counts=={'shardA':500,'shardB':9500},hot_counts
        assert sum(even_counts.values())==10000 and len(even_counts)==2 and min(even_counts.values())>4000,even_counts
        assert len(plans['hotspot_data_date_range']['targeted_shards'])==1
        assert len(plans['even_data_date_range']['targeted_shards'])==2
        assert len(plans['even_hashed_range']['targeted_shards'])==2
        assert len(plans['even_hashed_equality']['targeted_shards'])==1
        report='# Lab 11.2 measured results\n\n| Collection | Shard | Documents | Data bytes | Storage bytes |\n|---|---|---:|---:|---:|\n'
        for r in rows: report+='| {collection} | {shard} | {count} | {data_bytes} | {storage_bytes} |\n'.format(**r)
        report+='\nRouting results:\n'
        for name,plan in plans.items(): report+=f'- {name}: {plan["targeted_shards"]}; {plan["nReturned"]} documents returned.\n'
        report+='\nThe controlled range placement models a newest-range hotspot; it is not evidence of automatic balancer behavior. Hashing spreads distinct values, but ranges on the hashed field scatter across shards. Ranged keys remain appropriate for selective range scans or time locality when write skew is acceptable.\n'
        (EVIDENCE/'11.2-report.md').write_text(report,encoding='utf-8')
        print('11.2 passed: hotspot, balanced hashing, and query routing verified.')
    finally:
        if previous!='off': c.admin.command('balancerStart')
