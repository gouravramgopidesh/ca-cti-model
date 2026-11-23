"""Lab 5.1: Monthly revenue, top customers, average value by status."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from lab5_common import connection,data,seed,dates_pipeline

FILE=Path(__file__).with_name('orders.json')

def main():
    client,db=connection()
    try:
        col=db['orders_51']
        inserted=seed(col,data(FILE),'order_id')
        print(f'Seeded/upserted orders; new={inserted}, sample documents={col.count_documents({})}')
        assert col.count_documents({})>=20,'Need at least 20 orders'
        total={'$multiply':['$quantity','$unit_price']}

        monthly=list(col.aggregate([
          dates_pipeline(),
          {'$group':{'_id':{'$dateToString':{'format':'%Y-%m','date':'$parsed_order_date'}},
                     'revenue':{'$sum':total},'orders':{'$sum':1}}},
          {'$sort':{'_id':1}}
        ]))
        print('\nMONTHLY REVENUE (all statuses, as specified):')
        for row in monthly: print(f"  {row['_id']}: revenue={row['revenue']} | orders={row['orders']}")
        assert len(monthly)>=3
        assert monthly==sorted(monthly,key=lambda x:x['_id'])

        top=list(col.aggregate([
          {'$group':{'_id':'$customer','spending':{'$sum':total},
                     'products':{'$addToSet':'$product'}}},
          {'$sort':{'spending':-1,'_id':1}},
          {'$limit':3}
        ]))
        print('\nTOP 3 CUSTOMERS:')
        for row in top: print(f"  {row['_id']}: spent={row['spending']}, products={sorted(row['products'])}")
        assert len(top)==3
        assert all(top[i]['spending']>=top[i+1]['spending'] for i in range(2))

        avg=list(col.aggregate([
          {'$group':{'_id':'$status','average_order_value':{'$avg':total},'count':{'$sum':1}}},
          {'$sort':{'_id':1}}
        ]))
        print('\nAVERAGE ORDER VALUE PER STATUS:')
        for row in avg: print(f"  {row['_id']}: avg={row['average_order_value']:.2f}, orders={row['count']}")
        assert {x['_id'] for x in avg}=={'completed','pending','cancelled'}
        print('\nACTIVITY 5.1: PASS')
    finally:client.close()

if __name__=='__main__':main()
