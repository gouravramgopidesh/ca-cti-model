import os
from pymongo.errors import OperationFailure
from common import client, HOSTS, wait, healthy, save
with client(HOSTS[0], direct=True) as c:
    wait(lambda: c.admin.command('ping'))
    try:
        c.admin.command('replSetGetConfig')
    except OperationFailure as e:
        if e.code != 94:
            raise
        print(c.admin.command('replSetInitiate', {'_id':'rs0','members':[
            {'_id':i,'host':h} for i,h in enumerate(HOSTS)]}))
with client() as c:
    s = wait(lambda: healthy(c))
    if os.getenv('MONITOR_PASSWORD'):
        if not c.admin.command('usersInfo','labmonitor')['users']:
            c.admin.command('createUser','labmonitor',pwd=os.environ['MONITOR_PASSWORD'],roles=[{'role':'clusterMonitor','db':'admin'},{'role':'read','db':'local'}])
    save('13.1-replica-status.json', {'passed':True,'members':s})
