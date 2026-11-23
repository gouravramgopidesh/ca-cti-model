"""Lab 6.1: 50,000 documents, five pre/post-index query explains."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from lab6_common import *

def main():
    cfg=load_config(Path(__file__).with_name('workload_50000.json'))
    client,coll=connect('products_50k')
    try:
        print('Creating',cfg['document_count'],'generated products in',DATABASE)
        reset_workload(coll,cfg['document_count'])
        print('Documents:',coll.count_documents({}))
        assert coll.index_information().keys()=={'_id_'} or len(coll.index_information())==1
        print('\nBEFORE INDEXES (COLLSCAN expected for these queries)')
        before=[explain(coll,q) for q in workloads()]
        for row in before:print_explain(row)
        assert all('COLLSCAN' in x['stages'] for x in before)
        create_indexes(coll)
        print('\nAFTER FIVE INDEXES')
        after=[explain(coll,q) for q in workloads()]
        for row in after:print_explain(row)
        assert all('IXSCAN' in x['stages'] for x in after), 'An expected index was not used; inspect the explain JSON'
        print('\nDOCS EXAMINED BEFORE -> AFTER')
        for b,a in zip(before,after):
            print(f"  {b['query']}: {b['totalDocsExamined']} -> {a['totalDocsExamined']}")
        write_json('lab6_1_explain_comparison.json',{'docs':coll.count_documents({}),'before':before,'after':after,'indexes':coll.index_information()})
        print('ACTIVITY 6.1: PASS')
    finally:client.close()
if __name__=='__main__':main()
