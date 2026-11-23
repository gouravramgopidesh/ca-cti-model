import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import local, DB, save
from books import seed
import math

def main():
    with local() as c:
        col = c[DB].books
        seed(col)
        print('CREATE: 5 books inserted')
        for label, query, expected in [
            ('After 2020', {'year':{'$gt':2020}},1),
            ('Machine Learning', {'genre':'Machine Learning'},2),
            ('$40-$60', {'price':{'$gte':40,'$lte':60}},3),
            ('AI tag', {'tags':'AI'},2)]:
            rows = list(col.find(query, {'_id':0,'title':1,'price':1}))
            assert len(rows) == expected
            print('READ:', label, rows)
        before = {b['title']:b['price'] for b in col.find()}
        assert col.update_many({}, {'$mul':{'price':1.10}}).modified_count == 5
        for b in col.find():
            old = before[b['title']]
            assert math.isclose(b['price'], old*1.10)
            print('UPDATE:', b['title'], f'{old:.2f} -> {b["price"]:.2f}')
        assert col.delete_one({'title':'Clean Code'}).deleted_count == 1
        assert col.count_documents({}) == 4
        assert not col.find_one({'title':'Clean Code'})
        print('DELETE: Clean Code; remaining: 4')
        save(col, 'activity-2.2')
    print('LAB 2.2 PASSED')

if __name__ == '__main__': main()
