"""Lab 5.1 try it: $bucket based on quantity * unit_price."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from lab5_common import connection,data,seed

FILE=Path(__file__).with_name('orders.json')

def main():
    client,db=connection()
    try:
        col=db['orders_51_bucket']
        seed(col,data(FILE),'order_id')
        # Sample data uses integer prices, so total=200 is medium and >=201 is large.
        categories=list(col.aggregate([
          {'$addFields':{'order_total':{'$multiply':['$quantity','$unit_price']}}},
          {'$bucket':{
            'groupBy':'$order_total','boundaries':[0,50,201,100000000],
            'default':'other',
            'output':{'orders':{'$sum':1},'revenue':{'$sum':'$order_total'},
                      'order_ids':{'$push':'$order_id'}}}}
        ]))
        names={0:'Small (< $50)',50:'Medium ($50–$200)',201:'Large (> $200)','other':'Other'}
        print('ORDER SIZE BUCKETS:')
        for row in categories:
            print(f"  {names[row['_id']]}: count={row['orders']}, total={row['revenue']}, order_ids={sorted(row['order_ids'])}")
        assert sum(x['orders'] for x in categories)==col.count_documents({})
        assert {x['_id'] for x in categories if x['_id']!='other'}=={0,50,201}
        print('ACTIVITY 5.1 TRY IT YOURSELF: PASS')
    finally:client.close()

if __name__=='__main__':main()
