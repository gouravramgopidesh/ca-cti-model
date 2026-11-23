from common import client, wait_for, save, DB
with client() as c:
    wait_for(lambda: c.admin.command('ping'))
    assert c.admin.command('hello').get('msg') == 'isdbgrid'
    existing = {s['_id'] for s in c.admin.command('listShards')['shards']}
    for name, host in [('shardA','shard-a:27017'), ('shardB','shard-b:27017')]:
        if name not in existing:
            c.admin.command('addShard', f'{name}/{host}', name=name)
    c.admin.command('enableSharding', DB)
    status = c.admin.command('listShards')
    assert {s['_id'] for s in status['shards']} == {'shardA','shardB'}
    save('cluster-status.json', status)
    print('Sharded cluster ready:', status['shards'])
