"""Lab 5.2: Join referenced products and discover products never ordered."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from lab5_common import connection,data,seed
FILE=Path(__file__).with_name('data.json')

def main():
    client,db=connection()
    try:
        payload=data(FILE)
        prod=db['products_52'];orders=db['orders_52']
        seed(prod,payload['products'],'product_id')
        seed(orders,payload['orders'],'order_id')
        joined=list(orders.aggregate([
          {'$lookup':{'from':'products_52','localField':'product_id',
                      'foreignField':'product_id','as':'product_details'}},
          {'$unwind':'$product_details'},
          {'$project':{'_id':0,'order_id':1,'order_date':1,'product_name':'$product_details.name',
                       'quantity':1,'total':{'$multiply':['$quantity','$product_details.base_price']}}},
          {'$sort':{'order_id':1}}
        ]))
        print(f'JOINED ORDERS (count={len(joined)}):')
        for row in joined: print(f"  {row['order_id']} | {row['order_date']} | {row['product_name']} | qty={row['quantity']} | total={row['total']}")
        assert len(joined)==len(payload['orders'])

        never=list(prod.aggregate([
          {'$lookup':{'from':'orders_52','localField':'product_id',
                      'foreignField':'product_id','as':'linked_orders'}},
          {'$match':{'linked_orders':{'$size':0}}},
          {'$project':{'_id':0,'product_id':1,'name':1,'category':1}},
          {'$sort':{'product_id':1}}
        ]))
        print('\nPRODUCTS NEVER ORDERED:')
        for row in never:print(f"  {row['product_id']}: {row['name']} ({row['category']})")
        assert {x['product_id'] for x in never}=={'P009','P010'}
        print('ACTIVITY 5.2: PASS')
    finally:client.close()

if __name__=='__main__':main()
