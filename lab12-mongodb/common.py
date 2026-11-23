import json, os
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import OperationFailure
DB = 'lab12-mongodb'

def connect(user=None, password=None, host='mongo', **options):
    if user is not None:
        options.update(username=user, password=password, authSource='admin' if user == 'labadmin' else DB)
    return MongoClient(host, 27017, serverSelectionTimeoutMS=4000, **options)

def admin(host='mongo', **options):
    return connect('labadmin', os.environ['LAB12_ADMIN_PASSWORD'], host, **options)

def app(user, role):
    return connect(user, os.environ[f'LAB12_{role}_PASSWORD'])

def save(name, result):
    Path('evidence').mkdir(exist_ok=True)
    Path('evidence', name).write_text(json.dumps(result, indent=2, default=str), encoding='utf-8')
    print(json.dumps(result, indent=2, default=str))

def allowed(label, fn):
    fn()
    print('ALLOWED:', label)
    return {'test': label, 'allowed': True, 'passed': True}

def denied(label, fn, code=13):
    try:
        fn()
    except OperationFailure as exc:
        if exc.code != code:
            raise
        print('DENIED:', label, 'code', exc.code)
        return {'test': label, 'allowed': False, 'code': exc.code, 'passed': True}
    raise AssertionError('Unexpected access: ' + label)

def role(db, name, collection, actions):
    privileges = [{'resource': {'db': DB, 'collection': collection}, 'actions': actions}]
    cmd = 'updateRole' if db.command('rolesInfo', name)['roles'] else 'createRole'
    db.command(cmd, name, privileges=privileges, roles=[])

def user(db, name, password, roles):
    cmd = 'updateUser' if db.command('usersInfo', name)['users'] else 'createUser'
    db.command(cmd, name, pwd=password, roles=[{'role': r, 'db': DB} for r in roles])
