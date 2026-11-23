import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import local, DB, save
from books import seed
import math

def main():
    with local() as c:
        col = c[DB].books_updated
        seed(col) # independent baseline; safe to rerun
        before = {b['_id']:b['price'] for b in col.find()}
        result = col.update_many({'year':{'$lt':2010}}, {'$mul':{'price':1.10}})
        assert result.matched_count == result.modified_count == 1
        for b in col.find():
            old = before[b['_id']]
            expected = old*1.10 if b['year'] < 2010 else old
            assert math.isclose(b['price'], expected)
            print(b['title'], b['year'], f'{old:.2f} -> {b["price"]:.2f}')
        print('Matched:', result.matched_count, 'Modified:', result.modified_count)
        save(col, 'activity-2.2-try')
    print('LAB 2.2 TRY PASSED: pre-2010 prices increased only')

if __name__ == '__main__': main()
