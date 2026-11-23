import os
from common import *

with admin() as a:
    db = a[DB]
    db.reports.replace_one({'_id': 'sample'}, {'_id': 'sample', 'title': 'Training threat report'}, upsert=True)
    db.private_notes.replace_one({'_id': 1}, {'_id': 1, 'note': 'Restricted training data'}, upsert=True)
    role(db, 'reportReader', 'reports', ['find'])
    role(db, 'reportWriter', 'reports', ['find', 'insert', 'update', 'remove'])
    user(db, 'app_user_read', os.environ['LAB12_READ_PASSWORD'], ['reportReader'])
    user(db, 'app_user_write', os.environ['LAB12_WRITE_PASSWORD'], ['reportWriter'])
    db.reports.delete_one({'_id': 'writer-test'})
    opts = a.admin.command('getCmdLineOpts')['parsed']
    assert opts['security']['authorization'] == 'enabled'
    results = [{'test': 'authorization enabled', 'passed': True}]
with connect() as anonymous:
    results.append(denied('anonymous report read', lambda: anonymous[DB].reports.find_one()))
with connect('app_user_read', 'invalid-password') as wrong:
    results.append(denied('incorrect password', lambda: wrong[DB].reports.find_one(), 18))
with app('app_user_read', 'READ') as r:
    d = r[DB]
    results += [allowed('reader find', lambda: d.reports.find_one()),
                allowed('reader aggregate', lambda: list(d.reports.aggregate([{'$match': {'_id': 'sample'}}]))),
                denied('reader insert', lambda: d.reports.insert_one({'_id': 'forbidden'})),
                denied('reader update', lambda: d.reports.update_one({'_id': 'sample'}, {'$set': {'bad': True}})),
                denied('reader delete', lambda: d.reports.delete_one({'_id': 'sample'})),
                denied('reader private collection', lambda: d.private_notes.find_one())]
with app('app_user_write', 'WRITE') as w:
    d = w[DB]
    results += [allowed('writer insert', lambda: d.reports.insert_one({'_id': 'writer-test', 'title': 'test'})),
                allowed('writer read', lambda: d.reports.find_one({'_id': 'writer-test'})),
                allowed('writer update', lambda: d.reports.update_one({'_id': 'writer-test'}, {'$set': {'title': 'updated'}})),
                allowed('writer delete', lambda: d.reports.delete_one({'_id': 'writer-test'})),
                denied('writer private read', lambda: d.private_notes.find_one()),
                denied('writer private insert', lambda: d.private_notes.insert_one({'_id': 2})),
                denied('writer admin command', lambda: w.admin.command('serverStatus'))]
save('12.1-rbac.json', {'passed': True, 'tests': results})
