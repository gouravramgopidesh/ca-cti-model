from uuid import uuid4
from common import connect, save, DB, HOSTS, direct, wait_for
from bank import seed, snapshot, transfer
from transactions import InsufficientFunds, InjectedFailure
from pymongo import ReadPreference

with connect() as client:
    run=uuid4().hex
    seed(client,run)
    initial=snapshot(client,run)
    operation=transfer(client,run,'A','B',200)
    committed=snapshot(client,run)
    assert committed['A']['balance']==800 and committed['B']['balance']==700
    assert sum(v['balance'] for v in initial.values())==sum(v['balance'] for v in committed.values())
    for label,amount,inject,expected in [('insufficient',10000,False,InsufficientFunds),('after-debit',50,True,InjectedFailure)]:
        try: transfer(client,run,'A','B',amount,inject_failure=inject)
        except expected as e: print(label,'rollback:',str(e))
        else: raise AssertionError('Expected failure did not occur')
        assert snapshot(client,run)==committed
        assert client[DB].transfer_history.count_documents({'run':run})==1
    def replicated(host):
        with direct(host) as node:
            coll=node[DB].get_collection('transfer_history',read_preference=ReadPreference.SECONDARY_PREFERRED)
            return bool(coll.find_one({'_id':operation}))
    replicas={h:wait_for(lambda:replicated(h),60) for h in HOSTS}
    result={'run':run,'initial':initial,'committed':committed,'after_failed_transfers':snapshot(client,run),'history_count':1,'rollback_insufficient':True,'rollback_after_debit':True,'write_concern':{'w':'majority','j':True},'replicated_history':replicas,'passed':True}
    print(result); save('10.1-bank-transfer.json',result)
