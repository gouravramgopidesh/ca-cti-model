from common import client, wait_for, save
from pymongo import MongoClient
from pymongo.errors import OperationFailure

def init(host, name, config=False):
    with MongoClient(host, directConnection=True, serverSelectionTimeoutMS=3000) as c:
        wait_for(lambda: c.admin.command('ping'))
        cfg = {'_id': name, 'members': [{'_id': 0, 'host': host}]}
        if config:
            cfg['configsvr'] = True
        try:
            c.admin.command('replSetInitiate', cfg)
        except OperationFailure as exc:
            if exc.code != 23:
                raise
        wait_for(lambda: c.admin.command('hello').get('isWritablePrimary'))
        print('Replica set ready:', name, host)

if __name__ == '__main__':
    init('config:27017', 'cfg', True)
    init('shard-a:27017', 'shardA')
    init('shard-b:27017', 'shardB')
