import sys, os
from common import client, wait, healthy, verify_all, save
from pymongo.write_concern import WriteConcern
mode=sys.argv[1]
record=os.environ['LAB13_RECORD']
with client() as c:
    members=wait(lambda:healthy(c))
    if mode=='seed':
        c.lab13.records.with_options(write_concern=WriteConcern('majority',j=True)).insert_one({'_id':record,'title':'Persistent Kubernetes CTI record'})
    assert c.lab13.records.find_one({'_id':record})
    result=verify_all(record)
    assert all(result.values())
    save('unused.json',{'passed':True,'mode':mode,'record':record,'members':members,'verified_on_all_members':result})
