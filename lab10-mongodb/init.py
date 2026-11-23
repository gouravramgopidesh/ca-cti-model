from common import *
from pymongo.errors import OperationFailure
with direct('mongo1') as c:
    wait_for(lambda: c.admin.command('ping').get('ok'))
    try:
        c.admin.command('replSetInitiate', {'_id':'rs0','members':[{'_id':i,'host':h+':27017'} for i,h in enumerate(HOSTS)]})
    except OperationFailure as e:
        if e.code != 23: raise
s=wait_for(healthy,180)
print('Replica set ready:', [(m['name'],m['stateStr'],m['health']) for m in s['members']])
save('replica-status.json',s)
