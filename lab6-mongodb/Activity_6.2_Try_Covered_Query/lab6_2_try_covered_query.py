"""Lab 6.2 extension: prove a covered query uses IXSCAN without FETCH."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from lab6_common import *

def walk_stages(v):
    found=[]
    if isinstance(v,dict):
        if 'stage' in v:found.append(v['stage'])
        for x in v.values():found.extend(walk_stages(x))
    elif isinstance(v,list):
        for x in v:found.extend(walk_stages(x))
    return found

def main():
    cfg=load_config(Path(__file__).with_name('covered_query.json'))
    client,coll=connect('products_index_benchmark')
    try:
        assert coll.count_documents({})==20000,'Run Activity 6.2 first'
        assert 'ix_category_price' in coll.index_information(),'Missing category-price index'
        filt={'category':cfg['category']}
        projection={'_id':0,'category':1,'price':1}
        cmd={'find':coll.name,'filter':filt,'projection':projection,'limit':100}
        exp=coll.database.command({'explain':cmd,'verbosity':'executionStats'})
        stages=walk_stages(exp['queryPlanner']['winningPlan'])
        stats=exp['executionStats']
        print('Covered query: category filter; only category and price returned; _id excluded')
        print('Explain plan stages:',stages)
        print('Docs examined:',stats['totalDocsExamined'],'Keys examined:',stats['totalKeysExamined'])
        assert 'IXSCAN' in stages,'Index scan not found'
        assert 'FETCH' not in stages,'Covered query should not need FETCH'
        assert stats['totalDocsExamined']==0,'Covered query should examine zero documents'
        rows=list(coll.find(filt,projection).limit(3))
        print('Sample documents:',rows)
        assert rows and all(set(d)<= {'category','price'} for d in rows)
        write_json('lab6_2_covered_query_evidence.json',{
            'plan_stages':stages,'totalDocsExamined':stats['totalDocsExamined'],
            'totalKeysExamined':stats['totalKeysExamined'],'samples':rows})
        print('ACTIVITY 6.2 TRY IT YOURSELF: PASS')
    finally:client.close()
if __name__=='__main__':main()
