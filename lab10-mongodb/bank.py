from uuid import uuid4
from common import DB
from transactions import transact, InsufficientFunds, InjectedFailure
from pymongo.write_concern import WriteConcern


def seed(client, run):
    db = client[DB].with_options(write_concern=WriteConcern(w='majority', j=True))
    db.accounts.create_index([('run',1),('account_id',1)], unique=True)
    db.transfer_history.create_index('run')
    db.accounts.insert_many([{'run':run,'account_id':a,'balance':b,'version':0} for a,b in [('A',1000),('B',500)]])


def snapshot(client, run):
    return {d['account_id']:{'balance':d['balance'],'version':d['version']} for d in client[DB].accounts.find({'run':run})}


def transfer(client, run, source, target, amount, retries=5, events=None, hook=None, inject_failure=False):
    if amount <= 0 or source == target: raise ValueError('Invalid transfer')
    db=client[DB]; operation=uuid4().hex
    def body(session, attempt):
        src={'run':run,'account_id':source}; dst={'run':run,'account_id':target}
        account=db.accounts.find_one(src,session=session)
        if not account or account['balance']<amount: raise InsufficientFunds('Insufficient funds')
        if hook: hook(attempt)
        changed=db.accounts.update_one({**src,'balance':{'$gte':amount},'version':account['version']}, {'$inc':{'balance':-amount,'version':1}},session=session)
        if changed.matched_count!=1: raise InsufficientFunds('Debit rejected')
        if inject_failure: raise InjectedFailure('Deliberate failure after debit')
        changed=db.accounts.update_one(dst,{'$inc':{'balance':amount,'version':1}},session=session)
        if changed.matched_count!=1: raise ValueError('Destination missing')
        db.transfer_history.insert_one({'_id':operation,'run':run,'source':source,'target':target,'amount':amount},session=session)
        return operation
    return transact(client,body,retries=retries,events=events)
