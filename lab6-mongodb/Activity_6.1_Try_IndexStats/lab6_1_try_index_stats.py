"""Lab 6.1 extension: run all queries repeatedly; inspect $indexStats accesses.ops."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from lab6_common import *

def main():
    cfg=load_config(Path(__file__).with_name('index_usage.json'))
    client,coll=connect('products_50k')
    try:
        assert coll.count_documents({})==50000, 'Run Activity 6.1 first'
        assert len(coll.index_information())>=6, 'Run Activity 6.1 first to create indexes'
        before={x['name']:x['accesses']['ops'] for x in coll.aggregate([{'$indexStats':{}}])}
        for repeat in range(cfg['query_repetitions']):
            for workload in workloads():execute_query(coll,workload)
        after=list(coll.aggregate([{'$indexStats':{}}]))
        stats=[]
        for item in after:
            name=item['name'];current=item['accesses']['ops'];delta=current-before.get(name,0)
            stats.append({'index':name,'total_ops':current,'delta_ops':delta})
        stats.sort(key=lambda x:x['delta_ops'],reverse=True)
        print('INDEX USAGE (delta since this run):')
        for x in stats:print(f"  {x['index']:20} usage delta={x['delta_ops']:3} lifetime ops={x['total_ops']}")
        used=[x for x in stats if x['delta_ops']>0 and x['index']!='_id_']
        assert used,'No named indexes were used; review query plans'
        print('Most frequently used this run:',used[0]['index'])
        write_json('lab6_1_index_stats.json',stats)
        print('ACTIVITY 6.1 TRY IT YOURSELF: PASS')
    finally:client.close()
if __name__=='__main__':main()
