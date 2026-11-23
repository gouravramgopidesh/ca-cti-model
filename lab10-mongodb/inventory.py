import time
from uuid import uuid4
from common import DB
from transactions import transact, OutOfStock, InjectedFailure
from pymongo import ReturnDocument
from pymongo.write_concern import WriteConcern


def seed_inventory(client,stock):
    run=uuid4().hex; db=client[DB].with_options(write_concern=WriteConcern(w='majority',j=True))
    db.inventory.create_index([('run',1),('product_id',1)],unique=True)
    db.orders.create_index([('run',1),('order_id',1)],unique=True)
    db.inventory.insert_one({'run':run,'product_id':'P1','name':'Security sensor','stock':stock,'version':0,'price':25})
    return run


def reserve(client,run,customer,qty=1,retries=5,events=None,barrier=None,transactional=True,inject_failure=False):
    if qty<1: raise ValueError('quantity must be positive')
    db=client[DB]; product={'run':run,'product_id':'P1'}; order_id=uuid4().hex
    def order(price): return {'run':run,'order_id':order_id,'customer_id':customer,'items':[{'product_id':'P1','qty':qty,'price':price}],'status':'pending','total':price*qty}
    def body(session,attempt):
        doc=db.inventory.find_one(product,session=session)
        if barrier is not None and attempt==0: barrier.wait(timeout=30)
        if doc['stock']<qty: raise OutOfStock('Insufficient stock')
        changed=db.inventory.update_one({**product,'stock':{'$gte':qty},'version':doc['version']},{'$inc':{'stock':-qty,'version':1}},session=session)
        if changed.matched_count!=1: raise OutOfStock('Reservation rejected')
        if inject_failure: raise InjectedFailure('Order creation deliberately failed')
        db.orders.insert_one(order(doc['price']),session=session)
        return order_id
    if transactional: return transact(client,body,retries=retries,events=events)
    # Use same majority+journal durability for fairer comparison, but no multi-document atomicity.
    inv=db.inventory.with_options(write_concern=WriteConcern(w='majority',j=True))
    orders=db.orders.with_options(write_concern=WriteConcern(w='majority',j=True))
    doc=inv.find_one_and_update({**product,'stock':{'$gte':qty}},{'$inc':{'stock':-qty,'version':1}},return_document=ReturnDocument.BEFORE)
    if not doc: raise OutOfStock('Insufficient stock')
    if inject_failure: raise InjectedFailure('Order creation deliberately failed')
    orders.insert_one(order(doc['price']))
    return order_id


def state(client,run,initial):
    db=client[DB]; stock=db.inventory.find_one({'run':run})['stock']; orders=list(db.orders.find({'run':run}))
    sold=sum(item['qty'] for order in orders for item in order['items'])
    return {'initial_stock':initial,'remaining_stock':stock,'orders':len(orders),'reserved_quantity':sold,'consistent':stock+sold==initial and stock>=0}
