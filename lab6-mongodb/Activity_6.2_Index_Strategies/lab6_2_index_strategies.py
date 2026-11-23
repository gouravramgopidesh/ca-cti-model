"""Lab 6.2: benchmark insert write cost, then compare five reads with 5 vs 1 index."""
from pathlib import Path
import sys,time
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from lab6_common import *

def main():
    cfg=load_config(Path(__file__).with_name('index_strategy.json'))
    client,coll=connect('products_index_benchmark')
    try:
        coll.drop()
        count=cfg['batch_size']
        start=time.perf_counter()
        insert_batches(coll,make_documents(count,42,start=0))
        no_index=time.perf_counter()-start
        create_indexes(coll)
        start=time.perf_counter()
        insert_batches(coll,make_documents(count,43,start=count))
        five_indexes=time.perf_counter()-start
        slowdown=(five_indexes-no_index)/no_index*100 if no_index else 0.0
        print(f'Insert {count:,} records, only _id: {no_index:.3f}s')
        print(f'Insert {count:,} records, five indexes: {five_indexes:.3f}s')
        print(f'Write slowdown: {slowdown:+.2f}% (measurements vary by machine)')
        assert coll.count_documents({})==2*count
        print('\nQUERIES WITH FIVE INDEXES')
        five=[explain(coll,q) for q in workloads()]
        for r in five:print_explain(r)
        for item in list(coll.index_information()):
            if item not in ('_id_','ix_category_price'):coll.drop_index(item)
        assert len(coll.index_information())==2
        print('\nQUERIES WITH ONLY MOST CRITICAL INDEX: ix_category_price')
        one=[explain(coll,q) for q in workloads()]
        for r in one:print_explain(r)
        print('\nANALYSIS: Maintaining five secondary indexes generally adds write overhead,')
        print('but improves more read patterns. A single compound index saves write')
        print('maintenance/storage and supports category+price queries; other queries')
        print('may scan more documents. Use workload-specific measurements to decide.')
        write_json('lab6_2_index_strategy_comparison.json',{
            'insert_without_indexes_seconds':no_index,
            'insert_with_five_indexes_seconds':five_indexes,
            'slowdown_percent':slowdown,
            'five_index_query_results':five,'one_index_query_results':one,
            'retained_index':'ix_category_price','count':coll.count_documents({})})
        print('ACTIVITY 6.2: PASS')
    finally:client.close()
if __name__=='__main__':main()
