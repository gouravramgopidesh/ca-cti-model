from uuid import uuid4
from common import connect, save, DB
from bank import seed, snapshot, transfer
from pymongo.write_concern import WriteConcern

with connect() as client, connect() as competitor:
    run=uuid4().hex; seed(client,run); events=[]
    def conflict(attempt):
        if attempt==0:
            # Commit a real competing write after the transaction's snapshot read.
            # The first transaction then tries to modify a newer version of the same document.
            coll=competitor[DB].accounts.with_options(write_concern=WriteConcern(w='majority',j=True))
            result=coll.update_one({'run':run,'account_id':'A'},{'$inc':{'version':1}})
            assert result.modified_count==1
            print('Competing write committed; forcing a snapshot write conflict')
    operation=transfer(client,run,'A','B',100,events=events,hook=conflict)
    state=snapshot(client,run)
    assert state['A']['balance']==900 and state['B']['balance']==600
    assert client[DB].transfer_history.count_documents({'run':run})==1
    assert any(e['kind']=='transaction-retry' for e in events), 'No transient retry was observed'
    for e in events: print(e)
    result={'run':run,'operation':operation,'retry_events':events,'final':state,'history_count':1,'passed':True}
    print(result); save('10.1-retry.json',result)
