"""Lab 5.2 try it: $lookup with a pipeline and correlated $expr filter."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from lab5_common import connection,data,seed
FILE=Path(__file__).with_name('data.json')

def main():
    client,db=connection()
    try:
        payload=data(FILE)
        products=db['products_52_filtered'];orders=db['orders_52_filtered']
        seed(products,payload['products'],'product_id')
        seed(orders,payload['orders'],'order_id')
        # Foreign-side filter: only ELECTRONICS products costing at least $50.
        results=list(orders.aggregate([
          {'$lookup':{
            'from':'products_52_filtered',
            'let':{'ref_product_id':'$product_id'},
            'pipeline':[
              {'$match':{'$expr':{'$and':[
                {'$eq':['$product_id','$$ref_product_id']},
                {'$eq':['$category','Electronics']},
                {'$gte':['$base_price',50]}
              ]}}},
              {'$project':{'_id':0,'name':1,'category':1,'base_price':1,'product_id':1}}
            ],
            'as':'filtered_products'
          }},
          {'$match':{'filtered_products.0':{'$exists':True}}},
          {'$unwind':'$filtered_products'},
          {'$project':{'_id':0,'order_id':1,'product':'$filtered_products.name',
                       'quantity':1,'unit_price':'$filtered_products.base_price',
                       'total':{'$multiply':['$quantity','$filtered_products.base_price']}}},
          {'$sort':{'order_id':1}}
        ]))
        print('JOIN WITH FOREIGN-SIDE FILTER (Electronics, base_price >= $50):')
        for r in results: print(f"  {r['order_id']}: {r['product']} | qty={r['quantity']} | total={r['total']}")
        expected={'P002','P006','P008'}
        expected_count=sum(1 for r in payload['orders'] if r['product_id'] in expected)
        assert len(results)==expected_count
        assert all(x['unit_price']>=50 for x in results)
        print(f'Filtered join count={len(results)}; expected={expected_count}')
        print('ACTIVITY 5.2 TRY IT YOURSELF: PASS')
    finally:client.close()

if __name__=='__main__':main()
