import csv, random
from datetime import datetime, timedelta, timezone
from collections import Counter
from common import client, DB, save, EVIDENCE

# Synthetic e-commerce workload: intentionally skewed customer demand.
rng = random.Random(11)
start = datetime(2025,1,1,tzinfo=timezone.utc)
orders = [{'_id': i, 'order_id': f'ORD-{i:05d}',
           'customer_id': 'C000' if i % 5 == 0 else f'C{rng.randrange(1,1000):03d}',
           'order_date': start + timedelta(seconds=i), 'total': rng.randrange(100,10000)}
          for i in range(10000)]
with client() as c:
    col = c[DB].orders
    col.drop()
    col.insert_many(orders)
    rows = []
    for field, strategy, distribution, targeting in [
        ('order_id','range','Sequential IDs can hotspot; random IDs distribute better','Order equality targeted; customer query broadcasts'),
        ('customer_id','range','Skew possible from frequent customers','Customer equality and ranges can target shards'),
        ('order_date','range','Monotonic writes concentrate in newest range','Date ranges can target overlapping shards'),
        ('customer_id','hashed','Distributes distinct customers; hot customer still stays together','Customer equality targets; ranges broadcast')]:
        frequencies = list(col.aggregate([{'$group': {'_id': '$'+field, 'n': {'$sum': 1}}}, {'$sort': {'n': -1}}]))
        rows.append(dict(key=field, strategy=strategy, cardinality=len(frequencies),
                         hottest_value_count=frequencies[0]['n'], distribution=distribution, targeting=targeting))
    save('11.1-decision-matrix.json', rows)
    with (EVIDENCE/'11.1-decision-matrix.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    for row in rows: print(row)
    print('Recommendation: hashed customer_id for equality-heavy customer workloads; large single-customer hotspots remain possible.')
    print('11.1 completed: actual cardinalities, qualitative routing/distribution assessment.')
